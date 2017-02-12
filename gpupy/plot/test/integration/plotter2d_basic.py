#-*- coding: utf-8 -*-
"""
using texture utilities to create a random texture which
is regenerated each rendering cycle.

:author: Nicolas 'keksnicoh' Heimann
"""

from gpupy.plot.plotter2d import Plotter2d
from OpenGL.GL import *
from gpupy.gl.vector import *
import numpy as np
from gpupy.gl.components.camera import Camera2D
from gpupy.gl.driver.glfw import GLFW_WindowFunction
from time import time

from gpupy.gl.components.fps import Fps



class Plotter2dBasic():
    def __init__(self, window):
        self.window = window
        window.on_init.append(self.init)
        window.on_cycle.append(self.draw)
        window.on_resize.append(self.resize)

        self.t = time()

    def resize(self):

        self.plotter.size = self.window.get_size()
        self.camera.screensize = self.window.get_size()
        self.draw()
    def init(self):
        size = vec2(self.window.get_size())
        self.camera = Camera2D(screensize=size, position=size.observe_as_vec3(lambda v: (v[0]/2, v[1]/2, 0)))
        self.plotter = Plotter2d(self.window.get_size())
        self.border = 3 


    def draw(self):

        dt = time() - self.t
       # self.plotter._plot_container.border = (int(dt*30) % 45, int(dt*30) % 45, 50*(0.5+0.5*np.sin(int(dt*30)*0.1)), 3)
       # self.plotter.size.x = self.window.get_size()[0] * 1*(0.75+0.25*np.sin(int(dt*30)*0.1))
       # self.plotter.size.y = self.window.get_size()[1] * 1*(0.75+0.25*np.sin(int(dt*30)*0.1+1))
       # self.plotter.configuration_space = (0.2*dt, 1+0.2*dt, 0, 1)
        self.plotter.tick()
        self.camera.enable()
        self.plotter.draw()
  
@GLFW_WindowFunction
def main(window):
    texture_controller = Plotter2dBasic(window)







if __name__ == '__main__':
    main()