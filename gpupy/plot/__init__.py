from gpupy.gl.glfw import GLFW_Context, GLFW_run

from gpupy.plot.plotter2d import Plotter2d
from OpenGL.GL import *
from gpupy.gl import *
from gpupy.gl.common.vector import *
import numpy as np
from gpupy.gl.components.camera import Camera2D
from gpupy.gl.glfw import GLFW_window
from time import time
from gpupy.plot.graph.frgfnc import Frag1DGraph, Frag2DGraph
from gpupy.plot.graph.glpoints import GlPointsGraph
from gpupy.plot import domain

from functools import partial


def plot2d(f):
    def ready(window):
        Plotter2dBasic(window, f)
    width, height = 400, 400
    title = 'plot'
    window = GLFW_Context(size=(width, height), title=title)
    window.on_ready.append(ready)
    for window in GLFW_run(window):
        pass

class Plotter2dBasic():
    def __init__(self, window, plot):
        self.window = window
        window.on_ready.append(self.init)
        window.on_cycle.append(self.draw)
        window.on_resize.append(self.resize)
        window.on_cycle.append(partial(self.flag,False))
        self._plot = plot
        self._resizing = False
        self.t = time()
    def flag(self,unf, *e):
        if unf != self._resizing:
            sf = 0.5
            self.plotter.plot_resolution_factor = 1 if not unf else sf
            self._resizing = unf

    def resize(self, window):
        self.flag(True)
        self.draw(window)

    def init(self, window):
        size = window.size
        self.camera = Camera2D(screensize=size, position=size.observe_as_vec3(lambda v: (v[0]/2, v[1]/2, 0)))
        s = self.window.size
        self.plotter = Plotter2d(size, cs=(-4, 4, -4, 4))
        self._plot(self.plotter)
        self.plotter.init()
        self.plotter._plot_container.border = (2,2,2,2)
        self.plotter._plot_container.margin = (10, 10, 10, 10)
        self.border = 3 

    def draw(self, window):
        # very basic plot controlling
        dt = time()-self.t
        #self.plotter2.plot_resolution_factor = 0.8+0.5*np.sin(dt)

        check_cs = False
        speed = 0.05
        if 68 in self.window.active_keys: #d
            self.plotter.cs += (speed, speed, 0, 0)
        if 65 in self.window.active_keys: #a
            self.plotter.cs -= (speed, speed, 0, 0)
        if 87 in self.window.active_keys: #w
            self.plotter.cs += (0, 0, speed, speed)
        if 83 in self.window.active_keys: #s
            self.plotter.cs -= (0, 0, speed, speed)
        if 32 in self.window.active_keys and 340 in self.window.active_keys: #s
            check_cs = True
            self.plotter.cs += (-0.01, 0.01, -0.01, 0.01)
        elif 32 in self.window.active_keys: #s
            check_cs = True
            self.plotter.cs *= (0.99, 0.99, 0.99, 0.99)
        if False and check_cs:
            au = self.plotter.axes_unit
            css = self.plotter.cs_size
            n = (css.x/au.x, css.y/au.y)
            if n[0] > 10:
                self.plotter.axes_unit.x = css.x/5
            if n[1] > 10:
                self.plotter.axes_unit.y = css.y/5
            if n[0] < 5:
                self.plotter.axes_unit.x = css.x/10
            if n[1] < 5:
                self.plotter.axes_unit.y = css.y/10
            print(self.plotter.axes_unit)
        dt = time() - self.t
        self.plotter.tick()

        glClearColor(*self.plotter.background_color.values)
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        self.camera.enable()
        self.plotter.draw()