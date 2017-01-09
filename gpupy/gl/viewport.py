#-*- coding: utf-8 -*-
"""
viewport 

:author: Nicolas 'keksnicoh' Heimann
"""
from OpenGL.GL import *
from gpupy.gl.vector import * 

class ViewPort():
    #size = Vec2Property()
    #position = Vec2Property()



    def __init__(self, position, size, restore=True):
        self._position = vec2(position)
        self._size = vec2(size)
        self._old_viewport = None
        self.restore = restore

    @classmethod
    def create(cls):
        vp = glGetIntegerv(GL_VIEWPORT)
        return cls(vp[0:2], vp[2:4])

    @property
    def size(self):
        return self._size 

    @size.setter
    def size(self, value):
        self._size.xy = value

    @property
    def position(self):
        return self._position 

    def use(self):
        self._old_viewport = glGetIntegerv(GL_VIEWPORT)
        glViewport(*self._position.xy_gl_int, *self._size.xy_gl_int)

    def unuse(self, restore=None):
       # if restore is None and self.restore or restore is not None and restore:
       #     oerk()
       #     return

        if self._old_viewport is not None:
            glViewport(*self._old_viewport)