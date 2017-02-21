#-*- coding: utf-8 -*-
"""


from glsl_plotter import plotter
plotter(window_size=(400, 400)).plot('x**x', 'sin(x)')


:author: Nicolas 'keksnicoh' Heimann
"""

from gpupy.plot.plotter2d import Plotter2d
from OpenGL.GL import *
from gpupy.gl.vector import *
import numpy as np
from gpupy.gl.components.camera import Camera2D
from gpupy.gl.glfw import GLFW_window
from time import time

from gpupy.gl.components.fps import Fps

from functools import partial

class Plotter2dBasic():
    def __init__(self, window):
        self.window = window
        window.on_ready.append(self.init)
        window.on_cycle.append(self.draw)
        window.on_resize.append(self.resize)
        window.on_cycle.append(partial(self.flag,False))

        self._resizing = False
        self.t = time()
    def flag(self,unf, *e):
        if unf != self._resizing:
            sf = 0.75
            self.plotter.plot_resolution_factor = 1 if not unf else sf
            self._resizing = unf

    def resize(self, window):
        self.flag(True)
        self.draw(window)

    def init(self, window):
        size = window.size
        self.camera = Camera2D(screensize=size, position=size.observe_as_vec3(lambda v: (v[0]/2, v[1]/2, 0)))
        s = self.window.size

        self.plotter = Plotter2d(size, configuration_space=(0, 1, -1, 1))
        self.plotter._plot_container.border = (2,2,2,2)
        self.plotter._plot_container.margin = (10, 10, 10, 10)
        self.border = 3 


    def draw(self, window):
        # very basic plot controlling
        dt = time()-self.t
        #self.plotter2.plot_resolution_factor = 0.8+0.5*np.sin(dt)

        check_cs = False
        speed = 0.005
        if 68 in self.window.active_keys: #d
            self.plotter.configuration_space += (speed, speed, 0, 0)
        if 65 in self.window.active_keys: #a
            self.plotter.configuration_space -= (speed, speed, 0, 0)
        if 87 in self.window.active_keys: #w
            self.plotter.configuration_space += (0, 0, speed, speed)
        if 83 in self.window.active_keys: #s
            self.plotter.configuration_space -= (0, 0, speed, speed)
        if 32 in self.window.active_keys and 340 in self.window.active_keys: #s
            check_cs = True
            self.plotter.configuration_space += (-0.01, 0.01, -0.01, 0.01)
        elif 32 in self.window.active_keys: #s
            check_cs = True
            self.plotter.configuration_space *= (0.99, 0.99, 0.99, 0.99)
        if False and check_cs:
            au = self.plotter.axes_unit
            css = self.plotter.configuration_space_size
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

  
@GLFW_window
def main(window):
    texture_controller = Plotter2dBasic(window)


if __name__ == '__main__':
    main()