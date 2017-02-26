""" experimental! """
from gpupy.common.color import hex_to_rgba
from gpupy.gl.common.vector import * 

def parse_4f1_1c4(string):
    split = [s.strip() for s in string.split(' ')]
    if len(split) == 2:
        return tuple(split[0] for i in range(4)), parse_1c4(split[1])
    return (float(split[0]), float(split[1]), float(split[2]), float(split[3])), parse_1c4(split[4])

def parse_4f1(string):
    split = [s.strip() for s in string.split(' ')]
    if len(split) == 1:
        return tuple(split[0] for i in range(4))
    return (float(split[0]), float(split[1]), float(split[2]), float(split[3]))

def parse_2f1(string):
    split = [s.strip() for s in string.split(' ')]
    if len(split) == 1:
        return tuple(split[0] for i in range(2))
    return (float(split[0]), float(split[1]))
    
def parse_1c4(string):
    return hex_to_rgba(string.strip().replace('#', ''))

class Style():
    """ experimental! """
    def __init__(self, description, style=None):
        self._description = {
            k: v if isinstance(v, tuple) else (v, lambda *x: None)
            for k, v in description.items() }
        self._style = {}
        if style is not None:
            self.load(style)
    def load(self, style):
        for k in style:
            self.set(k, style[k])
    def set(self, key, value):
        if key in self._description:
            value = self._description[key][0](value)
        if not key in self._style or self._style[key] != value:
            self._style[key] = value
            self._description[key][1]()
    def get(self, key):
        return self._style[key]
    def __getitem__(self, key): return self.get(key)
    def __setitem__(self, key, value): return self.set(key, value)