#-*- coding: utf-8 -*-
"""
open a single glfw window without any controller

:author: Nicolas 'keksnicoh' Heimann
"""
from gpupy.gl.components.widgets.frame import FrameWidget 
from gpupy.gl.components.fps import Fps

from gpupy.gl.glfw import GLFW_window
from gpupy.gl import *
from gpupy.gl.components.camera import Camera2D
from gpupy.gl.lib.matrix import *
from gpupy.gl.lib.vector import *
from OpenGL.GL import *


import numpy as np 
from time import time 

class PrototypeBaseController():
    def __init__(self, window):
        window.on_ready.append(self._init)
        window.on_ready.append(self.init)
        window.on_cycle.append(self.draw)
        window.on_resize.append(self._resize)
        window.on_resize.append(self.resize)

        self.window = window 

    def _init(self, window):
        viewport = Viewport((0,0), self.window.size)

        self.viewport = viewport
        camera = Camera2D(screensize=self.window.size)
        self.camera = camera
        #self.camera.translate(x=200, y=200, z=-800)
        self.camera.enable()

    def _resize(self, window):
        ss = self.window.size
        self.camera.set_position((ss[0]*0.5, ss[1]*0.5, -800))
        self.camera.set_screensize(ss)
        self.viewport.size = self.window.size

    def draw(self, window):
        self.tick()
        self.viewport.use((0, 0), window.size.xy_gl_int)    
        self.scene()
        self.viewport.unuse()

    def scene(self):
        pass 


class Controller(PrototypeBaseController):

    def init(self, window):
        
        self.fps = Fps(size=100)

        # 200px height, scales with window size
        cap_size = (self.window.size[0]*0.8, 200)

        # create a frame with a capture size vector
        # this way the size, resolution and screensize of the camera are
        # all bound by the same vector. 
        #
        # since the components listen to changes of the vector
        # they'll automatically update if the size changes.
        linked_cap_size = vec2(cap_size)
        #, camera=Camera2D(screensize=linked_cap_size, position=(200, 100, 0))
        self.frame_dynamic = FrameWidget(linked_cap_size)

        # in this example the capture size wont be connected to the camera's
        # screensize.
        #, camera=Camera2D(screensize=cap_size, position=(200, 100, 0))
        self.frame_static = FrameWidget(cap_size)
        self.mat_static = mat4_translation(180, 180, 0).T
        self.frame_static.program.uniform('mat_model', self.mat_static)

        # here the camera screensize is connected to the 
        # framebuffers size and capture size is connected to 
        # size such that the x=size.x*0.25 and y=size.y*4
        size = vec2(cap_size)
        #, camera=Camera2D(screensize=size, position=(200, 100, 0))
        self.frame_bad_resolution = FrameWidget(size, 
                                                resulution=size.observe(lambda x: x*(0.25, 4)))
        self.mat_bad_resolution = mat4_translation(0, -400, 0).T
        self.frame_bad_resolution.program.uniform('mat_model', self.mat_bad_resolution)

        glClearColor(0, 0, 0, 1)

    def resize(self):
        """
        we will resize the dynamic and the bad_resolution  frame.
        for the dynamic frame we change the camera's position to
        such that the content won't move on resize
        """
        s = self.window.size

        self.frame_dynamic.size = (s[0], 200)
        self.frame_dynamic.camera.position = ((self.frame_dynamic.size[0]/2, 100, 0))

        self.frame_bad_resolution.size = (s[0], 200)

        self.draw()

    def tick(self):
        self.fps.tick()
  #      self.frame_dynamic.use()
  #      glClearColor(0, 0, 0, 1)
  #      glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
  #      self.fps.draw()
  #      self.frame_dynamic.unuse()

        self.frame_static.use()
        glClearColor(0, 0, 0, 1)
        self.fps.draw()
        self.frame_static.unuse()

     #   self.frame_bad_resolution.use()
     #   glClearColor(0, 0, 0, 1)
     #   glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
     ##   self.fps.draw()
      #  self.frame_bad_resolution.unuse()

    def scene(self):
        self.camera.enable()
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

        self.frame_static.draw()
     #   self.frame_dynamic.draw()
     #   self.frame_bad_resolution.draw()


@GLFW_window
def main(window):
    controller = Controller(window)

if __name__ == '__main__':
    main()


