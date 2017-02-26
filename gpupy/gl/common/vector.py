"""
experimental!

let's see if this is a good idea or not ..
"""
from gpupy.gl.common import Event

import numpy as np 
from functools import partial
from weakref import WeakKeyDictionary

__all__ = ['vec2', 'vec3', 'vec4', 'vecn', 
           'vec2p', 'vec3p', 'vec4p', 
           'Vector']

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
                return self._values[i]

            def fset(self, value): 
                # XXX REmove old values arg
                if self.transformation is not None:
                    values = self.transformation((*self._values[0:i], 
                                                 value, 
                                                 *self._values[i+1:dim]))
                    modified = not np.allclose(self._values[0:dim], values)
                    self._values[0:dim] = values
                else:
                    modified = not np.isclose(self._values[i], value)
                    self._values[i] = value

                modified and self.on_change(self)
            return fget, fset

        # define vec.x, vec.x, etc. 
        for i, field in enumerate(fields):
            setattr(cls, field, property(*__create_fgetset(i, field)))

        # define vec.values
        def fget(self):
            return self._values 

        def fset(self, values):
            if len(values) != len(fields):
                print(fields, self)
                raise ValueError('values must be a iteratable of length {}'.format(len(fields)))
            if self.transformation is not None:
                values = self.transformation(values)
            modified = not np.allclose(self._values[0:dim], values)
            self._values[0:dim] = values
            modified and self.on_change(self)

        setattr(cls, 'values', property(fget, fset))

        # define vec.xy or vec.xyz, ...
        all_attr = ''.join(fields)
        setattr(cls, all_attr, property(fget, fset))
  
        # opengl type conversions.  
        setattr(cls, all_attr + '_gl_float', property(lambda s: s._values.astype(np.float32)))
        setattr(cls, all_attr + '_gl_double', property(lambda s: s._values.astype(np.float64)))
        setattr(cls, all_attr + '_gl_int', property(lambda s: s._values.astype(np.int32)))
        setattr(cls, all_attr + '_gl_uint', property(lambda s: s._values.astype(np.uint32)))


class Vector(metaclass=VectorMeta):
    """
    base vector class
    """
    __p_cls__ = None
    __base_cls__ = None
    def __init__(self):
        self.on_change = Event()
        self.transformation = None

    def observe(self, transformation=lambda x: x):
        """
        creates a new vector which values are given 
        by the *transformation* of the origin vector values.
        the new vector is listening to the original vector's
        on_change event.

        modifications to the values won't affect the original vector.

        any modification of the vector will be overwritten
        when the orignal vector values change; except the event 
        listener is removed from the original vectors on_change
        event queue.
        """
        vector = self.__base_cls__(*transformation(self._values))

        def _listener(subject, *e):
            vector.values = transformation(subject._values)
            
        self.on_change.append(_listener)

        return vector

    def _transform(self, values):
        return values 

    def observe_as_vec2(self, transformation):
        """
        like Vector.observe but creates a two dimensional
        vector by the given *transformation*
        """
        vector = vec2(transformation(self._values))
        
        def _listener(subject, *e):
            vector.values = transformation(subject._values)
            
        self.on_change.append(_listener)

        return vector


    def observe_as_vec3(self, transformation):
        """
        like Vector.observe but creates a three dimensional
        vector by the given *transformation*
        """
        vector = vec3(transformation(self._values))
        
        def _listener(subject, *e):
            vector.values = transformation(subject._values)
            
        self.on_change.append(_listener)

        return vector


    def __deepcopy__(self, *args):
        """
        removes all event handlers
        """
        return self.__p_cls__(self.values.copy())

    def __repr__(self):
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
    def __add__(self, a):  return self.__p_cls__(a + self._values)
    def __radd__(self, a): return self.__p_cls__(self._values + a)
    def __sub__(self, a):  return self.__p_cls__(self._values - a)
    def __rsub__(self, a): return self.__p_cls__(a - self._values)
    def __mul__(self, a):  return self.__p_cls__(self._values * a)
    def __rmul__(self, a): return self.__p_cls__(a * self._values)
    def __div__(self, a):  return self.__p_cls__(self._values / a)
    def __rdiv__(self, a): return self.__p_cls__(a / self._values)

    def __iadd__(self, a):
        self.values = self.values + a
        return self 

    def __isub__(self, a):
        self.values = self.values - a
        return self 

    def __getitem__(self, i):
        return self._values[i]

    def __setitem__(self, i, value):
        if isinstance(i, slice):
            raise NotImplementedError('slices are not supported yet.')
        return setattr(self, self.__fields__[i], value)

    # order relations
    def __eq__(self, a):
        return (self._values == a).all()

    def __ne__(self, a):
        if a is None:
            return True
        return (self._values != a).any()


    def assert_comparable_vector(self, v):
        if len(v) != len(self):
            raise ValueError('value ({}) must be some vector type of length {}'.format(v, len(self)))

    def transform(self):
        if self.transformation is None:
            return 

        old_values = self._values
        values = self.transformation(old_values)
        modified = np.any(self._values[:] != values)
        if modified:
            self._values[:] = values
            self.on_change(self)
            return True
        return False

class Vec2(Vector):
    """
    vector of two components
    """
    __fields__ = ('x', 'y') 
    def __init__(self, x=0, y=0):
        self._values = np.array((x, y), dtype=np.float64)
        super().__init__()

class Vec3(Vector):
    """
    vector of three components
    """
    __fields__ = ('x', 'y', 'z') 
    def __init__(self, x=0, y=0, z=0):
        self._values = np.array((x, y, z), dtype=np.float64)
        super().__init__()

class Vec4(Vector):
    """
    vector of four components
    """
    __fields__ = ('x', 'y', 'z', 'w') 
    def __init__(self, x=0, y=0, z=0, w=0):
        self._values = np.array((x, y, z, w), dtype=np.float64)
        super().__init__()

# -- VecNp allows to assign numpy ndarray directly via constructor.

class Vec2p(Vector):
    __fields__ = ('x', 'y') 
    def __init__(self, ndarray):
        self._values = ndarray
        Vector.__init__(self)

class Vec3p(Vector):
    __fields__ = ('x', 'y', 'z') 
    def __init__(self, ndarray):
        self._values = ndarray
        Vector.__init__(self)

class Vec4p(Vector):
    __fields__ = ('x', 'y', 'z', 'w') 
    def __init__(self, ndarray):
        self._values = ndarray
        Vector.__init__(self)

# fast access of classes
Vec2.__p_cls__ = Vec2p
Vec3.__p_cls__ = Vec3p
Vec4.__p_cls__ = Vec4p
Vec2.__base_cls__ = Vec2
Vec3.__base_cls__ = Vec3
Vec4.__base_cls__ = Vec4

Vec2p.__p_cls__ = Vec2p
Vec3p.__p_cls__ = Vec3p
Vec4p.__p_cls__ = Vec4p
Vec2p.__base_cls__ = Vec2
Vec3p.__base_cls__ = Vec3
Vec4p.__base_cls__ = Vec4


# -- helper methods
def _vecd(veccls, d, obj=None, use_instance=True):
    if obj is None:
        return veccls()

    vector = None
    if use_instance and isinstance(obj, Vector):
        return obj

    if hasattr(obj, '__iter__') and hasattr(obj, '__len__'):
        if len(obj) == d:
            vector = veccls(*obj) 

    if vector is None:
        raise ValueError('argument {} cannot be transformed to a {}-dimensional vector.'.format(obj, d))

    return vector

# -- shotcurts

        
def vecn(obj, use_instance=True):
    """
    transforms any object into a corresponding 
    n-dimensional vector if possible. 

    throws:
      -  ValueError
    """
    vector = None
    if use_instance and isinstance(obj, Vector):
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

def vec2p(data):
    return Vec2p(data)

def vec3p(data):
    return Vec3p(data)

def vec4p(data):
    return Vec4p(data)
