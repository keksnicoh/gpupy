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
#        self.plotter.borders(3, int(dt) % 15, 3, 3)

        self.plotter.tick()

        self.camera.enable()
        self.plotter.draw()
@GLFW_WindowFunction
def main(window):
    texture_controller = Plotter2dBasic(window)

if __name__ == '__main__':
    main()