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


    def __init__(self, size, position=(0, 0, 0, 1), configuration_space=(0,0), grid=(1,1), background_color=(1, 1, 1, 1), line_color=(0, 0, 0, 1),resolution=None):
        super().__init__()
        self.position = position
        self.size = size
        self.configuration_space = configuration_space
        self.grid = grid

        self.line_color = line_color 
        self.background_color = background_color
        self.resolution = resolution or self.size
        self._init_plane()

    @size.on_change
    def _size_changed(self, size, *e):
        self.program.uniform('size', size.values)

    @configuration_space.on_change
    def _size_changed(self, configuration_space, *e):
        self.program.uniform('origin', (configuration_space.x, configuration_space.z))

    @grid.on_change
    def _size_changed(self, grid, *e):
        self.program.uniform('d_grid', (grid.x, grid.y))

    @grid_width.on_change
    def _size_changed(self, grid_width, *e):
        self.program.uniform('w_grid', (grid_width.x, grid_width.y))


    @resolution.on_change
    def _size_changed(self, resolution, *e):
        self.program.uniform('resolution', (resolution.x, resolution.y))


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
        self.program.uniform('w_grid', self.grid_width)
        self.program.uniform('d_grid', self.grid)
        self.program.uniform('c_bg', self.background_color)
        self.program.uniform('c_line', self.line_color)
        self.program.uniform('resolution', self.resolution)
    def draw(self):
        glEnable(GL_BLEND);
        glBlendFunc(GL_SRC_ALPHA, GL_SRC_ALPHA);
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
            uniform vec2 resolution;
            uniform vec2 size;
            in vec2 tex;
            out vec2 frg_tex;
            void main() {
                gl_Position = camera.mat_projection 
                            * camera.mat_view * mat_model 
                            * vec4(position.x + resolution.x*vertex.x, 
                                   position.y + resolution.y*vertex.y, 
                                   position.z + vertex.z, 
                                   vertex.w);
                frg_tex = resolution*tex;
            }
        """))

        self.shaders.append(Shader(GL_FRAGMENT_SHADER, """
            {% version %}
            out vec4 frag_color;
            in vec2 frg_tex;
            uniform vec2 size;
            uniform vec2 d_grid = vec2(25, 25);
            uniform vec2 w_grid = vec2(1, 1);
            uniform vec2 origin = vec2(0, 0);
            uniform vec4 c_bg;
            uniform vec4 c_line;
            uniform vec2 resolution;
            vec2 m;
            vec2 ts;
            float v;
            vec2 _w_grid;
            vec2 tfn, tf; // triangular function
            vec2 coords;
            float circles(vec2 ts) {
                return sqrt(ts.x*ts.x+ts.y*ts.y);
            }

            float grid(vec2 ts) {
                return min(ts.x, ts.y);
            }

float stroke_alpha(float distance, float linewidth, float antialias) {
    float t = linewidth/2.0 - antialias;
    float signed_distance = distance;
    float border_distance = abs(signed_distance) - t;
    float alpha = border_distance/antialias;
    alpha = exp(-alpha*alpha);
    if( border_distance > (linewidth/2.0 + antialias) )
        return 0.0;
    else if( border_distance < 0.0 )
        return 1.0;
    else
        return alpha;
}

float a;
            void main() {
                coords = (0.5*origin*size + frg_tex * size / resolution + d_grid/2);
                _w_grid = w_grid;

                // triangles, normalized
                //
                //  1 |\      /\      /\      .
                //    | \    /  \    /  \    .
                //    |  \  /    \  /    \  /
                //    |   \/      \/      \/
                //  0 +---|--------|-----------
                //       d_grid   2*d_grid 
                //  
                tfn = 2*abs(fract(coords/d_grid) - 0.5);

                // scaling factor
                m = d_grid / (2*_w_grid);

                // triangles, y=1 at n*d_grid +/- 0.5*w_grid
                // 
                // 1 |     \                            /
                //   |      \                          /
                //   ..         ...              ...
                //   |                \     /
                //   |                 \   /
                //   |                  \ /
                // 0 +-----|-------------|--------------|
                //       d_grid-w_grid    d_grid     d_grid+w_grid
                tf = m * tfn;
     
                // linear 
                v = min(grid(tf), 1.0);

                // smooth
               // v = smoothstep(0.5,1.0,grid(tf));
                a = stroke_alpha(v, 1.5, 3);
                vec4 c = mix(c_line, c_bg, v);
                frag_color = vec4(c.xyz, c.a*a);
                //frag_color = vec4(1, 0, 0, 1);
               // frag_color = vec4(vec3(v), 1.0);
            }


        """))

        self.declare_uniform('camera', Camera.DTYPE, variable='camera')
        self.link()

