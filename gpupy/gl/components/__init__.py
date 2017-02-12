from gpupy.gl.common import Event 
from gpupy.gl.common.attributes import ObservablesAccessor
from weakref import WeakKeyDictionary

from functools import partial 
"""
It is possible to have a widget which has components and widgets. 
problems:
    how to observe parent properties?
    1) it is not allowed for child components to know anyhting about there parents
    2) it is allowed for child components to know stuff about there parents but 
       not react on changes.
    3) child components bind parents ?!
"""
class Component():
    """
    A component is any object with a tick method. 
    The tick method implements logic of the component which should
    be executed within an application tick. 

    if the component has a components attribute it is an node (parent component).

    Events
        on_pre_tick 
        on_post_tick 
    """
    def __init__(self):
        self.on_pre_tick = Event()
        self.on_post_tick = Event()
        self._ = ObservablesAccessor(self)
        
    def tick(self):
        self.on_pre_tick()
        self._tick()
        self.on_post_tick()
