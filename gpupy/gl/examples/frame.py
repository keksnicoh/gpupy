#-*- coding: utf-8 -*-
"""
open a single glfw window without any controller

:author: Nicolas 'keksnicoh' Heimann
"""
from gpupy.gl.driver.glfw import GLFW_WindowFunction
from gpupy.gl.components.frame import Frame 
from gpupy.gl.camera import Camera
from gpupy.gl.common import GlViewPort
from gpupy.gl.components.fps import Fps
from OpenGL.GL import *
import numpy as np 
from time import time 
class PrototypeBaseController():
    def __init__(self, window):
        window.on_init.append(self._init)
        window.on_init.append(self.init)
        window.on_cycle.append(self.draw)
        window.on_resize.append(self._resize)
        window.on_resize.append(self.resize)

        self.window = window 

    def _init(self):
        viewport = GlViewPort((0,0), self.window.get_size())
        viewport.use()

        self.viewport = viewport
        camera = Camera(screensize=self.window.get_size())
        self.camera = camera
        self.camera.translate(x=200, y=200, z=-800)
        self.camera.enable()

    def _resize(self):
        ss = self.window.get_size()
        self.camera.set_position((ss[0]*0.5, ss[1]*0.5, -800))
        self.camera.set_screensize(ss)
        self.viewport.size = self.window.get_size()

    def draw(self):
        self.tick()
        self.viewport.use()    
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

        self.scene()
        self.viewport.unuse()

    def scene(self):
        pass 


class Controller(PrototypeBaseController):

    def init(self):
        cap_size = (100, 100)

        inner_camera = Camera(screensize=(self.window.get_size()[0],self.window.get_size()[1]))
        inner_camera.translate(x=200, y=200, z=-800)

        self.frame = Frame(self.window.get_size(), capture_size=cap_size, camera=inner_camera)
        self.fps = Fps(size=200)

        glClearColor(0, 0, 0, 1)

    def resize(self):
        s = self.window.get_size()

        # resize_inner
        self.frame.size = s
        self.frame.camera.set_screensize(s)

        # resize_capture
        self.draw()

    def tick(self):
        self.fps.tick()
        self.frame.use()
        glClearColor(0, 0, 0, 1)
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        self.fps.draw()
        self.frame.unuse()

    def scene(self):
        self.camera.enable()
        self.frame.draw()

@GLFW_WindowFunction
def main(window):
    controller = Controller(window)

if __name__ == '__main__':
    main()


