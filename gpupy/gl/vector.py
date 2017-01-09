"""
experimental!

let's see if this is a good idea or not ..
"""
from gpupy.gl.util import Event

import numpy as np 
from functools import partial
from weakref import WeakKeyDictionary

__all__ = ['vec2', 'vec3', 'vec4', 'vecn', 
           'vec2p', 'vec3p', 'vec4p', 
           'Vec2Field', 'Vec3Field', 'Vec4Field']

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
                old_values = tuple(self._values)
                modified = self._values[i] != value
                self._values[i] = value
                modified and self._modified(old_values)
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
            modified = np.any(self._values[0:dim] != values)
            self._values[0:dim] = values
            modified and self._modified(old_values)

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
    base vector class
    """

    def __init__(self):
        self.on_change = Event()
        self.rules = []

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

        def _listener(subject, old):
            vector.values = transformation(subject._values)
            
        self.on_change.append(_listener)

        return vector


    def observe_as_vec2(self, transformation):
        """
        like Vector.observe but creates a two dimensional
        vector by the given *transformation*
        """
        vector = vec2(transformation(self._values))
        
        def _listener(subject, old):
            vector.values = transformation(subject._values)
            
        self.on_change.append(_listener)

        return vector


    def observe_as_vec3(self, transformation):
        """
        like Vector.observe but creates a three dimensional
        vector by the given *transformation*
        """
        vector = vec3(transformation(self._values))
        
        def _listener(subject, old):
            vector.values = transformation(subject._values)
            
        self.on_change.append(_listener)

        return vector


    def __deepcopy__(self, *args):
        """
        removes all event handlers
        """
        return self.__p_cls__(self.values.copy())

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

    def _modified(self, old_values):
        self.on_change(self, old_values)


class Vec2(Vector):
    """
    vector of two components
    """
    __fields__ = ('x', 'y') 
    __p_cls__ = None
    __base_cls__ = None

    def __init__(self, x=0, y=0):
        self._values = np.array((x, y), dtype=np.float64)
        super().__init__()

class Vec3(Vector):
    """
    vector of three components
    """
    __fields__ = ('x', 'y', 'z') 
    __p_cls__ = None
    __base_cls__ = None

    def __init__(self, x=0, y=0, z=0):
        self._values = np.array((x, y, z), dtype=np.float64)
        super().__init__()

class Vec4(Vector):
    """
    vector of four components
    """
    __fields__ = ('x', 'y', 'z', 'w') 
    __p_cls__ = None
    __base_cls__ = None

    def __init__(self, x=0, y=0, z=0, w=0):
        self._values = np.array((x, y, z, w), dtype=np.float64)
        super().__init__()

# -- VecNp allows to assign numpy ndarray directly via constructor.

class Vec2p(Vec2):
    def __init__(self, ndarray):
        self._values = ndarray
        Vector.__init__(self)

class Vec3p(Vec3):
    def __init__(self, ndarray):
        self._values = ndarray
        Vector.__init__(self)

class Vec4p(Vec4):
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

def vec2p(data):
    return Vec2p(data)

def vec3p(data):
    return Vec3p(data)

def vec4p(data):
    return Vec4p(data)

# -- descriptors

class _VecField():
    """
    vector field descriptor 
    """
    def __init__(self, default=None):
        self._val = WeakKeyDictionary()
        self._default = default 
        self._on_change = None
        self._rules = []

    def __get__(self, instance_obj, objtype):
        """
        returns the vector for *instance_obj*.
        if no value set the default value is used
        to instantiate the vector. 
        """
        if not instance_obj in self._val:
            if self._default is None:
                raise RuntimeError('vector values undefined')
            default = self._default
            for rule in self._rules:
                default = rule(instance_obj, default)
            return self._create(instance_obj, default)
        return self._val[instance_obj] 

    def __set__(self, instance_obj, components):
        """
        sets vector *components* for *instance_obj* 
        field. 
        """
        if not instance_obj in self._val:
            return self._create(instance_obj, components)
        else:
            # we only apply rules when the vector is allready
            # created. 
            for rule in self._rules:
                components = rule(instance_obj, components)

            self._val[instance_obj].values = components

    def __delete__(self, instance_obj):
        del self._val[instance_obj]

    def on_change(self, f):
        self._on_change = f
        return f

    def rule(self, rule):
        """
        applies a *rule* to the given vector components
        when they are changed. 
        """
        self._rules.append(rule)

    def _create(self, instance_obj, components):
        self._val[instance_obj] = self.__vec__(components)
        if self._on_change is not None:
            self._val[instance_obj].on_change.append(partial(self._on_change, instance_obj))
        return self._val[instance_obj]

class Vec2Field(_VecField): __vec__ = vec2
class Vec3Field(_VecField): __vec__ = vec3
class Vec4Field(_VecField): __vec__ = vec4

