
from gpupy.gl.vector import *
from collections import OrderedDict
from gpupy.gl.common import Event
import numpy as np 

class ObservableOrderedDict(OrderedDict):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.on_change = Event()
    def __setitem__(self, key, value):
        super().__setitem__(key, value)
        self.on_change(self, key)

class AbstractLayout():
    """
    

    NOTE
    ----
    be carefull with lazyness:

    just watching event listeners can result in huge
    overhead. If some properties a updated quiet often
    within the tick of a component, many operations are
    maybe done redundant, since only the last state
    is of intrest in most cases. On long term try to
    buffer the events during tick and release the buffer
    on pre render, if possible.

    .. code ::

        layout.buffer_events()

        # do a lot of cool stuff

        layout.fire_buffered_events()
        layout.buffer_events(False)

    """
    def __init__(self, size, position=(0,0)):

        # scope layout scope.
        self._scope = ObservableOrderedDict()

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
        self._data = np.zeros((self._max_box_index +1, 5), dtype=np.float64)

        # if events should be buffered.
        self._buffer_events = False 

    @property
    def scope(self):
        return self._scope
    
    @scope.setter
    def scope(self, values):
        self._scope.update(values)

    def create_box(self, name, transformations, scope=()):
        """
        creates a box 
        """
        index = len(self.boxes)
        if index > self._max_box_index:
            raise OverflowError('box overflow')

        self.boxes[name] = Box(self._data[index], transformations, scope)

        # listen to scope changes.
        def scope_watcher(scope, field):
            if field in self.boxes[name].scope:
                self.calculate()
                self.calculate_box(self.boxes[name])

        self.scope.on_change.append(scope_watcher)

        return self.boxes[name]

    def buffer_events(self, flag=True):
        """
        if the all vector events should be buffered. 

        use BoxLayout.fire_buffered_events() method
        to fire buffered events.

        Argumrnts:
          - flag: bool
        """ 
        self._buffer_events = flag
        self._old_data = self._data.copy()

    def fire_buffered_events(self):
        """
        fires buffered events 
        """
        diff = self._old_data - self._data
        pass 

    def calculate(self, force_events=False):
        """
        perform layout calculations
        """
        for i, (bid, box) in enumerate(self.boxes.items()):
            old_values = self._data[i].copy() # copy old data

            transformed = box.transformations(self)
            self._data[i][0], \
            self._data[i][1] = self.position.x + transformed[3], \
                               self.position.y + transformed[0]
            self._data[i][3], \
            self._data[i][4] = self.position.x + transformed[1] - self._data[i][0], \
                               self.position.y + transformed[2] - self._data[i][1] 

            if not self._buffer_events:
                # position event
                if force_events or not np.array_equal(old_values[0:3], self._data[i][0:3]):
                    box.position.on_change(box.position, old_values[0])

                # size event
                if force_events or not np.array_equal(old_values[3:5], self._data[i][3:5]):
                    box.size.on_change(box.size, old_values[1])

                # all-data event
                if np.array_equal(self._data[i], old_values): 
                    box.data.on_change(self._data, old_values)

class ContainerLayout(AbstractLayout):

    pass


class Box():
    def __init__(self, data, transformations, scope=()):
        self.transformations = transformations
        self.scope = scope
        self.position = vec3p(data[0:3])
        self.size = vec2p(data[3:5])
        self.data = vec4p(data)


class Container():
    def __init__(self, data, transformations, scope=()):
        self.transformations = transformations
        self.scope = scope
        self.position = vec3p(data[0:3])
        self.size = vec2p(data[3:5])
        self.data = vec4p(data)





