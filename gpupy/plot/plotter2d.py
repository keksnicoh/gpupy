from gpupy.plot.style import *

from gpupy.gl.components.camera import Camera2D

from gpupy.gl.components.widgets import Widget
from gpupy.gl.components.widgets.frame import FrameWidget
from gpupy.gl.components.widgets.grid import CartesianGrid
from gpupy.gl.components.widgets.container import Container

from gpupy.gl.common.attributes import CastedAttribute
from gpupy.gl.common import attributes
from gpupy.gl.common.observables import transform_observables

from gpupy.gl.vector import *
from gpupy.gl.common import Event
from gpupy.gl.mesh import StridedVertexMesh, mesh3d_rectangle
from gpupy.gl import *


from OpenGL.GL import * 
import numpy as np 

from functools import partial 

DEFAULT_STYLE = {
    'border':                '0 1 1 0 #528682ff',
    'background-color':      '#303233ff',
    'background-color':      '#202122ff',
    'plot-scaling':          '.5',
    'plot-background-color': '#161c20ff',
    'plot-padding':          '0 0 0 0',
    'min-size':              '100 100',
    'grid-color': '#5f6f77ff',
    'grid-sub-color': '#3c4c55ff',
}


def configuration_space_size(cs):
    """ returns the size of the configuration space """
    return (np.abs(cs.y - cs.x),  np.abs(cs.w - cs.z))

def unit_factor(unit, length):
    f = 1.0
    d = unit - length
    while True:
        if d < 0:
            f *= 0.5
            if length*f < 2*unit:
                break
        else:
            f *= 2
            if length*f > unit:
                break
    return f

def grid(au, cs):
    """ calculates grid from given axes_unit au and 
        configuration space css. This calculations ensures
        that not too many or too less grid lines are visible
        with the current configuration space """
    AT_LEAST_X = 4
    AT_LEAST_Y = 4
    css = configuration_space_size(cs)
    dens = (css[0]/au[0], css[1]/au[1])
    fx = unit_factor(au[0], css[0])
    fy = unit_factor(au[1], css[1])
    return (au[0]/fx/AT_LEAST_X, au[1]/fy/AT_LEAST_Y)

def mat_cs(cs, res):
    """ mat4 for projecting from configuration space **cs** 
        to vertex space of having resolution **res** """
    cl = configuration_space_size(cs)
    return np.array([res.x/cl[0], 0, 0, 0,
                     0, -res.y/cl[1], 0, 0, 
                     0, 0, 1, 0,
                     -res.x/cl[0]*(cs[0]), res.y*(1+cs[2]/cl[1]), 0, 1,],np.float32).reshape((4,4))

class Plotter2d(Widget):
    UBO_DTYPE = np.dtype([
        ('mat_cs', np.float32, (4, 4)),
        ('cs', np.float32, 4),
        ('cs_size', np.float32, 2)
    ])

    # widget configuration
    size = attributes.VectorAttribute(2)
    position = attributes.VectorAttribute(4, (0, 0, 0, 1))

    # configuration space determines [minx, maxx, miny, maxy]
    configuration_space  = attributes.VectorAttribute(4, (0, 1, 0, 1))

    # axes configuration
    # size of one unit (sx, sy) in configuration space
    axes_unit = attributes.VectorAttribute(2, (0.25, 0.25))

    # division of one axes_unit into sub units
    minor_axes_n = attributes.VectorAttribute(2, (5,5))

    # the plot plane is implemented via framebuffer. this factor 
    # allows to adjust the resolution of the framebuffer viewport.
    plot_resolution_factor = CastedAttribute(float, 1)

    background_color       = attributes.VectorAttribute(4, (0, 0, 0, 1))
    plot_background_color  = attributes.VectorAttribute(4, (0, 0, 0, 1))
    plot_padding           = attributes.VectorAttribute(4, (0, 0, 0, 0))




    # common precomputed properties
    configuration_space_size = attributes.ComputedAttribute(configuration_space, 
        descriptor=attributes.VectorAttribute(2), 
        transformation=configuration_space_size)

    def __init__(self, size, 
                       position=(0, 0, 0, 1), 
                       configuration_space=(0, 1, 0, 1), 
                       style=DEFAULT_STYLE,
                       axes_unit=None):
        super().__init__()
        # state
        self.configuration_space = configuration_space
        self.size = size 
        self.position = position
        self._flagged = set()

        if axes_unit is not None:
            self.axes_unit = axes_unit

        #self.axes_unit = (0.1, 0.1)
        self._style = Style({
            'border':                parse_4f1_1c4,
            'background-color':      parse_1c4,
            'grid-color':      parse_1c4,
            'grid-sub-color':      parse_1c4,
            'plot-background-color': parse_1c4,
            'plot-padding':          parse_4f1,
            'min-size':              parse_2f1,
            'plot-scaling': float,
        }, style)

        self.background_color = self._style['background-color']
        self.plot_background_color = self._style['plot-background-color']
        self.plot_padding = self._style['plot-padding']
        self.ubo = None 

        # event hooks
        self.on_pre_plot = Event()
        self.on_post_plot = Event()
        self.on_pre_graph = Event()
        self.on_post_graph = Event()

        self._plot_margin = vec4((0, 0, 0, 0))
        self.grid = None 
        self._plot_container = None 

        self.init()

    def init(self):
        GlConfig.STATE.reserve_buffer_base('gpupy.plot.plotter2d')
        
        self._init_plot_container()
        self._init_plot_camera()
        self._init_grid()
        self._init_ubo()

        self._tt = TestGraph(
            configuration_space=self.configuration_space, 
            plot_size=self._plot_container.widget.size, 
            plot_resolution=self._plot_container.widget.resulution)
        self._tt2 = TestGraph2(
            configuration_space=self.configuration_space, 
            plot_size=self._plot_container.widget.size, 
            plot_resolution=self._plot_container.widget.resulution)

    def _init_ubo(self):
        """ initializes plotting ubo """
        self.ubo = BufferObject.to_device(
            np.zeros(1, dtype=Plotter2d.UBO_DTYPE), 
            target=GL_UNIFORM_BUFFER)
        buffer_base = GlConfig.STATE.RESERVED_BUFFER_BASE['gpupy.plot.plotter2d']
        self.ubo.bind_buffer_base(buffer_base)
        self._plot_container.widget.resulution.on_change.append(self.update_ubo)

        self.update_ubo()

    def _init_grid(self):
        """ initializes grid component """
        major_grid = transform_observables(
            transformation=grid, 
            observables=(self.axes_unit, self.configuration_space))
        self.grid = CartesianGrid(
            size                = self._plot_container.widget.size,
            configuration_space = self.configuration_space,
            major_grid          = major_grid,
            major_grid_color    = self._style['grid-color'],
            minor_grid_color    = self._style['grid-sub-color'],
            background_color    = self.plot_background_color,
            resolution          = self._plot_container.widget.resulution,
            minor_grid_n        = self.minor_axes_n)

    @configuration_space.on_change 
    def update_ubo(self, *e):
        self.ubo.host['mat_cs']  = mat_cs(self.configuration_space, self._plot_container.widget.resulution)
        self.ubo.host['cs']      = self.configuration_space.values
        self.ubo.host['cs_size'] = configuration_space_size(self.configuration_space)
        self.ubo.sync_gpu()

    def _init_plot_camera(self):
        """
        creates a plot camera which is connected to
        the configuration space
        """
        pos = transform_observables(
            lambda s: (s[0]*0.5, s[1]*0.5, 1), vecn((0,0,0)), 
            (self._plot_container.widget.resulution, ))
        self._plot_camera = Camera2D(self._plot_container.widget.resulution, pos)

    def _init_plot_container(self):
        """ initializes main plotcontainer.
            the plotcontainer manages border, margin padding
            and contains the main plot framebuffer """
        plot_container = Container(widget=None, 
                                   size=self.size, 
                                   position=self.position, 
                                   margin=self._plot_margin, 
                                   padding=self.plot_padding,
                                   border=self._style['border'][0], 
                                   border_color=self._style['border'][1])

        plot_container.widget = FrameWidget(size=plot_container.content_size, 
                                            position=plot_container.content_position, 
                                            resulution=transform_observables(
                                                transformation=lambda s, v: s * v.xy, 
                                                observables=(self._.plot_resolution_factor, plot_container.content_size)),
                                            clear_color=self.plot_background_color)

        self._plot_container = plot_container



    def tick(self, redraw=True):
        pre_plot_event = PrePlotEvent(redraw=redraw)
        self.on_pre_plot(pre_plot_event)
        self._plot_container.tick()
        if pre_plot_event.redraw:
            self._plot_container.widget.use()
            self._plot_camera.enable()
            self.grid.tick()
            self.grid.draw()

            self.ubo.bind_buffer_base(GlConfig.STATE.RESERVED_BUFFER_BASE['gpupy.plot.plotter2d'])
            self._tt.draw()
            self._tt2.draw()

            self._plot_container.widget.unuse()
        self.on_post_plot()
        


    def draw(self):
        self._plot_container.render() 

f = lambda x: np.sin(4*x)**2
td = np.array([((0.0005*x, f(0.001*x)), (1, 0)) for x in range(2000)], dtype=np.dtype([('vertex', np.float32, 2), ('color', np.float32, 2)]))

#random walk
l = 10000
s = 100
tdd = np.zeros(l, np.float32)
randoms = np.random.rand(l*s)
l = 0
for i, r in enumerate(randoms):
    if r >= 0.5: l+=0.01
    else: l-=0.01
    if not i % s:
        tdd[i/s] = l
tdd /= np.max(np.abs(tdd))

td2 = np.array([
    ((0, 0), (1,0)),
    ((0, .25), (1,0)),
    ((0, .5), (1,0)),
    ((0, .75), (1,0)),
    ((0, 1), (1,0)),
    ((np.pi/4, 0), (1,0)),
    ((np.pi/4, .25), (1,0)),
    ((np.pi/4, .5), (1,0)),
    ((np.pi/4, .75), (1,0)),
    ((np.pi/4, 1), (1,0)),

    ], dtype=np.dtype([('vertex', np.float32, 2), ('color', np.float32, 2)]))




class TestGraph(Widget):
    configuration_space = attributes.VectorAttribute(4)
    plot_size = attributes.VectorAttribute(2)
    plot_resolution = attributes.VectorAttribute(2)

    def __init__(self, configuration_space, plot_size, plot_resolution, point_size=4):
        self.configuration_space = configuration_space
        self.plot_size = plot_size 
        self.plot_resolution = plot_resolution
        self.program = TestGraphProgram()
        self.point_size = point_size
        self.mesh = StridedVertexMesh(td, GL_POINTS, self.program.attributes)
        self.upload_point_size()

    @plot_resolution.on_change
    @plot_size.on_change
    def upload_point_size(self, *e):
        self.program.uniform('point_size', self.point_size * max(1.0, self.plot_resolution[0]/self.plot_size[0]))


    def draw(self):
        glEnable(GL_PROGRAM_POINT_SIZE)
        self.program.use()
        self.mesh.draw()
        self.program.unuse()



class TestGraphProgram(Program):
    def __init__(self):
        super().__init__()
        self.shaders.append(Shader(GL_VERTEX_SHADER, """
            {% version %}
            {% uniform_block camera %}
            {% uniform_block plot %}
            in vec2 vertex;
            in vec2 color;
            uniform float point_size = 1;
            out vec2 frg_color;
            void main() {
                if (camera.mat_view[0][0] == 1){}
                gl_Position = camera.mat_projection * camera.mat_view * vec4((plot.mat_cs * vec4(vertex, 0, 1)).xyz, 1);
                frg_color = color;
                gl_PointSize = point_size;
            }
        """))
        self.shaders.append(Shader(GL_FRAGMENT_SHADER, """
            {% version %}
            out vec4 out_color;
            in vec2 frg_color;
            void main() {
                out_color = vec4(frg_color.x, 0, 0,1);
            }
        """))

        self.declare_uniform('camera', Camera2D.DTYPE, variable='camera')
        self.declare_uniform('plot', Plotter2d.UBO_DTYPE, variable='plot')
        self.link()
        self.uniform_block_binding('plot', GlConfig.STATE.RESERVED_BUFFER_BASE['gpupy.plot.plotter2d'])





class TestGraph2(Widget):
    configuration_space = attributes.VectorAttribute(4)
    plot_size = attributes.VectorAttribute(2)
    plot_resolution = attributes.VectorAttribute(2)

    def __init__(self, configuration_space, plot_size, plot_resolution):
        self.configuration_space = configuration_space
        self.plot_size = plot_size 
        self.plot_resolution = plot_resolution
        self.program = TestGraph2Program()
        self.mesh = StridedVertexMesh(mesh3d_rectangle(), 
                                      GL_TRIANGLES, 
                                      attribute_locations=self.program.attributes)
        self.x_space = [-.5, 1]
        d = td['vertex'][:,1]
        d = tdd

        self.texture = Texture1D.from_numpy(d)
        self.texture.activate()
        self.texture.interpolation_linear()
        self.program.uniform('tex', self.texture)
        self.program.uniform('u_x_space', self.x_space)

    def draw(self):
        glEnable(GL_PROGRAM_POINT_SIZE)
        self.texture.activate()
        self.program.use()
        self.mesh.draw()
        self.program.unuse()


class TestGraph2Program(Program):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.shaders.append(Shader(GL_VERTEX_SHADER, """
            {% version %}
            {% uniform_block camera %}
            {% uniform_block plot %}
            in vec4 vertex;
            in vec2 tex;
            out vec2 frag_pos;
            void main() {
                gl_Position = camera.mat_projection * camera.mat_view * plot.mat_cs * vec4(
                    plot.cs.x + plot.cs_size.x * vertex.x, 
                    plot.cs.z + plot.cs_size.y * vertex.y, 
                    0, 1);
                frag_pos = vec2(tex.x, 1-tex.y);
            }
        """))

        self.shaders.append(Shader(GL_FRAGMENT_SHADER, """
            {% version %}
            uniform sampler1D tex;
            {% uniform_block plot %}
            in vec2 frag_pos;
            out vec4 frag_color;
            uniform vec2 u_x_space;

            void main() {
                
                float x = -u_x_space.x + (frag_pos.x * plot.cs_size.x + plot.cs.x);

                // if the signal is not periodic
                // if (x > 1 || x < 0) discard

                float y = frag_pos.y * plot.cs_size.y + plot.cs.z;
                float ty  = texture(tex, x).r;
 
                // signed distance from the graph y-value to x-axis.
                // positive if outside otherwise negative.
                float sd = abs(y) - sign(y) * ty;
                
                // relative signed distance. 
                // from x-axis to y-value: [-1,0]
                float rsd = sd / ty * sign(ty);

                // color kernel here
                if (rsd > 0) { discard; }
                frag_color = vec4(y+0.5, 0, 1-y-.5, exp(-2*abs(rsd)));
            }
        """))
        self.declare_uniform('camera', Camera2D.DTYPE, variable='camera')
        self.declare_uniform('plot', Plotter2d.UBO_DTYPE, variable='plot')
        self.link()
        self.uniform_block_binding('plot', GlConfig.STATE.RESERVED_BUFFER_BASE['gpupy.plot.plotter2d'])




class PrePlotEvent():
    def __init__(self, redraw=False):
        self.redraw = redraw 
