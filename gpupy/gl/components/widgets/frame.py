#-*- coding: utf-8 -*-
"""
component  allows allows to render
scene into a framebuffer and renders a 
display plane.

:author: Nicolas 'keksnicoh' Heimann
"""
from gpupy.gl.buffer import create_vao_from_program_buffer_object
from gpupy.gl.mesh import mesh3d_rectangle, StridedVertexMesh
from gpupy.gl.common.vector import *
from gpupy.gl.common import attributes
from gpupy.gl.components.widgets import Widget
from gpupy.gl import *
from gpupy.gl import GPUPY_GL as _G

from OpenGL.GL import *
import numpy as np 
from functools import partial 

def idf2(obj):
    oidb = np.int64(id(self)).tobytes()
    return np.array([np.frombuffer(oidb[0:4], dtype=np.float32), np.frombuffer(oidb[4:8], dtype=np.float32)], dtype=np.float32)
def f2id(vid):
    bf = vid[0].tobytes() + vid[1].tobytes()
    return int(np.frombuffer(bf, dtype=np.int64)[0])

_tidx = lambda idx: 3*idx
_tidxl = lambda idx: 3*idx+1
_tidxc = lambda idx: 3*idx+2
from copy import copy
class LayerWidget(Widget):
    _T_RENDER_LAYER = 1

    resolution = attributes.VectorAttribute(2)
    size = attributes.VectorAttribute(2)
    position = attributes.VectorAttribute(4)

    def __init__(self, position, size, resolution):
        super().__init__()
        self.resolution = resolution
        self.size = size
        self.position = position

        self._items = []
        self._default_configuration = {
            'color_channels': 4,
            'resolution': self.resolution,
            'type': 'static',
            'rendered': False,
        }
        self._layers = []
        self._tasks = [];

    def is_ready(self):
        pass 

    def forward(self):
        pass

    def render(self):
        pass

    def append(self, configuration):
        self._item.append(self._layer(configuration))
        self._task((self._T_RENDER_LAYER, len()))

    def insert(self, i, configuration):
        self._items.insert(i, self._layer(configuration))
        self._task((self._T_RENDER_LAYER, i))

    def _layer(self, configuration):
        config = copy(self._default_configuration)
        config.update(configuration)
        si = _LayerWidgetLayer(config)
        return si 

    def _task(self, task):
        if task in self._tasks:
            self._tasks.remove(task)
        self._tasks.append(task)

   # def __next__(self):
   #     for item in self._items:
   #         if not item.rendered
   #     return False

def _LayerWidgetLayer():
    def __init__(self, configuration):

        self._instance = configuration['instance']
        self._fbo = glGenFramebuffers(1)
        self._res = configuration['resolution']
        self._color_channels = configuration.get('color_channels', 4)

        # initialize main texture
        self._tex = Texture2D.empty((*self._res, self._color_channels), dtype=np.float32)
        _tex.activate()
        _tex.parameter(GL_TEXTURE_WRAP_S, GL_CLAMP_TO_EDGE)
        _tex.parameter(GL_TEXTURE_WRAP_T, GL_CLAMP_TO_EDGE)
        glBindFramebuffer(GL_DRAW_FRAMEBUFFER, self._fbo[0])
        glFramebufferTextureLayer(GL_FRAMEBUFFER, GL_COLOR_ATTACHMENT0, self._tex.gl_texture_id, 0, 0);
        glDrawBuffers([GL_COLOR_ATTACHMENT0])
        glBindFramebuffer(0)

class FramestackWidget(Widget):
    SUBJECT = 0
    IDX = 1
    RENDERER = 2
    CLICKMAP = 3

    M_TOP_LAYER = 1
    M_LAYERS = 0

    resolution = attributes.VectorAttribute(2)
    size = attributes.VectorAttribute(2)
    position = attributes.VectorAttribute(4)

    def __init__(self, position, size, resolution, pf=1):
        super().__init__()
        print(glGetIntegerv(GL_MAX_DRAW_BUFFERS))

        self._s = []
        self.resolution = resolution
        self.size = size
        self.position = position
        self._pf = pf
        self._rs = []
        self._hrl = 0

        self._init_textures()
        self._init_fb()
        self._init_program()
        self._init_mesh()

    def _init_textures(self):
        
        def _texture(txres):
            txt = Texture2D.empty((self._ln(), *txres, 4), dtype=np.float32, array=True)
            txt.activate()
            txt.parameter(GL_TEXTURE_WRAP_S, GL_CLAMP_TO_EDGE)
            txt.parameter(GL_TEXTURE_WRAP_T, GL_CLAMP_TO_EDGE)
            return txt

        # LOW TEXTURE
        txres = self.resolution.xy
        self._rs.append(txres)
        self.tarray_rl = _texture(txres) if self._pf != 1 else None

        # MAIN TEXTURE
        txres = self.resolution.xy * self._pf
        self._rs.append(txres)
        self.tarray = _texture(txres)

        # HIGH TEXTURE
        txres = self.resolution.xy * self._pf ** 2
        self._rs.append(txres)
        self.tarray_rh = _texture(txres) if self._pf != 1 else None

    def _init_fb(self):
        self._rb_fb = glGenFramebuffers(1)
        self._rb_fbs = glGenFramebuffers(100)

    def _init_program(self):

        self._rs_prg = _CameraProgram(_GLSL_VRT, _GLSL_STACK_FRG)
        
        self._rs_prg.uniform('mat_model', np.identity(4, dtype=np.float32))

        self._rs_prg_layer = Program()
        self._rs_prg_layer.shaders.append(Shader(GL_VERTEX_SHADER, _GLSL_STACK_VRT_LAYER))
        self._rs_prg_layer.shaders.append(Shader(GL_FRAGMENT_SHADER, _GLSL_STACK_FRG_LAYER))
        self._rs_prg_layer.link()
        self._rs_prg_layer.uniform('frame_texture', self.tarray)

        self.upload_uniforms()

    def _init_mesh(self):
        self._rs_mesh = StridedVertexMesh(mesh3d_rectangle(), 
                                          GL_TRIANGLES, 
                                          attribute_locations=self._rs_prg.attributes)
    def upload_uniforms(self):
        self._rs_prg.uniform('size',          self.size)
        self._rs_prg.uniform('position',      self.position)  
        self._rs_prg.uniform('frame_texture', self.tarray)

        self._rs_prg_layer.uniform('frame_texture', self.tarray)

    def _ln(self):
        return 35

    @resolution.on_change
    def _resolution_changed(self, *e):
        return
        if self._pf != 1:
            if self._rs[1][0] < self.resolution[0] \
            or self._rs[1][1] < self.resolution[1]:
                _G.debug('FramestackWidget swap textures HIGH')

                # swap textures
                old_tarray_rl = self.tarray_rl
                self.tarray_rl = self.tarray 
                self.tarray = self.tarray_rh
                self.tarray_rh = old_tarray_rl
                self.tarray.activate()
                self._rs[0] = self._rs[1]
                self._rs[1] = self._rs[2]
                self._rs[2] = self._rs[2] * self._pf
                # resize the new small texture
                self.tarray_rh.resize((self._ln(), *self._rs[2]))
                self._rebind_active_fbo()

            elif self.resolution[0]/self._rs[1][0] <= .25 \
            and self.resolution[1]/self._rs[1][1] <= .25:
                _G.debug('FramestackWidget swap textures LOW')

                # swap textures
                old_tarray_rh = self.tarray_rh
                self.tarray_rh = self.tarray
                self.tarray = self.tarray_rl
                self.tarray_rl = old_tarray_rh
                self.tarray.activate()
                self._rs[2] = self._rs[1] 
                self._rs[1] = self._rs[0]
                self._rs[0] = self._rs[0] / self._pf

                # resize the new large texture
                self.tarray_rl.resize((self._ln(), *self._rs[0]))
                self._rebind_active_fbo()

            rf = (self.resolution[0] / self._rs[1][0], 
                  self.resolution[1] / self._rs[1][1])
            self._rs_prg.uniform('rf', rf)
            self._rs_prg_layer.uniform('rf', rf)
        else:
            self.tarray.resize((self._ln(), *self.resolution.xy))
            self._rs[1] = self.resolution.xy
            self._rs_prg.uniform('rf', (1, 1))
            self._rs_prg_layer.uniform('rf',  (1, 1))
        self.upload_uniforms()
            
    @size.on_change
    @position.on_change
    def _attributes_changed(self, *e):
        self.upload_uniforms()

    def _rebind_active_fbo(self):
        tex = self.tarray.gl_texture_id
        for si in self._s:
            tidx = 2*si[FramestackWidget.IDX]
            fb = self._rb_fbs[tidx]
            glBindFramebuffer(GL_DRAW_FRAMEBUFFER, fb)
            glFramebufferTextureLayer(GL_FRAMEBUFFER, GL_COLOR_ATTACHMENT0, tex, 0, tidx);

            tidx = 2*si[FramestackWidget.IDX]+1
            fb = self._rb_fbs[tidx]
            glBindFramebuffer(GL_DRAW_FRAMEBUFFER, fb)
            glFramebufferTextureLayer(GL_FRAMEBUFFER, GL_COLOR_ATTACHMENT0, tex, 0, tidx);

    def render_stack(self, mode=0, layers=None):
        vp = glGetIntegerv(GL_VIEWPORT)
        glViewport(0, 0, *((self.resolution.xy).astype(np.int32)))
        glClearColor(0, 1, 0, 0)
        if layers is not None:
            layers = sorted(layers)

        print('REEE')
        if self._hrl < len(self._rs) -1:
            print('RENDER LEVEL', self._hrl)
            self._hrl += 1

        # render all layers
        # (slowest mode)
        if mode == self.M_LAYERS:
            glDisable(GL_BLEND)
            last_idx = None if layers is None or layers[0] == 0 else self._s[layers[0]-1][FramestackWidget.IDX]
            self._rs_prg_layer.uniform('idxl', -1)

            stack = self._s
            if layers is not None:
                stack = [(si, i in layers) for i, si in enumerate(self._s[layers[0]:], layers[0])]
            else:
                stack = [(si, True) for si in self._s]

            for si, rerender in stack:
                # render item
                if rerender:
                    glBindFramebuffer(GL_DRAW_FRAMEBUFFER, self._rb_fbs[_tidx(si[FramestackWidget.IDX])])
                    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
                    si[self.RENDERER]()

                # render layer
                glBindFramebuffer(GL_DRAW_FRAMEBUFFER, self._rb_fbs[_tidxl(si[FramestackWidget.IDX])])
                glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
                self._rs_prg_layer.use()
                self._rs_prg_layer.uniform('idx', _tidx(si[FramestackWidget.IDX]))
                self._rs_prg_layer.uniform('clickmap', si[FramestackWidget.CLICKMAP])
                if last_idx is not None:
                    self._rs_prg_layer.uniform('idxl', _tidxl(last_idx))
                    self._rs_prg_layer.uniform('idxc', _tidxc(last_idx))
                self._rs_mesh.draw()
                self._rs_prg_layer.unuse()
                last_idx = si[FramestackWidget.IDX]

            glBindFramebuffer(GL_DRAW_FRAMEBUFFER, 0)

        # render all items to the top layer directly
        # (this is the fastest rendering method)
        elif mode == self.M_TOP_LAYER:
            print('TOP')
            #glEnable(GL_BLEND)
            #glBlendFuncSeparate(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA, GL_ONE, GL_ONE_MINUS_SRC_ALPHA);
            fb = self._rb_fbs[_tidxl(self._s[len(self._s)-1][FramestackWidget.IDX])]
            glBindFramebuffer(GL_DRAW_FRAMEBUFFER, fb)
            glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

            stack = (self._s[i] for i in layers) if layers is not None else self._s
            for si in stack:
                si[self.RENDERER]()
            glBindFramebuffer(GL_DRAW_FRAMEBUFFER, 0)
            self._hrl = 0

        glViewport(*vp)

    def render(self):
        self.tarray.activate()
        self._rs_prg.use()
        self._rs_prg.uniform('idx', _tidxl(self._s[len(self._s)-1][FramestackWidget.IDX]))
        self._rs_mesh.draw()
        self._rs_prg.unuse()

    def _free_idx(self):
        sidx = sorted(self._s, key=lambda rsi: rsi[FramestackWidget.IDX])
        for idx, rsi in enumerate(sidx):
            if rsi[FramestackWidget.IDX] != idx:
                return idx
        return len(sidx) 

    def _caller(self, renderer):
        if hasattr(renderer, '__call__'):
            return renderer
        if hasattr(renderer, 'render'):
            return renderer.render 
        raise ValueError()

    def get_layer(self, renderer):
        for i, si in enumerate(self._s):
            if si[0] is renderer:
                return i

    def append(self, subject, clickmap=(0,0,0,0)):
        idx = self._free_idx()
        self._init_layer(idx)

        si = _StackItem()
        si.subject = subject
        si.idx = idx 
        si.clickmap = clickmap 
        si.renderer = self._caller(subject)
        si.init_gl(self.resolution.xy)

        self._s.append((subject, idx, self._caller(subject), clickmap))
        glBindFramebuffer(GL_DRAW_FRAMEBUFFER, 0)

    def insert(self, i, renderer, clickmap=(0,0,0,0)):
        idx = self._free_idx()
        self._init_layer(idx)
        self._s.insert(i, (renderer, idx, self._caller(renderer), clickmap))
        glBindFramebuffer(GL_DRAW_FRAMEBUFFER, 0)

    def _init_layer(self, idx):
        # we perform at least one clear operation on each texture on init.
        # otherwise OpenGL will lag when switching to another texture for the first
        # time.

        if self._pf != 1:
            glBindFramebuffer(GL_DRAW_FRAMEBUFFER, self._rb_fbs[_tidx(idx)])
            glFramebufferTextureLayer(GL_FRAMEBUFFER, GL_COLOR_ATTACHMENT0, self.tarray_rh.gl_texture_id, 0, _tidx(idx));
            glClear(GL_COLOR_BUFFER_BIT)
            glFramebufferTextureLayer(GL_FRAMEBUFFER, GL_COLOR_ATTACHMENT0, self.tarray_rl.gl_texture_id, 0, _tidx(idx));
            glClear(GL_COLOR_BUFFER_BIT)

            glBindFramebuffer(GL_DRAW_FRAMEBUFFER, self._rb_fbs[_tidxl(idx)])
            glFramebufferTextureLayer(GL_FRAMEBUFFER, GL_COLOR_ATTACHMENT0, self.tarray_rh.gl_texture_id, 0, _tidxl(idx));
            glFramebufferTextureLayer(GL_FRAMEBUFFER, GL_COLOR_ATTACHMENT1, self.tarray_rl.gl_texture_id, 0, _tidxc(idx));
            glClear(GL_COLOR_BUFFER_BIT)
            glFramebufferTextureLayer(GL_FRAMEBUFFER, GL_COLOR_ATTACHMENT0, self.tarray_rl.gl_texture_id, 0, _tidxl(idx));
            glFramebufferTextureLayer(GL_FRAMEBUFFER, GL_COLOR_ATTACHMENT1, self.tarray_rl.gl_texture_id, 0, _tidxc(idx));
            glClear(GL_COLOR_BUFFER_BIT)

        
        glBindFramebuffer(GL_DRAW_FRAMEBUFFER, self._rb_fbs[_tidx(idx)])
        glFramebufferTextureLayer(GL_FRAMEBUFFER, GL_COLOR_ATTACHMENT0, self.tarray.gl_texture_id, 0, _tidx(idx));
        glClear(GL_COLOR_BUFFER_BIT)

        glBindFramebuffer(GL_DRAW_FRAMEBUFFER, self._rb_fbs[_tidxl(idx)])
        glFramebufferTextureLayer(GL_FRAMEBUFFER, GL_COLOR_ATTACHMENT0, self.tarray.gl_texture_id, 0, _tidxl(idx));
        glFramebufferTextureLayer(GL_FRAMEBUFFER, GL_COLOR_ATTACHMENT1, self.tarray.gl_texture_id, 0, _tidxc(idx));
        glDrawBuffers([GL_COLOR_ATTACHMENT0, GL_COLOR_ATTACHMENT1])
        glClear(GL_COLOR_BUFFER_BIT)



        glBindFramebuffer(GL_FRAMEBUFFER, 0)

def _StackItem():
    R0 = 0x0001
    R1 = 0x0010
    def __init__(self):
        self.subject = None
        self.idx = None 
        self.render = None 
        self.clickmap = vec4(0,0,0,0)
        self.rendered = 0
        self.fbo = None 
        self.txt = None 

    def init_gl(self, txres):
        self.fbo = glGenFramebuffers(2)
       # self.txt = 
        txt = Texture2D.empty((2, *txres, 4), dtype=np.float32, array=True)
        txt.activate()
        txt.parameter(GL_TEXTURE_WRAP_S, GL_CLAMP_TO_EDGE)
        txt.parameter(GL_TEXTURE_WRAP_T, GL_CLAMP_TO_EDGE)



        def _texture(txres):

            return txt

        # LOW TEXTURE
        txres = self.resolution.xy
        self._rs.append(txres)
        self.tarray_rl = _texture(txres) if self._pf != 1 else None

class FrameWidget(Widget):
    """
    Frame component uses framebuffer to render a scene on 
    a plane. 

    the state of a Frame is described by the following properties:

    Properties:

    - size: the size of the frame
    - resulution: the size of the texture which captures the scene.
                    e.g. the capture size might be higher than the size
                         of the plane to enable anti aliasing like down
                         sampling.

    - viewport: gpupy.gl.ViewPort
                if not defined the viewport is set to 
                    ViewPort((0, 0), resulution)
    - camera: camera which will be enabled when the Framebuffer 
              starts cawhichpturing
    - camera: camera for rendering the screen


         +----------------------------------------+
         |
         |             capture.x 
         |  c #####################################
         |  a #
      s  |  p #         
      i  |  t #       vp.pos          vp.w
      z  |  u #            x ---------------------
      e  |  r #            |          
      .  |  e #       vp.h | 
      y  |  . #            + ---------------------
         |  y ####################################
         |
         +----------------------------------------+

    """


    size         = attributes.VectorAttribute(2)
    position     = attributes.VectorAttribute(4)
    resulution   = attributes.VectorAttribute(2)
    plane_size   = attributes.ComputedAttribute(size, descriptor=attributes.VectorAttribute(2))
    clear_color  = attributes.VectorAttribute(4)

    def __init__(self, 
                 size, 
                 resulution=None, 
                 position=(0,0,0,1), 
                 multisampling=None, 
                 post_effects=None, 
                 blit=None, 
                 clear_color=(0, 0, 0, 1), 
                 preload_factor=2):
        """
        creates a framebuffer of *size* and *resulution* 
        at *position*.

        if *resulution* is None, the resulution is linked
        to *size*.
        """
        # XXX
        # - multisampling 
        # - post effects
        # - blit/record mode

        super().__init__()
        self._res = None
        self.size         = size
        self.position     = position
        self.resulution = resulution if resulution is not None else self.size
        self.viewport     = Viewport((0, 0), self.resulution)
        self.texture      = None
        self.clear_color  = clear_color
        self.preload_factor = preload_factor
        self._init_capturing()
        self._init_plane()

        

        self._require_resize = False 

    # -- initialization --

    def _init_capturing(self):
        self._res = self.preload_factor*self.resulution.values
        self.texture = Texture2D.empty((*self._res, 4), np.float32)
        self.texture.interpolation_linear()
        self.framebuffer = Framebuffer()
        self.framebuffer.color_attachment(self.texture)
        self.texture.parameter(GL_TEXTURE_WRAP_S, GL_CLAMP_TO_EDGE)
        self.texture.parameter(GL_TEXTURE_WRAP_T, GL_CLAMP_TO_EDGE)

    @resulution.on_change
    def resulution_changed(self, value):
        print('WFWEFWEFFF§§33')
        self._require_resize = True 

    def _init_plane(self):
        self.program = _CameraProgram(_GLSL_VRT, _GLSL_FRG)
        self.texture.activate()

        self.program.uniform('frame_texture', self.texture)
        self.program.uniform_block_binding('camera', GPUPY_GL.CONTEXT.buffer_base('gpupy.gl.camera'))

        self.program.uniform('size', self.plane_size.xy)
        self.program.uniform('mat_model', np.identity(4, dtype=np.float32))
        self.program.uniform('position', self.position.xyzw)
        self.program.uniform('rf', (self.resulution[0]/self._res[0], self.resulution[1]/self._res[1]))
        self.position.on_change.append(partial(self.program.uniform, 'position'))
        self.size.on_change.append(partial(self.program.uniform, 'size'))

        self.mesh = StridedVertexMesh(mesh3d_rectangle(), 
                                      GL_TRIANGLES, 
                                      attribute_locations=self.program.attributes)

    @plane_size.transformation
    @resulution.transformation
    def normalize(self, v):
        """ to avoid pixel rounding errors """
        # XXX 
        # - is this the best solution?
        v = np.ceil(v)
        return (max(1, v[0]), max(1, v[1]))

    def tick(self):
        if self._require_resize:
            
            if self._res[0] < self.resulution[0] \
            or self._res[1] < self.resulution[1]:
                self._res = self.resulution.values * self.preload_factor
                self.texture.resize(self._res) 
            self.program.uniform('rf', (self.resulution[0]/self._res[0], self.resulution[1]/self._res[1]))
            self._require_resize = False

    def render(self):
        self.draw()

    def draw(self, shader=None):
        shader = shader or self.program
        self.texture.activate()
        shader.use()
        self.mesh.draw()
        shader.unuse()

    def use(self): 
        self.framebuffer.use()
        self.viewport.use((0, 0), np.array(self.resulution, dtype=np.int32))
        glClearColor(*self.clear_color)
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

    def unuse(self): 
        self.viewport.unuse(restore=True)
        self.framebuffer.unuse()

class _CameraProgram(Program):
    def __init__(self, vrt, frg, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.shaders.append(Shader(GL_VERTEX_SHADER, vrt))
        self.shaders.append(Shader(GL_FRAGMENT_SHADER, frg))
        self.declare_uniform('camera', Camera.DTYPE, variable='camera')
        self.link()
        self.uniform_block_binding('camera', _G.CONTEXT.buffer_base('gpupy.gl.camera'))

# ---- GLSL ---------------

_GLSL_STACK_VRT_LAYER = """
{% version %}
in vec4 vertex;
in vec2 tex;
out vec2 frag_pos;
uniform vec2 rf;
void main() {
    gl_Position = vec4(2*vertex.x-1, 0 + 1-2*vertex.y, 0, 1);
    frag_pos = tex*rf;
}
"""

_GLSL_STACK_FRG_LAYER = """
{% version %}
in vec2 frag_pos;
layout(location=0) out vec4 frag_color;
layout(location=1) out vec4 click_color;
uniform sampler2DArray frame_texture;
uniform int idx = 0;
uniform int idxl = 0;
uniform int idxc = 0;
uniform vec4 clickmap = vec4(0,0,0,0);
void main() {
    if (idxl > -1) { 
        vec4 c = texture(frame_texture, vec3(frag_pos, idx));
        vec4 c2 = texture(frame_texture, vec3(frag_pos, idxl));

        if (c.a < 0.001) {
            frag_color = c2;
        }
        else {
            frag_color = mix(c, c2, 1-c.a);
        }
        vec4 cc = texture(frame_texture, vec3(frag_pos, idxc));
        if (c.w == 0) {
            click_color = cc;
        }
        else if (c.w > 0.01) {
            click_color = clickmap;
        }
    }
    else {
        vec4 c = texture(frame_texture, vec3(frag_pos, idx));
        frag_color = c;

        if (c.w > 0.1) {
            click_color = clickmap;
        }
        else {
            click_color = vec4(0, 0, 0, 0);
        }
    }
}
"""

_GLSL_VRT = """
{% version %}
{% uniform_block camera %}
in vec4 vertex;
uniform vec4 position;
in vec2 tex;
out vec2 frag_pos;
uniform mat4 mat_model;
uniform vec2 rf;
uniform vec2 size;
void main() {
    gl_Position = camera.mat_projection 
                * camera.mat_view * mat_model 
                * vec4(position.x + size.x*vertex.x, 
                       position.y + size.y*vertex.y, 
                       position.z + vertex.z, 
                       vertex.w);
    frag_pos = tex*rf;
}
"""

_GLSL_STACK_FRG = """
{% version %}
uniform sampler2DArray frame_texture;
in vec2 frag_pos;
out vec4 frag_color;
uniform int idx = 0;
void main() {
    frag_color = texture(frame_texture, vec3(frag_pos, idx));
}
"""

_GLSL_FRG = """
{% version %}
uniform sampler2D frame_texture;
in vec2 frag_pos;
out vec4 frag_color;
void main() {
    frag_color = texture(frame_texture, frag_pos);
    //frag_color = vec4(0, frag_pos.y, 0, 1);
}
"""