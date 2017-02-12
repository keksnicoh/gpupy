#-*- coding: utf-8 -*-
"""
component  allows allows to render
scene into a framebuffer and renders a 
display plane.

:author: Nicolas 'keksnicoh' Heimann
"""
from gpupy.gl.buffer import create_vao_from_program_buffer_object
from gpupy.gl.mesh import mesh3d_rectangle, StridedVertexMesh
from gpupy.gl.vector import *
from gpupy.gl.common import attributes

from gpupy.gl import *
from OpenGL.GL import *
import numpy as np 
from functools import partial 

class FrameWidget():


    """
    Frame component uses framebuffer to render a scene on 
    a plane. 

    the state of a Frame is described by the following properties:

    Properties:

    - size: the size of the frame
    - capture_size: the size of the texture which captures the scene.
                    e.g. the capture size might be higher than the size
                         of the plane to enable anti aliasing like down
                         sampling.

    - viewport: gpupy.gl.ViewPort
                if not defined the viewport is set to 
                    ViewPort((0, 0), capture_size)
    - camera: camera which will be enabled when the Framebuffer 
              starts cawhichpturing
    - outer_camera: camera for rendering the screen


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
    capture_size = attributes.VectorAttribute(2)
    plane_size   = attributes.ComputedAttribute(size, descriptor=attributes.VectorAttribute(2))
    clear_color  = attributes.VectorAttribute(4)

    def __init__(self, size, capture_size=None, position=(0,0,0,1), multisampling=None, post_effects=None, blit=None, clear_color=(0, 0, 0, 1)):
        """
        creates a framebuffer of *size* and *capture_size* 
        at *position*.

        if *capture_size* is None, the capture_size is linked
        to *size*.
        """
        # XXX
        # - multisampling 
        # - post effects
        # - blit/record mode

        self.size         = size
        self.position     = position
        self.capture_size = capture_size if capture_size is not None else self.size
        self.viewport     = Viewport((0, 0), self.capture_size)
        self.texture      = None
        self.clear_color  = clear_color
        
        self._init_capturing()
        self._init_plane()

        self._require_resize = False 

    # -- initialization --

    def _init_capturing(self):
        self.texture = Texture2D.empty((*self.capture_size.xy, 4), np.float32)
        self.texture.interpolation_linear()
        self.framebuffer = Framebuffer()
        self.framebuffer.color_attachment(self.texture)

    @capture_size.on_change
    def capture_size_changed(self, value):
        print('NW', value)
        self._require_resize = True 

    def _init_plane(self):
        self.program = FrameProgram()
        self.texture.activate()

        self.program.uniform('frame_texture', self.texture)
        self.program.uniform_block_binding('outer_camera', GlConfig.STATE.RESERVED_BUFFER_BASE['gpupy.gl.camera'])

        self.program.uniform('size', self.plane_size.xy)
        self.program.uniform('mat_model', np.identity(4, dtype=np.float32))
        self.program.uniform('position', self.position.xyzw)
        self.mesh = StridedVertexMesh(mesh3d_rectangle(), 
                                      GL_TRIANGLES, 
                                      attribute_locations=self.program.attributes)

    @plane_size.transformation
    @capture_size.transformation
    def normalize(self, v):
        """ to avoid pixel rounding errors """
        # XXX 
        # - is this the best solution?
        v = np.ceil(v)
        return (max(1, v[0]), max(1, v[1]))

    @plane_size.on_change
    def _size_changed(self, size, *e):
        print('PLANE SIZE CHANGED', size)
        self.program.uniform('size', self.plane_size)

    @position.on_change
    def position_changed(self, position, *e):
        self.program.uniform('position', position.xyzw)

    def tick(self):
        if self._require_resize:
            self.texture.resize(self.capture_size) 
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
        self.viewport.use()
        glClearColor(*self.clear_color)
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

    def unuse(self): 
        self.viewport.unuse(restore=True)
        self.framebuffer.unuse()


class FrameProgram(Program):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.shaders.append(Shader(GL_VERTEX_SHADER, """
            {% version %}
            {% uniform_block outer_camera %}
            in vec4 vertex;
            uniform vec4 position;
            in vec2 tex;
            out vec4 frag_vertex;
            out vec2 frag_pos;
            uniform mat4 mat_model;
            uniform vec2 size;
            void main() {
                gl_Position = outer_camera.mat_projection 
                            * outer_camera.mat_view * mat_model 
                            * vec4(position.x + size.x*vertex.x, 
                                   position.y + size.y*vertex.y, 
                                   position.z + vertex.z, 
                                   vertex.w);
                frag_vertex = gl_Position;
                frag_pos = tex;
            }
        """))

        self.shaders.append(Shader(GL_FRAGMENT_SHADER, """
            {% version %}
            uniform sampler2D frame_texture;
            in vec2 frag_pos;
            in vec4 frag_vertex;
            out vec4 frag_color;
            uniform float vpw = 800; // Width, in pixels
uniform float vph = 800; // Height, in pixels

uniform vec2 offset = vec2(0, 0); // e.g. [-0.023500000000000434 0.9794000000000017], currently the same as the x/y offset in the mvMatrix
uniform vec2 pitch = vec2(100, 10);  // e.g. [50 50]

            uniform vec4 color = vec4(0.1, 0, 0, 1);
            void main() {
            if(texture(frame_texture, frag_pos).x == 1) {}
            if(frag_vertex.x == 1) {}
                frag_color = texture(frame_texture, frag_pos);
return;

                  vec2 coord = 50*frag_vertex.xz;
                  vec2 grid = abs(fract(coord - 0.5) - 0.5);
                  float line = min(grid.x, grid.y);
                  frag_color = vec4(vec3(1.0 - min(line, 1.0)), 1.0);

                  float lX = gl_FragCoord.x / vpw;
                  float lY = gl_FragCoord.y / vph;

                  float offX = gl_FragCoord.x;
                  float offY = (1.0 - gl_FragCoord.y);

                  if (int(mod(offX, pitch[0])) == 0 ||
                      int(mod(offY, pitch[1])) == 0) {
                    frag_color = vec4(0.0, 0.0, 0.0, 0.5);
                  } else {
                    frag_color = vec4(1.0, 1.0, 1.0, 1.0);
                  }
            }
        """))

        self.declare_uniform('outer_camera', Camera.DTYPE, variable='outer_camera')
        self.link()

"""
  // Pick a coordinate to visualize in a grid
  vec2 coord = 200*vertex.xz;

  // Compute anti-aliased world-space grid lines
  vec2 grid = abs(fract(coord - 0.5) - 0.5) / fwidth(coord);
  float line = min(grid.x, grid.y);

  // Just visualize the grid lines directly
  gl_FragColor = vec4(vec3(1.0 - min(line, 1.0)), 1.0);

"""
