#-*- coding: utf-8 -*-
"""
font rendering library.

XXX
- intelligent partioning of char buffers
- what if characters are unkown
- simple markup        <color=red>...</color>
- simple TeX parsing   $ ... $
   * fractionals
   * square roots
   * integrals
   * uppers
   * lowers
   * left and right () with correct size

@author Nicolas 'keksnicoh' Heimann <nicolas.heimann@gmail.com>
"""
from gpupy.gl import Gl
from gpupy.gl.shader import Shader, Program
from gpupy.gl.camera import Camera
from gpupy.common.helper import load_lib_file, resource_path
from gpupy.gl.texture import Texture2D
from gpupy.gl.buffer import BufferObject, create_vao_from_program_buffer_object
import os
import re

from OpenGL.GL import *
import numpy as np
from scipy.ndimage.io import imread

FONT_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'fonts')
import re

class FontException(Exception):
    pass

class FontRenderer():
    # definition of a character:
    #
    # a character has a glyph_id and properties like position.
    # this dtype is the dtype of the opengl buffer object of 
    # a list of character which should be rendered.
    CHAR_DTYPE = np.dtype([
        # a character has a certain position
        ('position', np.float32, (2,)),

        # a character has a color
        ('color',    np.float32, (4,)),

        # a character has a size
        ('size',     np.float32),

        # a character might be rotated
        ('rot',      np.float32),

        # font id of the glyph
        ('glyph_id',   np.int32),
    ])

    # definition of a glyph
    GLYPH_DTYPE = np.dtype([
        ('position',  np.float32, (4,)),
        ('size',      np.float32, (4,)),
        ('offset',    np.float32, (4,)),
        ('xadvance',  np.float32),
        ('page',      np.float32),
        ('chnl',      np.float32),
        ('buff',      np.float32),
    ])

    def __init__(self, font=None, camera=None, buffer_base=None):
        self.camera = camera
        if font is None:
            font = os.path.join(FONT_FOLDER, 'arial.fnt')
        self.font_path = font
        self.texts = []
        self._has_changes = True
        self._fnt = None
        self._buffer_base = buffer_base

    @property
    def font(self):
        return self._fnt

    def init(self):
        # load font file
        self._fnt = FNTFile.load_from_file(self.font_path)

        # prepare glyph atlas
        page_data         = [imread(img_path)[:,:,3] for img_path in self._fnt.page_paths]
        glypthatlas_width = page_data[0].shape[0]
        glyphatlas_height = page_data[0].shape[1]
        glyphatlas        = np.empty((len(page_data), glypthatlas_width, glyphatlas_height), dtype=np.float32)
        for i, glyphdata in enumerate(page_data):
            if glyphdata.shape[0:2] != (glypthatlas_width,glyphatlas_height):
                raise FontException((
                    'font "{}" corrupt: font page id={} file="{}" image size {}x{}'
                    + ' differs from the first page id=0 file="{}" {}x{}').format(
                        self.font, i, self._fnt.page_paths[i], glyphdata.shape[0],
                        glyphdata.shape[1], self._fnt.page_paths[0],
                        page_data[0].shape[0], page_data[0].shape[1]))

            glyphatlas[i] = glyphdata

        # texture glyph atlas
        self.texture = Texture2D(array=True)
        self.texture.load(glyphatlas)
        self.texture.interpolation_linear()

        # create shader
        self.shader_program = Program()
        self.shader_program.shaders.append(Shader(GL_VERTEX_SHADER, VERTEX_SHADER))
        self.shader_program.shaders.append(Shader(GL_GEOMETRY_SHADER, GEOMETRY_SHADER.replace('$n$', str(len(self._fnt.glyphs)))))
        self.shader_program.shaders.append(Shader(GL_FRAGMENT_SHADER, FRAGMENT_SHADER.replace('$n$', str(len(self._fnt.glyphs)))))
        self.shader_program.declare_uniform('camera', Camera.DTYPE if self.camera is None else self.camera)
        self.shader_program.link()

        # create vbo/vao
        self.buffer = BufferObject.empty(1, dtype=self.CHAR_DTYPE)
        self.vao = create_vao_from_program_buffer_object(self.shader_program, self.buffer)

        # upload glyph information
        glyphdata = np.empty(len(self._fnt.glyphs), dtype=self.GLYPH_DTYPE)
        glyphdata[:] = [c.dump() for c in self._fnt.glyphs]
        self.font_buffer = BufferObject.to_device(glyphdata, target=GL_UNIFORM_BUFFER)
        self.font_buffer.bind_buffer_base(self._buffer_base if self._buffer_base is not None else Gl.STATE.RESERVED_BUFFER_BASE['gpupy.gl.font'])
        self.shader_program.uniform_block_binding('ubo_font_objects', self.font_buffer)

        # shader configuration
        self.shader_program.uniform_block_binding('camera', Gl.STATE.RESERVED_BUFFER_BASE['gpupy.gl.camera'] if self.camera is None else self.camera)
        self.shader_program.uniform('tex_scale', (1.0/glypthatlas_width, 1.0/glyphatlas_height))
        self.shader_program.uniform('fontsize_real', 60)
        self.shader_program.uniform('tex', 1)

        # currently the default parameters for the model of width and edge
        # parameters of the distane field rendering. 
        self.set_render_parameters(width_max=.425, width_k=.0739, edge_slope=3.759, edge_trans=.045)

    def set_render_parameters(self, width_max, width_k, edge_slope ,edge_trans):
        """
        sets parameters for signed distance field parameter
        functions.
        """
        self.shader_program.uniform('width_max', width_max)
        self.shader_program.uniform('width_k', width_k)
        self.shader_program.uniform('edge_slope', edge_slope)
        self.shader_program.uniform('edge_trans', edge_trans)

    def create_text(self, text, size=10, position=(0,0), color=[0,0,0,1], rotation=0, **kwargs):
        """
        creates a text with certain size, position and rotation.
        :text: the text to be rendered
        :size: size of the text
        :position: position on xy plane
        :rotation: angle to rotate aroung (position.x, position.y)
           in mathematical way (anti clockwise).
           np.pi/2   = 90°
           np.pi     = 180°
           np.pi*3/2 = 270°
           2*pi      = 360°
        returns a TextObject instance.
        """
        textobj = TextObject(self, text, size, position, color=color, rotation=rotation, **kwargs)
        self.texts.append(textobj)
        self._has_changes = True
        return textobj

    def render(self):
        glClearColor(1,1,1,1)
        glActiveTexture(GL_TEXTURE1) # XXX disale texture later??

        with self.texture:
            glEnable (GL_BLEND)
            glBlendFunc (GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)

            # render
            for textobj in self.texts:
                shader = textobj.get_shader(self.shader_program)
                vao = textobj.get_vao(self.shader_program)

                shader.use()
                glBindVertexArray(vao)
                glDrawArrays(GL_POINTS, 0, len(textobj))
                glBindVertexArray(0)
                shader.unuse()


class TextObject(object):
    """
    basic text object.
    """
    _LATEX_CHARACTER_MAPPING = {
        'pi' : u'\u03C0', 'alpha': u'\u03b1', 'beta': u'\u03b2', 'gamma': u'\u03b3',
        'delta': u'\u03b4', 'epsilon': u'\u03b5', 'zeta': u'\u03b6', 'eta': u'\u03b7', 'Gamma': u'\u0393',
        'Delta': u'\u0394', 'Theta': u'\u0398', 'theta': u'\u03b8', 'vartheta': u'\u03d1', 'kappa': u'\u03ba',
        'lambda': u'\u03bb', 'mu': u'\u03bc', 'nu': u'\u03bd', 'xi': u'\u03be', 'Lambda': u'\u039b', 'Xi': u'\u039e', 
        'Pi': u'\u03a0', 'rho': u'\u03c1', 'varrho': u'\u03f1', 'sigma': u'\u03c3', 'varsigma': u'\u03c2', 
        'Sigma': u'\u03a3', 'Upsilon': u'\u03a5', 'Phi': u'\u03d5', 'tau': u'\u03c4', 'phi': u'\u03d5', 'varphi': u'\u03a6', 
        'chi': u'\u03a7', 'psi': u'\u03c8', 'omega': u'\u03c9', 'Psi': u'\u03a8', 'Omega': u'\u03a9', 'Int': u'\u222B' 
        }

    def __init__(self, renderer, chars, size, position, color=[0,0,0,1], rotation=0):
        self._chars = chars
        self.renderer = renderer
        self._rotation = rotation
        self._color = color
        self._size = size
        self._position = position

        self._boxsize = None

        self._char_data = None
        self._vao = None
        self._buffer_object = None

        self._has_changes = True

    def __len__(self):
        return len(self._chars)

    def _prepare(self, update_buffer_object=True):
        if not self._has_changes:
            pass

        font = self.renderer.font
        index = 0
        position = self.position

        colors = []
        if type(self._color[0]) in [list, tuple]:
            for charcol in self._color:
                colors.append(charcol)
            for i in range(len(colors), len(self.chars)):
                colors.append(charcol)
        else:
            colors = [self._color for i in range(len(self.chars))]

        try:
            chars = self.chars.decode('utf-8')
        except:
            chars = self.chars

        def _map_latex_placeholder(match):
            if match.group(1) not in self._LATEX_CHARACTER_MAPPING:
                return match.group(0)

            return self._LATEX_CHARACTER_MAPPING[match.group(1)]
            
        chars = re.sub(r'\$([a-zA-Z0-9]+)\$', _map_latex_placeholder, chars)
        chardata = np.empty(len(chars), dtype=FontRenderer.CHAR_DTYPE)

        char_list = []
        position = [self.position[0], self.position[1]]

        for char in chars:
            if not char in font.char_glyph:
                # XXX
                # - define me
                print('WARNING UNKOWN CHAR renderer.py')
                continue
            glyph_id = font.glyphs[font.char_glyph[char]]

            chardata[index] = ((position[0], position[1]), colors[index], self.size, self.rotation, font.char_glyph[char])
            sizefactor = float(self.size)/60
            position = (position[0]+sizefactor*float(glyph_id.xadvance-16), position[1])
            index += 1

        coords = chardata['position'] - self.position
        transformation = np.array([
            (np.cos(self.rotation), np.sin(self.rotation)),
            (-np.sin(self.rotation), np.cos(self.rotation))
        ], dtype=np.float32)
        chardata['position'] = [transformation.dot(a) for a in coords]
        chardata['position'] += self.position

        positions = chardata['position']
        self._char_data = chardata
        self._boxsize = (
            chardata['position'][-1][0]-chardata['position'][0][0]+self._size,
            chardata['position'][0][1]-chardata['position'][-1][1]+self._size)
        self._has_changes = False

        if update_buffer_object and self._buffer_object is not None:
            self._buffer_object.set(self._char_data)

    def get_data(self):
        self._prepare()
        return self._char_data
    
    def get_shader(self, default_shader):
        return default_shader

    def get_vao(self, default_shader):
        if self._buffer_object is None:
            self._buffer_object = BufferObject.to_device(self.get_data())

        elif self._has_changes:
            self._buffer_object.set(self.get_data(update_buffer_object=False))

        if self._vao is None:
            self._vao = create_vao_from_program_buffer_object(self.get_shader(default_shader), self._buffer_object)

        return self._vao

    @property
    def rotation(self):
        return self._rotation

    @rotation.setter
    def rotation(self, value):
        self._rotation = rotation
        self._has_changes = True

    @property
    def chars(self):
        return self._chars

    @chars.setter
    def chars(self, chars):
        self._chars = chars
        self._has_changes = True

    @property
    def size(self):
        return self._size

    @size.setter
    def size(self, size):
        self._size = size
        self.renderer._has_changes = True
        self._has_changes = True

    @property
    def position(self):
        return self._position

    @position.setter
    def position(self, position):
        self._position = position
        self._has_changes = True

    @property
    def color(self):
        return self._color

    @color.setter
    def color(self, color):
        self._color = color
        self.renderer._has_changes = True
        self._has_changes = True

    def __len__(self):
        try:
            return len(self._chars.decode('utf-8'))
        except:
            return len(self._chars)



class FNTFile():
    """
    *.fnt representation.
    todo: persist
    """

    class FNTGlyph():
        """
        representation of glyph
        """
        def __init__(self, *args):
            self.cid, self.x, self.y, self.width, self.height, \
            self.xoffset, self.yoffset, self.xadvance, \
            self.page, self.chnl = [int(a) for a in args]

        def dump(self):
            return ((self.x, self.y,0,0), (self.width,self.height,0,0),(self.xoffset,self.yoffset,0,0),self.page,self.xadvance,self.chnl,0)


    def __init__(self):
        self.page_paths = []
        self.glyphs = []
        self.char_glyph = {}

    @classmethod
    def load_from_file(cls, file_path):
        prog = re.compile(u'^char\s+id=(\d+)\s+x=(\d+)\s+y=(\d+)\s+width=(\d+)'
                        + u'\s+height=(\d+)\s+xoffset=(-?\d+)\s+yoffset=(-?\d+)'
                        + u'\s+xadvance=(\d+)\s+page=(\d+)\s+chnl=(\d+)')

        fnt = cls()
        page_prog = re.compile(u'^page id=(\d+)\s+file="?(.*\.png)"?')
        page_files = []
        with open(file_path) as f:
            expected_chars = None
            index = 0;
            for line in f:
                match = page_prog.match(line)
                if match is not None:
                    pid, pfile = match.groups()
                    page_path = os.path.join(os.path.dirname(file_path), pfile)
                    fnt.page_paths.append(page_path)
                    continue

                if expected_chars is None:
                    if line[0:11] == 'chars count':
                        expected_chars = int(line.split('=')[1])
                else:
                    match = prog.match(line)
                    if match is not None:
                        if len(fnt.glyphs) > expected_chars:
                            raise Exception('more characters than declared in "chars count" found in file ""'.format(file_path))

                        fntchar = FNTFile.FNTGlyph(*match.groups())
                        fnt.glyphs.append(fntchar)
                        try:
                            fnt.char_glyph[unichr(fntchar.cid)] = index
                        except:
                            fnt.char_glyph[chr(fntchar.cid)] = index
                        index += 1

            if expected_chars is None:
                raise Exception('"chars count" missing in file "{}"'.format(file_path))

            if expected_chars != len(fnt.glyphs):
                raise Exception(
                    ('did not find all characters: expected {}'
                    +' characterd to be defined but found {} in file "{}"').format(
                    expected_chars, len(fnt.glyphs), file_path))

            return fnt


VERTEX_SHADER = """
#version /*{$VERSION$}*/

{% uniform_block camera %}

in float rot;
out float geom_glyph_rot;

in vec4 color;
out vec4 geom_glyph_color;

in float size;
out float geom_glyph_size;

in int glyph_id;
out int geom_glyph_id;

in vec2 position;

void main()
{
    geom_glyph_size = size;
    geom_glyph_id = glyph_id;
    geom_glyph_rot = rot;
    geom_glyph_color = color;
    gl_Position = vec4(position, 0, 1);
}
"""

GEOMETRY_SHADER = """
#version /*{$VERSION$}*/

struct glyph {
  vec4 pos;
  vec4 size;
  vec4 offset;
  float page;
  float xadvance;

  float c;
};
uniform ubo_font_objects
{
    glyph glyphs[$n$];
};

layout (points)           in;
layout (triangle_strip)   out;
layout (max_vertices = 4) out;

in       float geom_glyph_size[1];
in       int   geom_glyph_id[1];
in       float geom_glyph_rot[1];
in       vec4  geom_glyph_color[1];

out       float frag_glyph_size;
out       vec2  tex_coord;
out       vec4  color;
flat      out   float page_id;

uniform float  fontsize_real;
{% uniform_block camera %}
uniform vec2   tex_scale;

float xwidth;
float ywidth;
float yfactor;
vec4  pos;
float sizefactor;
mat4  glyph_rotation;

float xo, yo;

glyph current;

void main(void)
{
    glyph_rotation[0] = vec4(cos(geom_glyph_rot[0]),-sin(geom_glyph_rot[0]),0,0);
    glyph_rotation[1] = vec4(sin(geom_glyph_rot[0]),cos(geom_glyph_rot[0]),0,0);
    glyph_rotation[2] = vec4(0,0,1,0);
    glyph_rotation[3] = vec4(0,0,0,1);

    current = glyphs[geom_glyph_id[0]];
    sizefactor = geom_glyph_size[0]/fontsize_real;

    xo = sizefactor*current.offset.x;
    yo = sizefactor*current.offset.y;
    xwidth = sizefactor*current.size.x;
    ywidth = sizefactor*current.size.y;

    // lower left - to upper left
    gl_Position = camera.mat_projection*camera.mat_view*(gl_in[0].gl_Position + glyph_rotation*vec4(xo, ywidth+yo,0,0));
    tex_coord = vec2(tex_scale.x*current.pos.x,tex_scale.x*(current.pos.y+current.size.y));
    color=geom_glyph_color[0];
    page_id=current.page;
    frag_glyph_size=geom_glyph_size[0];
    EmitVertex();

    // upper left - to upper right
    gl_Position = camera.mat_projection*camera.mat_view*(gl_in[0].gl_Position + glyph_rotation*vec4(xwidth+xo, ywidth+yo,0,0));
    tex_coord = vec2(tex_scale.x*(current.pos.x+current.size.x),tex_scale.x*(current.pos.y+current.size.y));
    color=geom_glyph_color[0];
    page_id=current.page;
    frag_glyph_size=geom_glyph_size[0];
    EmitVertex();

    // upper right - to lower left
    gl_Position = camera.mat_projection*camera.mat_view*(gl_in[0].gl_Position + glyph_rotation*vec4(xo, yo, 0,0));
    tex_coord = vec2(tex_scale.x*current.pos.x, tex_scale.x*current.pos.y);
    color=geom_glyph_color[0];
    page_id=current.page;
    frag_glyph_size=geom_glyph_size[0];

    EmitVertex();

    // lower left - to lower right
    gl_Position = camera.mat_projection*camera.mat_view*(gl_in[0].gl_Position + glyph_rotation*vec4(xwidth+xo, yo, 0,0));
    tex_coord = vec2(tex_scale.x*(current.pos.x+current.size.x), tex_scale.x*current.pos.y);
    color=geom_glyph_color[0];
    page_id=current.page;
    frag_glyph_size=geom_glyph_size[0];

    EmitVertex();

    EndPrimitive();
}
"""

FRAGMENT_SHADER = """
#version /*{$VERSION$}*/

in      vec2 tex_coord;
flat in float page_id;
in      vec4 color;
out     vec4 out_color;

uniform sampler2DArray tex;
uniform float width_max;
uniform float width_k;
uniform float edge_slope;
uniform float edge_trans;

in float frag_glyph_size;
float distance;
float alpha;
float _w;
float _e;

void main()
{
    // logistic function
    _w = width_max / (1 + exp(-width_k*frag_glyph_size));
    // 1/x + b function
    _e = edge_slope / frag_glyph_size + edge_trans;

    // signed distance field
    distance = 1.0-texture(tex, vec3(tex_coord, page_id)).r/255;
    alpha = 1.0-smoothstep(_w, _w+_e, distance);

    // colorize
    out_color = vec4(color.x,color.y,color.z,color.a*alpha);

}

"""
