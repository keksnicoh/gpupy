#-*- coding: utf-8 -*-
"""


from glsl_plotter import plotter
plotter(window_size=(400, 400)).plot('x**x', 'sin(x)')










:author: Nicolas 'keksnicoh' Heimann
"""

from gpupy.plot.plotter2d import Plotter2d
from OpenGL.GL import *
from gpupy.gl.common.vector import *
import numpy as np
from gpupy.gl.components.camera import Camera2D
from gpupy.gl.glfw import GLFW_WindowFunction
from time import time

from gpupy.gl.components.fps import Fps

from functools import partial

class Plotter2dBasic():
    def __init__(self, window):
        self.window = window
        window.on_init.append(self.init)
        window.on_cycle.append(self.draw)
        window.on_resize.append(self.resize)
        window.on_cycle.append(partial(self.flag,False))

        self._resizing = False
        self.t = time()
    def flag(self,unf, *e):
        if unf != self._resizing:
            sf = 0.5
            self.plotter.plot_resolution_factor = 1 if not unf else sf
            self.plotter2.plot_resolution_factor = 1 if not unf else sf
            self.plotter3.plot_resolution_factor = 1 if not unf else sf
            self.plotter32.plot_resolution_factor = 1 if not unf else sf
            self.plotter33.plot_resolution_factor = 1 if not unf else sf
            self.plotter34.plot_resolution_factor = 1 if not unf else sf
            self.plotter4.plot_resolution_factor = 1 if not unf else sf
            self._resizing = unf

    def resize(self):
        s = self.window.get_size()
        self.flag(True)

        self.plotter.size = (s[0], s[1]/4)
        self.plotter2.size = (s[0], s[1]/4)
        self.plotter2.position = (0, s[1]/4, 0, 1)
        self.plotter3.size = (s[0]/4, s[1]/4)
        self.plotter3.position = (0, 2*s[1]/4, 0, 1)
        self.plotter32.size = (s[0]/4, s[1]/4)
        self.plotter32.position = (s[0]/4, 2*s[1]/4, 0, 1)
        self.plotter33.size = (s[0]/4, s[1]/4)
        self.plotter33.position = (2*s[0]/4, 2*s[1]/4, 0, 1)
        self.plotter34.size = (s[0]/4, s[1]/4)
        self.plotter34.position = (3*s[0]/4, 2*s[1]/4, 0, 1)
        self.plotter4.size = (s[0], s[1]/4)
        self.plotter4.position = (0, 3*s[1]/4, 0, 1)

        self.camera.screensize = self.window.get_size()
        self.draw()

    def init(self):
        size = vec2(self.window.get_size())
        self.camera = Camera2D(screensize=size, position=size.observe_as_vec3(lambda v: (v[0]/2, v[1]/2, 0)))
        s = self.window.get_size()
        self.plotter = Plotter2d((s[0], s[1]/4), configuration_space=(0, 1, 0, 1))
        self.plotter.axes_unit = (np.pi/4, 0.25)
        self.plotter.plot_padding = (10,10,10,10)
        self.plotter2 = Plotter2d((s[0], s[1]/4), (0, s[1]/4, 0, 1), configuration_space=(0, 2, 0, 2))
        self.plotter3 = Plotter2d((s[0]/4, s[1]/4), (0, 2*s[1]/4, 0, 1), configuration_space=(0, 2, 0, 1))
        self.plotter32 = Plotter2d((s[0]/4, s[1]/4), (s[0]/4, 2*s[1]/4, 0, 1), configuration_space=(0, 1, 0, 3))
        self.plotter32._plot_container.border = (5,5,5,5)
        self.plotter32._plot_container.margin = (15,15,15,15)
        self.plotter32._plot_container.border_color = (1,0,1,0.5)
        self.plotter33 = Plotter2d((s[0]/4, s[1]/4), (2*s[0]/4, 2*s[1]/4, 0, 1), configuration_space=(0.5, 1, 0, 1))
        self.plotter33._plot_container.border = (1,1,1,1)
        self.plotter33._plot_container.margin = (15,15,15,15)
        self.plotter33.plot_padding = (15,15,15,15)
        self.plotter33._plot_container.border_color = (1,0,1,0.5)
        self.plotter34 = Plotter2d((s[0]/4, s[1]/4), (3*s[0]/4, 2*s[1]/4, 0, 1), configuration_space=(-1, 1, -1, 1))
        self.plotter4 = Plotter2d((s[0], s[1]/4), (0, 3*s[1]/4, 0, 1), configuration_space=(0, .05, 0, .3), axes_unit=(0.025, 0.025))
        self.plotter4.plot_padding = (1,2,9,18)
        self.plotter4._plot_container.border = (0,23,0,3)
        self.plotter4._plot_container.margin = (12,0,0,9)
        self.plotter4._plot_container.border_color = (0,1,0,0.5)

        self.border = 3 



    def draw(self, window):
        # very basic plot controlling
        dt = time()-self.t
        #self.plotter2.plot_resolution_factor = 0.8+0.5*np.sin(dt)

        check_cs = False
        speed = 0.005
        if 68 in self.window.keyboard.active: #d
            self.plotter.configuration_space += (speed, speed, 0, 0)
        if 65 in self.window.keyboard.active: #a
            self.plotter.configuration_space -= (speed, speed, 0, 0)
        if 87 in self.window.keyboard.active: #w
            self.plotter.configuration_space += (0, 0, speed, speed)
        if 83 in self.window.keyboard.active: #s
            self.plotter.configuration_space -= (0, 0, speed, speed)
        if 32 in self.window.keyboard.active and 340 in self.window.keyboard.active: #s
            check_cs = True
            self.plotter.configuration_space *= (+1.01, 1.01, +01.01, 1.01)
        elif 32 in self.window.keyboard.active: #s
            check_cs = True
            self.plotter.configuration_space *= (+0.99, .99, +0.99, .99)
        if check_cs:
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
        dt = time() - self.t
        self.plotter.tick()
        self.plotter2.tick()
        self.plotter3.tick()
        self.plotter32.tick()
        self.plotter33.tick()
        self.plotter34.tick()
        self.plotter4.tick()
        glClearColor(*self.plotter.background_color.values)
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        self.camera.enable()
        self.plotter.draw()
        self.plotter2.draw()
        self.plotter3.draw()
        self.plotter32.draw()
        self.plotter33.draw()
        self.plotter34.draw()
        self.plotter4.draw()
  
@GLFW_WindowFunction
def main(window):
    texture_controller = Plotter2dBasic(window)







if __name__ == '__main__':
    main()