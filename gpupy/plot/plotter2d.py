from gpupy.plot.style import *

from gpupy.gl.components import Component
from gpupy.gl.components.camera import Camera2D
from gpupy.gl.components.widgets import Widget
from gpupy.gl.components.widgets.frame import FrameWidget
from gpupy.gl.components.widgets.grid import CartesianGrid
from gpupy.gl.components.widgets.container import Container

from gpupy.gl.common import Event, attributes, observables
from gpupy.gl.common.vector import *
from gpupy.gl import *

from OpenGL.GL import * 

import numpy as np 
from functools import partial 
from collections import OrderedDict

DEFAULT_STYLE = {
    'border':                '0 1 1 0 #528682ff',
    'background-color':      '#303233ff',
    'background-color':      '#202122ff',
    'plot-scaling':          '.5',
    'plot-background-color': '#161c20ff',
    'plot-padding':          '0 0 0 0',
    'min-size':              '100 100',
    'grid-color':            '#5f6f77ff',
    'grid-sub-color':        '#3c4c55ff',
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
        ('mat_cs', np.float32, (4, 4)),
        ('cs', np.float32, 4),
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
    minor_axes_n = attributes.VectorAttribute(2, (5,5))

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
        self._flagged = set()

        self._redraw = True
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

        # event hooks
        self.on_pre_plot = Event()
        self.on_post_plot = Event()
        self.on_pre_graph = Event()
        self.on_post_graph = Event()

        self._plot_margin = vec4((0, 0, 0, 0))
        self.grid = None 
        self._plot_container = None 
        self._graphs = OrderedDict()

        self._initialized = False

    # -- graph api

    def __setitem__(self, key, value):
        self._graphs[key] = value


    def __getitem__(self, key):
        return self._graphs[key]

    def add(self, value):
        self._graphs[id(value)] = value 
        return self 
        
    def __iadd__(self, value):
        self.add(value)
        return self

    # -- init

    def init(self):        
        self._init_plot_container()
        self._init_plot_camera()
        self._init_grid()
        self._init_ubo()

        for d in self._graphs.values():
            try:
                cs = d.cs
            except Exception:
                d.cs = self.cs.values
            d.frame               = self._plot_container.widget
            d.init()


        self._initialized = True

    # -- plot ubo 

    def _init_ubo(self):
        """ initializes plotting ubo """
        self.ubo = BufferObject.to_device(
            np.zeros(1, dtype=Plotter2d.UBO_DTYPE), 
            target=GL_UNIFORM_BUFFER)
        buffer_base = GPUPY_GL.CONTEXT.buffer_base('gpupy.plot.plotter2d')
        self.ubo.bind_buffer_base(buffer_base)
        self._plot_container.widget.resulution.on_change.append(self.update_ubo)
        self.update_ubo()

    @cs.on_change 
    def update_ubo(self, *e):
        self.ubo.host['mat_cs']  = mat_cs(self.cs, self._plot_container.widget.resulution)
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
            size                = self._plot_container.widget.size,
            cs                  = self.cs,
            major_grid          = major_grid,
            major_grid_color    = self._style['grid-color'],
            minor_grid_color    = self._style['grid-sub-color'],
            background_color    = self.plot_background_color,
            resolution          = self._plot_container.widget.resulution,
            minor_grid_n        = self.minor_axes_n)

    # -- camera

    def _init_plot_camera(self):
        """
        creates a plot camera which is connected to
        the configuration space
        """
        pos = observables.transform_observables(
            lambda s: (s[0]*0.5, s[1]*0.5, 1), vecn((0,0,0)), 
            (self._plot_container.widget.resulution, ))
        self._plot_camera = Camera2D(self._plot_container.widget.resulution, pos)

    # -- container

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
                                            resulution=observables.transform_observables(
                                                transformation=lambda s, v: s * v.xy, 
                                                observables=(self._.plot_resolution_factor, plot_container.content_size)),
                                            clear_color=self.plot_background_color)

        self._plot_container = plot_container


        
    @size.on_change
    @position.on_change
    @cs.on_change
    @axes_unit.on_change
    @minor_axes_n.on_change
    @plot_resolution_factor.on_change
    @background_color.on_change
    @plot_background_color.on_change
    @plot_padding.on_change
    def force_redraw(self, *e):
        self._redraw = True

    def tick(self, redraw=False):
        if not self._initialized:
            self.init()
            redraw = True

        pre_plot_event = PrePlotEvent(redraw=True if self._redraw else redraw)
        self.on_pre_plot(pre_plot_event)
        self._plot_container.tick()

        if pre_plot_event.redraw:
            self._plot_container.widget.use()
            self._plot_camera.enable()
            self.grid.tick()
            self.grid.draw()

            self.ubo.bind_buffer_base(GPUPY_GL.CONTEXT.buffer_base('gpupy.plot.plotter2d'))

            rs = self._plot_container.widget.resulution.xy
            size = self._plot_container.widget.size.xy
            for d in self._graphs.values():
                # we only pass the values here, since the plot 
                # can be plotted within multiple plotters
                d.resolution = rs
                d.viewport = size

                d.draw()
            self._plot_container.widget.unuse()
            self._redraw = False
        self.on_post_plot()
        

    def draw(self):
        self._plot_container.render() 




class PrePlotEvent():
    def __init__(self, redraw=False):
        self.redraw = redraw 

