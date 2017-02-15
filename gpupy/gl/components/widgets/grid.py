from gpupy.gl import * 
from OpenGL.GL import * 
from gpupy.gl.components.camera import Camera2D
from gpupy.gl.mesh import *
import numpy as np 
from gpupy.gl.buffer import create_vao_from_program_buffer_object
from gpupy.gl.mesh import mesh3d_rectangle, StridedVertexMesh
from gpupy.gl.vector import *

from gpupy.gl import *
from OpenGL.GL import *
import numpy as np 
from functools import partial 
from gpupy.gl.components.widgets import Widget
from gpupy.gl.common import attributes
import os 
class CartesianGrid(Widget):
    # widget configuration
    size                 = attributes.VectorAttribute(2)
    resolution           = attributes.VectorAttribute(2)
    position             = attributes.VectorAttribute(4)

    # grid configuration
    grid                = attributes.VectorAttribute(2, (.5, .5))
    grid_width          = attributes.VectorAttribute(2, (2, 2))
    configuration_space = attributes.VectorAttribute(4)

    # style
    background_color  = attributes.VectorAttribute(4, (1, 1, 1, 1))
    line_color        = attributes.VectorAttribute(4, (0, 0, 0, 1))
    sub_line_color    = attributes.VectorAttribute(4, (0, 0, 0, 1))


    def __init__(self, size, 
                       position                 = (0, 0, 0, 1), 
                       configuration_space      = (0,0), 
                       grid                     = (1,1), 
                       background_color         = (1, 1, 1, 1), 
                       line_color               = (0, 0, 0, 1),
                       resolution               = None,
                       sub_line_color           = (0,0,0,1)):
        super().__init__()
        self.position = position
        self.size = size
        self.configuration_space = configuration_space
        self.grid = grid


        self.line_color = line_color 
        self.sub_line_color = sub_line_color 
        self.background_color = background_color
        self.resolution = resolution or self.size
        self._init_plane()

    @size.on_change
    @configuration_space.on_change
    @grid.on_change
    @grid_width.on_change
    @resolution.on_change
    @position.on_change
    def upload_uniforms(self, *e):
        self.program.uniform('mat_model', np.array([
            self.resolution.x, 0, 0, 0,
            0, self.resolution.y, 0, 0,
            0, 0, 1, 0, 
            0, 0, 0, 1           
        ], dtype=np.float32).T)

        # add this extra bit and assure that u_limits1 != u_limit2
      
      # polar
      #  self.program.uniform('u_limits1',[-5.1,+5.1,-5.1,+5.1])
      #  self.program.uniform('u_limits2',  [-5.0,+5.0, np.pi/6.0, 11.0*np.pi/6.0])
      #  self.program.uniform('u_major_grid_step', [1.00,np.pi/ 6.0])
      #  self.program.uniform('u_minor_grid_step', [0.25,np.pi/60.0])

      # cartesian
        self.program.uniform('u_limits1', [0, 1.0001, 0, 1.0001])
        self.program.uniform('u_limits2',  [0, 1, 0, 1])
        self.program.uniform('u_major_grid_step', [0.20,0.2])
        self.program.uniform('u_minor_grid_step', [0.1, 0.1])
        self.program.uniform('u_major_grid_width', 1.5)
        self.program.uniform('u_minor_grid_width', 1)
        self.program.uniform('u_major_grid_color', self.line_color)
        self.program.uniform('u_minor_grid_color', self.sub_line_color)
        self.program.uniform('iResolution', self.resolution)
        self.program.uniform('u_antialias', 1)
        self.program.uniform('c_bg', self.background_color)

    def _init_plane(self):
        self.program = GridProgram()

        self.program.uniform_block_binding('camera', GlConfig.STATE.RESERVED_BUFFER_BASE['gpupy.gl.camera'])
        self.upload_uniforms()

        self.mesh = StridedVertexMesh(mesh3d_rectangle(), 
                                      GL_TRIANGLES, 
                                      attribute_locations=self.program.attributes)

    def draw(self):
        glEnable(GL_BLEND);
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA);
        self.program.use()
        self.mesh.draw()
        self.program.unuse()

class GridProgram(Program):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.shaders.append(Shader(GL_VERTEX_SHADER, """
            {% version %}
            {% uniform_block camera %}
            in vec4 vertex;
            uniform mat4 mat_model;
            //uniforsm vec2 size;
            in vec2 tex;
            out vec2 v_texcoord;
            void main() {
                gl_Position = camera.mat_projection 
                            * camera.mat_view 
                            * mat_model 
                            * vec4(vertex.xyz, 1);
                v_texcoord = tex-vec2(0.5, 0.5);
            }
        """))

        self.shaders.append(Shader(GL_FRAGMENT_SHADER, open(os.path.dirname(__file__)+'/grid.frag.glsl').read()))

        self.declare_uniform('camera', Camera.DTYPE, variable='camera')
        self.link()

