# RUBBISH 
from gpupy.gl.lib.vector import *
from collections import OrderedDict
from gpupy.gl.components.widgets import Widget
from gpupy.gl.lib import Event
import numpy as np 
from functools import partial 
class ObservableOrderedDict(OrderedDict):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.on_change = Event()
    def __setitem__(self, key, value):
        super().__setitem__(key, value)
        self.on_change(self, key)

class ObservableDict(dict):
    def __init__(self, *args, **kwargs):
        self.on_setitem = Event 

    def __setitem__(self, key, value):
        super().__setitem__(key, value)
        self.on_setitem(key, value)

class ContainerLayout(Widget):
    """
    

    """
    DTYPE = np.dtype([
        ('size', np.float32, 2),
        ('_csize', np.float32, 2),
        ('position', np.float32, 4),
        ('_cposition', np.float32, 4),
        ('margin', np.float32, 4),
    ])
    size = Vec2Field()
    
    def __init__(self, size, position=(0,0,0,1)):
        super().__init__()
        self.widgets = []

        # main outsite configuration
        self.position = vec2(position)
        self.size = vec2(size)

        # layout boxes. note that it is an ordered dict
        # since we need to identify a box with a vector
        # in the _data attribute.
        self.boxes = OrderedDict()

        # layout data. all box vectors are pointers
        # on vectors inside this array.
        self._max_box_index = 499
        self._data = np.zeros(self._max_box_index +1, dtype=self.DTYPE)

        # if events should be buffered.
        self._buffer_events = False 
        self._calculated = False

    def append(self, widget, size=None, position=(0, 0, 0, 1), margin=(0, 0, 0, 0)):
        if size is None: 
            size = self.size
        self._data[len(self.widgets)] = (size, (0, 0), position, (0, 0, 0, 1), margin)
        self.widgets.append(widget)

 

    def container_changed(self, container, field, value):
        print(e)
        container.data[field] = value
       # self._data[0:len(self.widgets)+1] = e[0]
       # print(self._data[0:len(self.widgets)+1])
        self._calculated = False

    def _tick(self):
        if not self._calculated:
            self.calculate()
            self._calculated = True

    def _render(self):
        for box in self.widgets:
            box.render()

    def calculate(self, force_events=False):
        """
        perform layout calculations
        """
        return
        for box in self.widgets:
            box.layout()
