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
    'border':                '5 #ff0000ff',
    'background-color':      '#111144ff',
    'plot-scaling':          '.5',
    'plot-background-color': '#eeeeeeee',
    'plot-padding':          '0 0 0 0',
    'min-size':              '100 100',
}


class Plotter2d(Widget):
    size                   = Vec2Field()
    position               = Vec4Field((0, 0, 0, 1))

    configuration_space    = Vec4Field((0, 0, 0, 0))

    background_color       = Vec4Field((0, 0, 0, 1))
    plot_background_color  = Vec4Field((0, 0, 0, 1))
    plot_padding           = Vec4Field((0, 0, 0, 0))

    plot_resolution_factor = CastedAttrbiute(float, 1)

    def __init__(self, size, 
                       position=(0, 0, 0, 1), 
                       configuration_space=(0, 1, 0, 1), 
                       style=DEFAULT_STYLE):
        super().__init__()
        # state
        self.configuration_space = configuration_space
        self.size = size 
        self.position = position
        self._flagged = set()

        self._style = Style({
            'border':                parse_4f1_1c4,
            'background-color':      parse_1c4,
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

        self._plot_margin = vec4((20, 20, 20, 20))

        self.init()


    def init(self):
        self._init_plot_container()
        self._init_plot_camera()

        self.grid = CartesianGrid(
            size=self._plot_container.widget.capture_size,
            configuration_space=self.configuration_space)

    def _init_plot_camera(self):
        """
        creates a plot camera which is connected to
        the configuration space
        """
        cam_position = self.configuration_space.observe_as_vec3(
            lambda v: (v[0]+np.abs(v[1]-v[0])*0.5, v[2]+np.abs(v[3]-v[2])*0.5, 0))

        cam_screensize = self.configuration_space.observe_as_vec2(
            lambda v: (np.abs(v[1]-v[0]), np.abs(v[3]-v[2])))

        self._plot_camera = Camera2D(cam_screensize, cam_position)


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
                                                transformation=lambda s, v: s * v.xy*2.6, 
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
            self._plot_container.widget.unuse()
        self.on_post_plot()


    def draw(self):
        glClearColor(*self.background_color.values)
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        self._plot_container.render() 

class PrePlotEvent():
    def __init__(self, redraw=False):
        self.redraw = redraw 
