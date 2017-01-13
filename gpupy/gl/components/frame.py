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

from gpupy.gl import *
from OpenGL.GL import *
import numpy as np 
from functools import partial 

class Frame():


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


    size         = Vec2Field()
    position     = Vec3Field()
    capture_size = Vec2Field()
    plane_size   = Vec2Field(listen_to=size)

    def __init__(self, size, capture_size=None, position=(0,0,0), multisampling=None, post_effects=None, blit=None):
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
        self.viewport     = ViewPort((0, 0), self.capture_size)
        self.texture      = None
        
        self._init_capturing()
        self._init_plane()

    # -- initialization --

    def _init_capturing(self):
        self.texture = Texture2D.empty((*self.capture_size.xy, 4), np.float32)
        self.texture.interpolation_linear()
        self.framebuffer = Framebuffer()
        self.framebuffer.color_attachment(self.texture)
        self.capture_size.on_change.append(partial(self.texture.resize))

    def _init_plane(self):
        self.program = FrameProgram()
        self.texture.activate()

        self.program.uniform('frame_texture', self.texture)
        self.program.uniform_block_binding('outer_camera', GlConfig.STATE.RESERVED_BUFFER_BASE['gpupy.gl.camera'])

        self.program.uniform('size', self.plane_size.xy)
        self.program.uniform('mat_model', np.identity(4, dtype=np.float32))
        self.program.uniform('position', self.position.xyz)
        self.mesh = StridedVertexMesh(mesh3d_rectangle(), 
                                      GL_TRIANGLES, 
                                      attribute_locations=self.program.attributes)

    @plane_size.transformation
    @capture_size.transformation
    def normalize(self, v):
        """ to avoid pixel errors """
        # XXX 
        # - is this the best solution?
        return np.ceil(v)

    @plane_size.on_change
    def _size_changed(self, size, *e):
        self.program.uniform('size', size)

    @position.on_change
    def position_changed(self, position, *e):
        self.program.uniform('position', position.xyz)

    def draw(self, shader=None):
        shader = shader or self.program

        self.texture.activate()
        shader.use()
        self.mesh.draw()
        shader.unuse()

        shader.use()
        if GlConfig.DEBUG:
            glPolygonMode(GL_FRONT_AND_BACK, GL_LINE);
            self.program.uniform('color', (0, 1, 0, 1))
            self.mesh.draw()
            self.program.uniform('color', (0, 0, 0, 0))
            glPolygonMode(GL_FRONT_AND_BACK, GL_FILL);
        shader.unuse()

    def use(self): 
        self.framebuffer.use()
        self.viewport.use()

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
            uniform vec3 position;
            in vec2 tex;
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
                frag_pos = tex;
            }
        """))

        self.shaders.append(Shader(GL_FRAGMENT_SHADER, """
            {% version %}
            uniform sampler2D frame_texture;
            in vec2 frag_pos;
            out vec4 frag_color;
            uniform vec4 color = vec4(0.1, 0, 0, 1);
            void main() {
            if(texture(frame_texture, frag_pos).x == 1) {}
                frag_color = texture(frame_texture, frag_pos);
                //;
            }
        """))

        self.declare_uniform('outer_camera', Camera.DTYPE, variable='outer_camera')
        self.link()


