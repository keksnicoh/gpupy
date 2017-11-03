from gpupy.plot.style import *

from gpupy.gl.components import Component
from gpupy.gl.components.camera import Camera2D
from gpupy.gl.components.widgets import Widget
from gpupy.gl.components.widgets.frame import FrameWidget, FramestackWidget
from gpupy.gl.components.widgets.grid import CartesianGrid
from gpupy.gl.components.widgets.container import Container
from gpupy.gl.mesh import mesh3d_rectangle, StridedVertexMesh

from gpupy.gl.lib import Event, attributes, observables
from gpupy.gl.lib.vector import *
from gpupy.gl import *
from gpupy.gl import GPUPY_GL as _G

from OpenGL.GL import * 

import numpy as np 
from functools import partial 
from collections import OrderedDict

DEFAULT_STYLE = {
    'border':                '0 1 1 0 #528682ff',
    'border':                '0 1 1 0 #ff8500ff',
    'border':                '0 1 1 0 #ffffffff',

    'background-color':      '#303233ff',
    'background-color':      '#202122ff',
    'background-color':      '#101011ff',
    'background-color':      '#232323ff',


    'plot-scaling':          '.5',
    'plot-background-color': '#161c20ff',
    'plot-background-color': '#121212ff',
    'plot-padding':          '0 0 0 0',
    'min-size':              '100 100',
    'grid-color':            '#5f6f77ff',
    'grid-sub-color':        '#3c4c55ff',

    'grid-color':            '#5c5c5cff',
    'grid-sub-color':        '#2b2b2bff',
}


def cs_size(cs):
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
    css = cs_size(cs)
    dens = (css[0]/au[0], css[1]/au[1])
    fx = unit_factor(au[0], css[0])
    fy = unit_factor(au[1], css[1])
    return (au[0]/fx/AT_LEAST_X, au[1]/fy/AT_LEAST_Y)

def mat_cs(cs, res):
    """ mat4 for projecting from configuration space **cs** 
        to vertex space of having resolution **res** """
    cl = cs_size(cs)
    tx = -res.x/cl[0]*(cs[0])
    ty = res.y*(1+cs[2]/cl[1])
    return np.array([res.x/cl[0], 0, 0, 0,
                     0, -res.y/cl[1], 0, 0, 
                     0, 0, 1, 0,
                     tx, ty, 0, 1,], np.float32).reshape((4,4))

class Plotter2d(Widget):

    UBO_DTYPE = np.dtype([
        ('mat_cs',  np.float32, (4, 4)),
        ('cs',      np.float32, 4),
        ('cs_size', np.float32, 2)
    ])

    # widget configuration
    size = attributes.VectorAttribute(2)
    position = attributes.VectorAttribute(4, (0, 0, 0, 1))

    # configuration space determines [minx, maxx, miny, maxy]
    cs  = attributes.VectorAttribute(4, (0, 1, 0, 1))

    # axes configuration
    # size of one unit (sx, sy) in configuration space
    axes_unit = attributes.VectorAttribute(2, (0.25, 0.25))

    # division of one axes_unit into sub units
    minor_axes_n = attributes.VectorAttribute(2, (5, 5))

    # the plot plane is implemented via framebuffer. this factor 
    # allows to adjust the resolution of the framebuffer viewport.
    plot_resolution_factor = attributes.CastedAttribute(float, 1)

    background_color       = attributes.VectorAttribute(4, (0, 0, 0, 1))
    plot_background_color  = attributes.VectorAttribute(4, (0, 0, 0, 1))
    plot_padding           = attributes.VectorAttribute(4, (0, 0, 0, 0))

    # common precomputed properties
    cs_size = attributes.ComputedAttribute(cs, 
        descriptor=attributes.VectorAttribute(2), 
        transformation=cs_size)

    def __init__(self, size, 
                       position=(0, 0, 0, 1), 
                       cs=(0, 1, 0, 1), 
                       style=DEFAULT_STYLE,
                       axes_unit=None):

        super().__init__()

        # state
        self.cs = cs
        self.size = size 
        self.position = position

        if axes_unit is not None:
            self.axes_unit = axes_unit

        #self.axes_unit = (0.1, 0.1)
        self._style = Style({
            'border':                parse_4f1_1c4,
            'background-color':      parse_1c4,
            'grid-color':            parse_1c4,
            'grid-sub-color':        parse_1c4,
            'plot-background-color': parse_1c4,
            'plot-padding':          parse_4f1,
            'min-size':              parse_2f1,
            'plot-scaling': float,
        }, style)

        self.background_color = self._style['background-color']
        self.plot_background_color = self._style['plot-background-color']
        self.plot_padding = self._style['plot-padding']
        self.ubo = None

        self.on_plot = Event() 

        self._plot_margin = vec4((0, 0, 0, 0))
        self.grid = None 
        self.layer = None 

        self._graphs = []
        self._graphs_initialized = False

        self._init()
        self.a = False
        self.last_fr = False
        self.on_plot.once(self.init_graphs)

        self.cmc = [
            [1, 0, 0, 1],
            [1, 1, 0, 1],
            [1, 0, 1, 1],
            [0, 1, 0, 1],
            [0, 0, 1, 1],
            [1, 1, 1, 1],
        ]

    # -- graph api

    def init_graphs(self):
        for graph in self._graphs:
            graph.init()
        self._graphs_initialized = True

    def append(self, graph):
        self._graphs.append(graph)
        if self._graphs_initialized:
            graph.init()
            graph.resolution = self.plotframe.resulution
            graph.viewport = self.plotframe.resulution
        
    def __iadd__(self, graph):
        self.append(graph)
        return self

    # -- init

    def _init(self):  
        self._initlayer()
        self._initplotcam()
        self._init_grid()
        self._init_ubo()


    # -- plot ubo 

    def _init_ubo(self):
        """ initializes plotting ubo """
        self.ubo = BufferObject.to_device(
            np.zeros(1, dtype=Plotter2d.UBO_DTYPE), 
            target=GL_UNIFORM_BUFFER)
        buffer_base = GPUPY_GL.CONTEXT.buffer_base('gpupy.plot.plotter2d')
        self.ubo.bind_buffer_base(buffer_base)
        self.update_ubo()

    @cs.on_change 
    def update_ubo(self, *e):
        self.ubo.host['mat_cs']  = mat_cs(self.cs, self.layer.content_size)
        self.ubo.host['cs']      = self.cs.values
        self.ubo.host['cs_size'] = cs_size(self.cs)
        self.ubo.sync_gpu()

    # -- grid 

    def _init_grid(self):
        """ initializes grid component """
        major_grid = observables.transform_observables(
            transformation=grid, 
            observables=(self.axes_unit, self.cs))

        self.grid = CartesianGrid(
            size                = self.layer.content_size,
            position            = self.layer.content_position,
            cs                  = self.cs,
            major_grid          = major_grid,
            major_grid_color    = self._style['grid-color'],
            minor_grid_color    = self._style['grid-sub-color'],
            background_color    = self.plot_background_color,
            resolution          = self.layer.content_size,
            minor_grid_n        = self.minor_axes_n)#.dev()

    # -- camera

    def _initplotcam(self):
        """
        creates a plot camera which is connected to
        the configuration space
        """
        pos = observables.transform_observables(
            lambda s: (s[0]*0.5, s[1]*0.5, 1), vecn((0,0,0)), 
            (self.layer.content_size, ))
        self.plotcam = Camera2D(self.layer.content_size, pos)

    # -- container

    def _initlayer(self):
        """ initializes main plotcontainer.
            the plotcontainer manages border, margin padding
            and contains the main plot framebuffer """

        layer = Container(
            size=self.size, 
            position=self.position, 
            margin=self._plot_margin, 
            padding=self.plot_padding,
            border=self._style['border'][0], 
            border_color=self._style['border'][1])

        self.plotframe = FrameWidget(
            position=layer.content_position,
            size=layer.content_size,
            resulution=layer.content_size,
            clear_color=(0, 0, 0, 0))
        self.layer = layer
        self.layer.content_size.on_change.append(self.update_ubo)

    def tick(self):
        self.on_tick()

        # -- tick the components
        self.plotcam.enable()
        self.layer.tick()
        self.grid.tick()
        self.plotframe.tick()

        # -- graph rendering
        self.plotframe.use()
        self.plotcam.enable()
        self.on_plot()
        self.ubo.bind_buffer_base(GPUPY_GL.CONTEXT.buffer_base('gpupy.plot.plotter2d'))
        for graph in self._graphs:
            graph.tick()
            graph.render()
        self.plotframe.unuse()

    def draw(self):
        self.grid.render()
        self.layer.render() 
        self.plotframe.render()



class PrePlotEvent():
    def __init__(self, redraw=False):
        self.redraw = redraw 

#http://stackoverflow.com/questions/2171085/opengl-blending-with-previous-contents-of-framebuffer
