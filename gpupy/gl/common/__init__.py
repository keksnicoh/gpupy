#-*- coding: utf-8 -*-
"""
Contains several common objects and helper functions
:author: Nicolas 'keksnicoh' Heimann
"""
from OpenGL.GL import *
from gpupy.gl import GPUPY_GL
import numpy as np
from functools import partial

class Event(list):
    """
    An event is a list of callbacks which are invoked
    if the event was invoked.

        my_event = Event()
        my_event.append(blurp)
        my_event >> another_callback # the same as .append(another_callback)     ????? Good idea ????? look cool anyway..
        my_event('first arg', 'and so on...')

    """
    OVERFLOW = 163

    def __call__(self, *args, **kwargs):
        """ invokes listeners l with arguments l(*args, **kwargs)"""
        try:
            for l in self:
                l(*args, **kwargs)
        except TypeError:
            raise TypeError(l)

    def append(self, callback):
        if len(self) > Event.OVERFLOW:
            raise OverflowError()
        super().append(callback)

class CommandQueue(list):
    """
    simple command queue structure.
    usage:

      q = CommandQueue()
      q.push(a_command)
      q.push(a_nother_command)
      q()

    """
    def __call__(self):
        """
        invokes the whole queue
        """
        for c in self: c[0](*c[1], **c[2])
        del self[:]

    def queue(self, command):
        """
        returns an callback which will push
        the given command with arguments into queue
        :param command: callback
        """
        return partial(self.push, command)

    def push(self, command, *args, **kwargs):
        """
        pushed a command with args into the queue
        """
        self.append((command, args, kwargs))

# some short hand type helpers
def glbool(v): return GL_TRUE if v else GL_FALSE
def glfloat(v): return np.float32(v)
def glint(v): return int(v)



class GlDriver():
    """ represents OpenGL driver profile """
    def __init__(self, version, core_profile=True, forward_compat=True):
        """ initialized glDriver
            :argument version: tuple or a string
            :core_profile: whether core profile should be used
            :forward_compat: see specifications."""
        if type(version) is str:
            prt = version.split('.')
            if len(prt) > 2:
                raise ValueError('Argument version must by either tuple or a string. version examples: "4", "4.0", "3.1"')

            version = (int(prt[0]), 0) if len(prt) == 1 else (int(prt[0]), int(prt[1]))

        self.version = version
        self.core_profile = bool(core_profile)
        self.forward_compat = bool(forward_compat)
    
    def get_gl_information():
        return {
            'GL_MAX_UNIFORM_BUFFER_BINDINGS': glGetIntegerv(GL_MAX_UNIFORM_BUFFER_BINDINGS),
            'GL_MAX_TEXTURE_IMAGE_UNITS': glGetIntegerv(GL_MAX_TEXTURE_IMAGE_UNITS),
        }




