"""
grid rendering widgets and shaders based on the paper 
"Antialiased 2D Grid, Marker, and Arrow Shaders" by
Nicolas P. Rougier published November 2014 in the
Journal of Computer Graphics Techniques (JCGT):
    http://jcgt.org/published/0003/04/01/

A grid can be drawn on any surface where the texture
coordinate is within [-0.5, 0.5]. The fragment shader
renders lines which have a fixed size compared to the
vieport resolution. 
"""

from gpupy.gl.components.widgets import Widget
from gpupy.gl.common import attributes
from gpupy.gl.common.observables import transform_observables

from gpupy.gl import * 
from gpupy.gl.mesh import mesh3d_rectangle, StridedVertexMesh
from gpupy.gl.common.vector import *

from OpenGL.GL import *

import numpy as np 

import os 
from functools import partial 

class AbstractGrid(Widget):
    """

    """
    # widget configuration
    size                 = attributes.VectorAttribute(2)
    resolution           = attributes.VectorAttribute(2)
    position             = attributes.VectorAttribute(4)
    cs  = attributes.VectorAttribute(4)

    # grid configuration
    major_grid         = attributes.VectorAttribute(2, (.5, .5))
    major_grid_width   = attributes.CastedAttribute(float,  1.5)
    major_grid_color   = attributes.VectorAttribute(4, (0, 0, 0, 1))

    minor_grid_width   = attributes.CastedAttribute(float,  1)
    minor_grid_color   = attributes.VectorAttribute(4, (0, 0, 0, 1))
    minor_grid_n       = attributes.VectorAttribute(2, (5, 5))

    # style
    background_color  = attributes.VectorAttribute(4, (1, 1, 1, 1))

    def __init__(self, size, 
                       position                 = (0, 0, 0, 1), 
                       cs                       = (0,0), 
                       major_grid               = (1,1), 
                       background_color         = (1, 1, 1, 1), 
                       major_grid_color         = (0, 0, 0, 1),
                       resolution               = None,
                       minor_grid_color         = (0,0,0,1),
                       minor_grid_n             = (5, 5)):

        super().__init__()
        self.position = position
        self.size = size
        self.cs = cs

        self.major_grid = major_grid
        self.major_grid_color = major_grid_color 
        self.minor_grid_color = minor_grid_color 
        self.minor_grid_n = minor_grid_n
        self.background_color = background_color

        self._req_uniforms = True
        self.resolution = resolution or self.size
        self._init_plane()

    @size.on_change
    @cs.on_change
    @major_grid.on_change
    @minor_grid_n.on_change
    @minor_grid_width.on_change
    @major_grid_width.on_change
    @resolution.on_change
    @position.on_change
    def req_uniforms(self, *e):
        self._req_uniforms = True

    def upload_uniforms(self):
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
        l1 = self.cs.values * 1.0001
        mg = self.major_grid.values 
        cs = self.cs.values 

        self.program.uniform('u_limits1',            l1)
        self.program.uniform('u_limits2',            cs)
        self.program.uniform('u_major_grid_step',    mg)
        self.program.uniform('u_minor_grid_step',    self.major_grid.values/self.minor_grid_n)
        self.program.uniform('u_major_grid_width',   self.minor_grid_width * max(1.0, self.resolution[0] / self.size[0]))
        self.program.uniform('u_minor_grid_width',   self.minor_grid_width * max(1.0, self.resolution[0] / self.size[0]))
        self.program.uniform('u_major_grid_color',   self.major_grid_color)
        self.program.uniform('u_minor_grid_color',   self.minor_grid_color)
        self.program.uniform('iResolution',          self.resolution)
        self.program.uniform('u_antialias',          2)
        self.program.uniform('c_bg',                 self.background_color)

        self._req_uniforms = False

     #   print('RES', self.resolution, 'size', self.size, 'CS', self.cs)
     #   print('GRID', self.major_grid)
    def _init_plane(self): 
        self.program = GridProgram()

        self.program.uniform_block_binding('camera', GPUPY_GL.CONTEXT.buffer_base('gpupy.gl.camera'))
        self.upload_uniforms()

        self.mesh = StridedVertexMesh(mesh3d_rectangle(), 
                                      GL_TRIANGLES, 
                                      attribute_locations=self.program.attributes)

    def _tick(self):
        if self._req_uniforms:
            self.upload_uniforms()


    def draw(self):
        glEnable(GL_BLEND);
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA);
        self.program.use()
        self.mesh.draw()
        self.program.unuse()

class CartesianGrid(AbstractGrid): pass 

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


