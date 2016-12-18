"""
experimental!

let's see if this is a good idea or not ..
"""
from gpupy.gl.util import Event

import numpy as np 
from functools import partial

__all__ = ['vec2', 'vec3', 'vec4', 'vecn']

class VectorMeta(type): 
    """
    metaclass that spawns the vector attributes
    and multiple attribute setters and getters

    e.g. __fields__ = ('x', 'y')

    the class will have x and y attribute
    """
    def __init__(cls, name, bases, namespace):
        super().__init__(name, bases, namespace)
        fields = namespace['__fields__'] if '__fields__' in namespace else () 
        dim = len(fields)

        def __create_fgetset(i, field):
            def fget(self): 
                return self.values[i]

            def fset(self, value): 
                old_values = tuple(self._values)
                self.values[i] = value
                self._modified(old_values)
            return fget, fset

        # define vec.x, vec.x, etc. 
        for i, field in enumerate(fields):
            setattr(cls, field, property(*__create_fgetset(i, field)))

        # define vec.values
        def fget(self):
            return self._values 

        def fset(self, values):
            if len(values) != len(fields):
                raise ValueError('values must be a iteratable of length {}'.format(len(fields)))
            old_values = tuple(self._values)
            self._values[0:dim] = values
            self._modified(old_values)

        setattr(cls, 'values', property(fget, fset))

        # define vec.xy or vec.xyz, ...
        all_attr = ''.join(fields)
        setattr(cls, all_attr, property(fget, fset))
  
        # opengl type conversions.  
        setattr(cls, all_attr + '_gl_float', property(lambda s: s._values.astype(np.float32)))
        setattr(cls, all_attr + '_gl_int', property(lambda s: s._values.astype(np.int32)))
        setattr(cls, all_attr + '_gl_uint', property(lambda s: s._values.astype(np.uint32)))


class Vector(metaclass=VectorMeta):
    """
    base vector class implements all operator 
    overloading
    """

    def __init__(self):
        self.on_change = Event()

    def observe(self, transformation=lambda x: x):
        """
        creates a new vector which observes
        this vector. 

        Arguments:
        - transformation: a callable which defines a 
            transformation of the value. 

        the new vector does listen to the
        original vector on_change event. 
        modify the state of the vector will
        not affect the original vector change.
        """
        vector = self.__base_cls__(*self._values)

        def _listener(subject, old):
            vector.values = transformation(subject._values)
            
        self.on_change.append(_listener)

        return vector

    def __deepcopy__(self, *args):
        """
        removes all event handlers
        """
        return self.__ndarray_cls__(self.values.copy())

    def __str__(self):
        """
        string representation

           VecN(x, y, ...)

        """
        return '{}({})'.format(str(self.__class__.__name__), ', '.join(str(a) for a in self))

    def __unicode__(self):
        return self.__str__()

    def __iter__(self):
        return iter(self.values)

    def __len__(self): 
        return len(self.__fields__)

    # numpy wrappers
    # XXX
    # - define missing 
    def __add__(self, a):  return self.__ndarray_cls__(a + self._values)
    def __radd__(self, a): return self.__ndarray_cls__(self._values + a)
    def __sub__(self, a):  return self.__ndarray_cls__(self._values - a)
    def __rsub__(self, a): return self.__ndarray_cls__(a - self._values)
    def __mul__(self, a):  return self.__ndarray_cls__(self._values * a)
    def __rmul__(self, a): return self.__ndarray_cls__(a * self._values)
    def __div__(self, a):  return self.__ndarray_cls__(self._values / a)
    def __rdiv__(self, a): return self.__ndarray_cls__(a / self._values)

    def __iadd__(self, a):
        self.values = self.values + a
        return self 

    def __isub__(self, a):
        self.values = self.values - a
        return self 

    def __getitem__(self, i):
        return self._values[i]

    def __setitem__(self, i, value):
        return setattr(self, self.__fields__[i], value)

    # order relations
    def __eq__(self, a):
        return (self._values == a).all()

    def __ne__(self, a):
        return (self._values != a).any()

    def assert_comparable_vector(self, v):
        if len(v) != len(self):
            raise ValueError('value ({}) must be some vector type of length {}'.format(v, len(self)))

    def _modified(self, old_values):
        self.on_change(self, old_values)


class Vec2(Vector):
    """
    vector of two components
    """
    __fields__ = ('x', 'y') 
    __ndarray_cls__ = None
    __base_cls__ = None

    def __init__(self, x=0, y=0):
        self._values = np.array((x, y), dtype=np.float64)
        super().__init__()

class Vec3(Vector):
    """
    vector of three components
    """
    __fields__ = ('x', 'y', 'z') 
    __ndarray_cls__ = None
    __base_cls__ = None

    def __init__(self, x=0, y=0, z=0):
        self._values = np.array((x, y, z), dtype=np.float64)
        super().__init__()

class Vec4(Vector):
    """
    vector of four components
    """
    __fields__ = ('x', 'y', 'z', 'w') 
    __ndarray_cls__ = None
    __base_cls__ = None

    def __init__(self, x=0, y=0, z=0, w=0):
        self._values = np.array((x, y, z, w), dtype=np.float64)
        super().__init__()

# -- VecNndarray allows to assign numpy ndarray directly via constructor.
#    that way we can use the ndarray from arithmethic operations 
#    defined in Vector.__XXX__ methods directly as the new vector.
class Vec2ndarray(Vec2):
    def __init__(self, ndarray):
        self._values = ndarray
        Vector.__init__(self)

class Vec3ndarray(Vec3):
    def __init__(self, ndarray):
        self._values = ndarray
        super(Vector, self).__init__()

class Vec4ndarray(Vec4):
    def __init__(self, ndarray):
        self._values = ndarray
        super(Vector, self).__init__()

# fast access of classes
Vec2.__ndarray_cls__ = Vec2ndarray
Vec3.__ndarray_cls__ = Vec3ndarray
Vec4.__ndarray_cls__ = Vec4ndarray
Vec2.__base_cls__ = Vec2
Vec3.__base_cls__ = Vec3
Vec4.__base_cls__ = Vec4

# -- helper methods
def _vecd(veccls, d, obj=None):
    if obj is None:
        return veccls()

    vector = None
    if isinstance(obj, Vector):
        return obj

    if hasattr(obj, '__iter__') and hasattr(obj, '__len__'):
        if len(obj) == d:
            vector = veccls(*obj) 

    if vector is None:
        raise ValueError('argument {} cannot be transformed to a {}-dimensional vector.'.format(obj, d))

    return vector

# -- shotcurts

        
def vecn(obj):
    """
    transforms any object into a corresponding 
    n-dimensional vector if possible. 

    throws:
      -  ValueError
    """
    vector = None
    if isinstance(obj, Vector):
        return obj

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

vec2 = partial(_vecd, Vec2, 2)
vec3 = partial(_vecd, Vec3, 3) 
vec4 = partial(_vecd, Vec4, 4) 

