#-*- coding: utf-8 -*-
"""
Contains several common objects and helper functions
:author: Nicolas 'keksnicoh' Heimann
"""
from OpenGL.GL import *
from gpupy.gl import GPUPY_GL
import numpy as np
from functools import partial
from scipy.ndimage import imread as sc_imread

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

    def once(self, callback, no_args=False):
        def _delete_wrapper(*args, **kwargs):
            callback(*args, **kwargs)
            self.remove(_delete_wrapper)
        self.append(_delete_wrapper)

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

def imread(name, flatten=False, mode=None, normalize=255.0, dtype=np.float32):
    txt = sc_imread(name, flatten=flatten, mode=mode).astype(dtype)
    txt = txt.reshape((txt.shape[1], txt.shape[0], txt.shape[2]))
    return txt / normalize