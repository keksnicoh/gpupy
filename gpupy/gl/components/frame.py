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
    def __init__(self, size, capture_size=None, position=(0,0,0), outer_camera=None, camera=None):
        self._size = vec2(size)
        self._size.on_change.append(self._size_changed)
        self._position = vec3(position)
        self._capture_size = vec2(capture_size) if capture_size is not None else self._size
        self._capture_size.on_change.append(self._capture_size_changed)
        self._position.on_change.append(self._position_changed)

        self.viewport = ViewPort((0, 0), self.capture_size)
        self.texture = None
        self.camera = camera
        self.outer_camera = outer_camera
        
        self._init_capturing()
        self._init_plane()
        pass

    # -- controlled properties --

    @property
    def size(self):
        return self._size 

    @size.setter
    def size(self, value):
        self.size.xy = value

    @property
    def position(self):
        return self._position 

    @position.setter
    def position(self, value):
        self.position.xyz = value

    @property
    def capture_size(self):
        return self._capture_size 

    @capture_size.setter
    def capture_size(self, value):
        self.capture_size.xy = value

    ## -- event handlers --

    def _size_changed(self, size, old_size):
        self.program.uniform('size', size)

    def _capture_size_changed(self, size, old_size):
        self.texture.resize(size)

    def _position_changed(self, position, old_position):
        self.program.uniform('position', position.xyz)
 
    # -- initialization --

    def _init_capturing(self):
        self.texture = Texture2D.empty((*self.capture_size.xy, 4), np.float32)
        self.texture.interpolation_linear()

        self.framebuffer = Framebuffer()
        self.framebuffer.color_attachment(self.texture)

    def _init_plane(self):

        self.program = FrameProgram()
        self.texture.activate()

        self.program.uniform('frame_texture', self.texture)
        if self.outer_camera is not None:
            self.program.uniform_block_binding('outer_camera', outer_camera)
        else:
            self.program.uniform_block_binding('outer_camera', GlConfig.STATE.RESERVED_BUFFER_BASE['gpupy.gl.camera'])

        self.program.uniform('size', self.size.xy)
        self.program.uniform('mat_model', np.identity(4, dtype=np.float32))
        self.program.uniform('position', self._position.xyz)
        self.mesh = StridedVertexMesh(mesh3d_rectangle(), 
                                      GL_TRIANGLES, 
                                      attribute_locations=self.program.attributes)

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
        self.camera.enable()

    def unuse(self): 
        self.camera.disable()
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


