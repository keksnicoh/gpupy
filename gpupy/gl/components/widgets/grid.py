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
class CartesianGrid(Widget):

    size = attributes.VectorAttribute(2)
    pixels = attributes.VectorAttribute(2)
    position = attributes.VectorAttribute(4)

    configuration_space = attributes.VectorAttribute(4)

    def __init__(self, size, position=(0, 0, 0, 1), configuration_space=(0,0)):
        super().__init__()
        self.position = position
        self.size = size
        self.configuration_space = configuration_space

        self._init_plane()

    @size.on_change
    def _size_changed(self, size, *e):
        self.program.uniform('size', size.values)

    @configuration_space.on_change
    def _size_changed(self, configuration_space, *e):
        self.program.uniform('origin', (configuration_space.x, configuration_space.z))


    @position.on_change
    def position_changed(self, position, *e):
        self.program.uniform('position', position.xyzw)

    def _init_plane(self):
        self.program = GridProgram()

        self.program.uniform_block_binding('camera', GlConfig.STATE.RESERVED_BUFFER_BASE['gpupy.gl.camera'])

        self.program.uniform('size', self.size.xy)
        self.program.uniform('mat_model', np.identity(4, dtype=np.float32))
        self.program.uniform('position', self.position.xyzw)
        self.mesh = StridedVertexMesh(mesh3d_rectangle(), 
                                      GL_TRIANGLES, 
                                      attribute_locations=self.program.attributes)
    def draw(self):
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
            uniform vec4 position;
            uniform mat4 mat_model;
            uniform vec2 size;
            in vec2 tex;
            out vec2 frg_tex;
            void main() {
                gl_Position = camera.mat_projection 
                            * camera.mat_view * mat_model 
                            * vec4(position.x + size.x*vertex.x, 
                                   position.y + size.y*vertex.y, 
                                   position.z + vertex.z, 
                                   vertex.w);
                frg_tex = tex;
            }
        """))

        self.shaders.append(Shader(GL_FRAGMENT_SHADER, """
            {% version %}
            out vec4 frag_color;
            in vec2 frg_tex;
            uniform vec2 size;
            uniform vec2 n_grid = vec2(15, 15);
            uniform vec2 w_grid = vec2(2, 2);
            uniform vec2 origin = vec2(0, 0);
            vec2 m;
            vec2 ts;
            float v;
            vec2 coords;
            float circles(vec2 ts) {
                return sqrt(ts.x*ts.x+ts.y*ts.y);
            }

            float grid(vec2 ts) {
                return min(ts.x, ts.y);
            }



            void main() {
                coords = origin / size + frg_tex;
                m = size/(2 * n_grid * w_grid);
                ts = m * abs(fract(n_grid * coords * size) - 0.5) * 2;
                v = min(circles(ts), 1.0);
                v = smoothstep(1.0,1.8,circles(ts));
               // frag_color = vec4(0.6 + 0.4 * vec3(min(circles(ts), 1.0)), 1.0);
                frag_color = vec4(0.6 + 0.4 * vec3(v), 1.0);
            }


        """))

        self.declare_uniform('camera', Camera.DTYPE, variable='camera')
        self.link()

