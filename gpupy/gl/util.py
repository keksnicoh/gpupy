#-*- coding: utf-8 -*-
"""
library utilities
:author: Nicolas 'keksnicoh' Heimann
"""

from functools import partial
import numpy

signal = lambda ssx, *args, **kwargs: lambda *x, **y: ssx(*args, **kwargs)

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

class Event(list):
    """
    event listener stack

    my_event = Event()
    my_event.append(blurp)
    my_event.append(blurp2)
    my_event('first arg', 'and so on...')

    """
    def __call__(self, *args, **kwargs):
        """
        invokes all listeners with given arguments
        """
        for l in self:
            l(*args, **kwargs)

