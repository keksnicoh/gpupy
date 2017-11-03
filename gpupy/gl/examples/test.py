
from gpupy.gl.lib import Event

import numpy as np 
from functools import partial



__all__ = ['vec2', 'vec3', 'vec4', 'watchable']


class VectorMeta(type): 
    """
    metaclass that spawns the vector attributes
    and multiple attribute setters and getters

    e.g. __fields__ = ('x', 'y')

    the class will have x and y attribute
    """
    def __init__(cls, name, bases, namespace):

        fields = namespace['__fields__'] if '__fields__' in namespace else () 

        for i, field in enumerate(fields):
            def fget(self): 
                return self.values[i]

            def fset(self, value): 
                old_values = tuple(self._values)
                self.values[i] = value
                self._modified(old_values)

            setattr(cls, field, property(fget, fset))

        def fget(self):
            return self._values 

        def fset(self, values):
            if len(values) != len(fields):
                raise ValueError('values must be a iteratable of length {}'.format(len(fields)))
            old_values = tuple(self._values)
            self._values = np.array(values, dtype=np.float64)
            self._modified(old_values)

        setattr(cls, 'values', property(fget, fset))

        all_attr = ''.join(fields)
        setattr(cls, all_attr, property(fget, fset))
    
        setattr(cls, all_attr + '_gl_float', property(lambda s: s._values.astype(np.float32)))
        setattr(cls, all_attr + '_gl_int', property(lambda s: s._values.astype(np.int32)))
        setattr(cls, all_attr + '_gl_uint', property(lambda s: s._values.astype(np.uint32)))

        super().__init__(name, bases, namespace)


def vecn(obj):
    vector = None
    if isinstance(obj, Vector):
        vector = obj

    if hasattr(obj, '__iter__') and hasattr(obj, '__len__'):
        if len(obj) == 2:
            vector = Vec2(*obj)
        elif len(obj) == 3:
            vector = Vec3(*obj)
        elif len(obj) == 4:
            vector = Vec4(*obj)

    if vector is None:
        raise ValueError('argument {} cannot be transformed to a vector.'.format(obj))

    return vector


class Vector(metaclass=VectorMeta):
    
    def __str__(self):
        return '{}({})'.format(str(self.__class__.__name__), ', '.join(str(a) for a in self))

    def __iter__(self):
        return iter(self.values)

    def __len__(self):
        return len(self.__fields__)

    def __radd__(self, a):
        new = self.__class__(*(self._values + a))
        return new

    def __add__(self, a):
        return self.__radd__(a)

    def __sub__(self, a):
        new = self.__class__(*(self._values -a))
        return new

    def __rsub__(self, a):
        new = self.__class__(*(a - self._values))
        return new

    def __iadd__(self, a):
        self.assert_comparable_vector(a)
        self.values = self.values + a
        return self 

    def __isub__(self, a):
        self.assert_comparable_vector(a)
        self.values = self.values - a
        return self 

    def __getitem__(self, i):
        return self._values[i]

    def __setitem__(self, i, value):
        return setattr(self, self.__fields__[i], value)

    def assert_comparable_vector(self, v):
        if len(v) != len(self):
            raise ValueError('value ({}) must be some vector type of length {}'.format(v, len(self)))

    def _modified(self, old_values):
        pass

    def __init__(self):
        self._values = ()

class Vec2(Vector):
    __fields__ = ('x', 'y') 

    def __init__(self, x=0, y=0):
        super().__init__()
        self.values = (x, y)

class Vec3(Vector):
    __fields__ = ('x', 'y', 'z') 

    def __init__(self, x=0, y=0, z=0):
        super().__init__()
        self.values = (x, y, z)

class Vec4(Vector):
    __fields__ = ('x', 'y', 'z', 'w') 

    def __init__(self, x=0, y=0, z=0, w=0):
        super().__init__()
        self.values = (x, y, z, w)

def _vecd(veccls, d, obj=None):
    if obj is None:
        return veccls()

    vector = None
    if isinstance(obj, Vector):
        vector = obj

    if hasattr(obj, '__iter__') and hasattr(obj, '__len__'):
        if len(obj) == d:
            vector = veccls(*obj)

    if vector is None:
        raise ValueError('argument {} cannot be transformed to a {}-dimensional vector.'.format(obj, d))

vec2 = partial(_vecd, Vec2, 2) 
vec3 = partial(_vecd, Vec3, 3) 
vec4 = partial(_vecd, Vec4, 4) 

class WatchableFactory():
    def __rmatmul__(self, obj):
        vector = vecn(obj)

        # if the vector isn't allready watchable
        if not hasattr(vector, 'on_change'):
            setattr(vector, 'on_change', Event())

            old_modified = vector._modified
            def modified(old_value):
                old_modified(old_value)
                vector.on_change(vector, old_value)
            setattr(vector, '_modified', modified)

        return vector

watchable = WatchableFactory()

