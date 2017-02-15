from gpupy.plot.style import *

from gpupy.gl.components.camera import Camera2D

from gpupy.gl.components.widgets import Widget
from gpupy.gl.components.widgets.frame import FrameWidget
from gpupy.gl.components.widgets.grid import CartesianGrid
from gpupy.gl.components.widgets.container import Container

from gpupy.gl.common.attributes import CastedAttrbiute
from gpupy.gl.common import attributes
from gpupy.gl.common.observables import transform_observables

from gpupy.gl.vector import *
from gpupy.gl.common import Event
from gpupy.gl.mesh import StridedVertexMesh
from gpupy.gl import *


from OpenGL.GL import * 
import numpy as np 

from functools import partial 



DEFAULT_STYLE = {
    'border':                '0 1 1 0 #528682ff',
    'background-color':      '#303233ff',
    'plot-scaling':          '.5',
    'plot-background-color': '#494F52ff',
    'plot-padding':          '0 0 0 0',
    'min-size':              '100 100',
    'grid-color': '#4D5D66ff',
    'grid-sub-color': '#3c4c55ff',
}
def axes_unit_pixels(size, configuration_space, axes_unit, rs):
    lx = np.abs(configuration_space.y - configuration_space.x)
    ly = np.abs(configuration_space.w - configuration_space.z)
    aur = (axes_unit.x / lx, axes_unit.y / ly)
    return (size.x * aur[0], size.y * aur[1])


class Plotter2d(Widget):
    size                   = attributes.VectorAttribute(2)
    position               = attributes.VectorAttribute(4, (0, 0, 0, 1))

    configuration_space      = attributes.VectorAttribute(4, (0, 1, 0, 1))
    configuration_space_size = attributes.ComputedAttribute(configuration_space, descriptor=attributes.VectorAttribute(2))

    background_color       = attributes.VectorAttribute(4, (0, 0, 0, 1))
    plot_background_color  = attributes.VectorAttribute(4, (0, 0, 0, 1))
    plot_padding           = attributes.VectorAttribute(4, (0, 0, 0, 0))

    axes_unit = attributes.VectorAttribute(2, (0.1, 0.1))
    plot_resolution_factor = CastedAttrbiute(float, 1)


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

        # event hooks
        self.on_pre_plot = Event()
        self.on_post_plot = Event()
        self.on_pre_graph = Event()
        self.on_post_graph = Event()

        self._plot_margin = vec4((0, 0, 0, 0))
        self.grid = None 
        self._plot_container = None 

        self.init()

    @configuration_space_size.transformation
    def get_configuration_space_size(self, configuration_space):
        return (np.abs(configuration_space.y - configuration_space.x), 
                np.abs(configuration_space.w - configuration_space.z))

    def init(self):
        self._init_plot_container()
        self._init_plot_camera()

        self.grid = CartesianGrid(
            size=self._plot_container.widget.size,
            configuration_space=self.configuration_space,
            grid=transform_observables(
                transformation=axes_unit_pixels,
                observables=(self._plot_container.widget.size, 
                             self.configuration_space, 
                             self.axes_unit,
                             self._.plot_resolution_factor)),
            line_color=self._style['grid-color'],
            sub_line_color=self._style['grid-sub-color'],
            background_color=self.plot_background_color,
            resolution=self._plot_container.widget.capture_size)

        self._tt = TestGraph(configuration_space=self.configuration_space, size=self._plot_container.widget.size, resolution=self._plot_container.widget.capture_size)
    def _init_plot_camera(self):
        """
        creates a plot camera which is connected to
        the configuration space
        """
        pos = transform_observables(lambda s: (s[0]*0.5, s[1]*0.5, 1), vecn((0,0,0)), (self._plot_container.widget.capture_size, ))
        self._plot_camera = Camera2D(self._plot_container.widget.capture_size, pos)


    def _init_plot_container(self):
        """
        initializes plot container widget as well as
        the main plot framebuffer
        """
        plot_container = Container(widget=None, 
                                   size=self.size, 
                                   position=self.position, 
                                   margin=self._plot_margin, 
                                   padding=self.plot_padding,
                                   border=self._style['border'][0], 
                                   border_color=self._style['border'][1])

        plot_container.widget = FrameWidget(size=plot_container.content_size, 
                                            position=plot_container.content_position, 
                                            capture_size=transform_observables(
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
            self.grid.draw()
            self._tt.draw()
            self._plot_container.widget.unuse()
        self.on_post_plot()
        


    def draw(self):
        self._plot_container.render() 

f = lambda x: np.sin(x)**2
td = np.array([((0.0001*x, f(0.001*x)), (1, 0)) for x in range(20000)], dtype=np.dtype([('vertex', np.float32, 2), ('color', np.float32, 2)]))
class TestGraph(Widget):
    # a plot has a domain matrix which transforms values from the plot domain into
    # screenspace.
    # then normal vertex processing takes place

    # a plot must know
    # - configuration space 
    # - screenspace
    # - viewport resolution

    configuration_space = attributes.VectorAttribute(4)
    plane_size = attributes.VectorAttribute(2)
    plane_resolution = attributes.VectorAttribute(2)
    def __init__(self, configuration_space, size, resolution):
        self.configuration_space = configuration_space
        self.plane_size = size 
        self.plane_resolution = resolution
        self.program = TestGraphProgram()
        self.mesh = StridedVertexMesh(td, GL_POINTS, self.program.attributes)
        self.mat_domain_vertex = None
        self.upload_cs_shader()

    @configuration_space.on_change
    @plane_resolution.on_change
    @plane_size.on_change
    def upload_cs_shader(self, *e):
        cs = self.configuration_space
        cl = (np.abs(cs[1]-cs[0]), np.abs(cs[3]-cs[2]))
        self.mat_domain_vertex = np.array([
            self.plane_resolution.x/cl[0], 0, 0, 0,
            0, -self.plane_resolution.y/cl[1], 0, 0, 
            0, 0, 1, 0,
            self.plane_resolution.x*(-0.5*cs[0]), self.plane_resolution.y*(1+.5*cs[2]), 0, 1,],np.float32).transpose()
        self.program.uniform('mat_domain', self.mat_domain_vertex)

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
            in vec2 vertex;
            in vec2 color;
            out vec2 frg_color;
            uniform mat4 mat_domain;
            void main() {
                if (camera.mat_view[0][0] == 1){}
                gl_Position = camera.mat_projection * camera.mat_view * mat_domain * vec4(vertex, 0, 1);
                frg_color = color;
                gl_PointSize = 1;
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
        self.link()


class PrePlotEvent():
    def __init__(self, redraw=False):
        self.redraw = redraw 
