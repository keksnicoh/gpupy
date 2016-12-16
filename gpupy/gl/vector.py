from gpupy.gl.util import Event 

__all__ = ['vec2', 'vec3', 'vec4', 'listenable']

def vec2(x=None, y=None):
    if isinstance(x, Vec2):
        assert y == None
        return x
    if hasattr(x, '__iter__'):
        assert y == None
        x, y = x[0], x[1]

    return Vec2(x or 0, y or 0)

def vec3(x=None, y=None, z=None):
    if (isinstance(x, Vec3)):
        assert y == None and z == None
        return x
    return Vec2(x or 0, y or 0, z or 0)

def vec4(x=None, y=None, z=None, w=None):
    if (isinstance(x, Vec4)):
        assert y == None and z == None and w == None
        return x
    return Vec2(x or 0, y or 0, z or 0, w or 0)

def listenable(vec):
    if isinstance(vec, ListenableVector):
        return vec

    return ListenableVector(vec)

class Vec2():
    _ALLOWED_ATTRIBUTES = ('x', 'y')

    def __init__(self, x, y):
        self._v = (x, y)
        self.x = x 
        self.y = y 

    def __getitem__(self, i): 
        return getattr(self, Vec4._ALLOWED_ATTRIBUTES[i])

    @property
    def xy(self):
        return self.x, self.y

    @xy.setter
    def xy(self, xy):
        self.x, self.y = xy

    def __iter__(self):
        yield self.x 
        yield self.y

    def __str__(self):
        return 'vec2({})'.format(', '.join('{:.2f}'.format(f) for f in self))

class Vec3():
    _ALLOWED_ATTRIBUTES = ('x', 'y', 'z')

    def __init__(self, x=0, y=0, z=0):
        self.x = x 
        self.y = y 
        self.z = z 

    def __getitem__(self, i): 
        return getattr(self, Vec4._ALLOWED_ATTRIBUTES[i])

    @property
    def xyz(self):
        return self.x, self.y, self.z

    @xyz.setter
    def xyz(self, xyz):
        self.x, self.y, self.z = xyz

    def __iter__(self):
        yield self.x 
        yield self.y
        yield self.z

class Vec4():
    _ALLOWED_ATTRIBUTES = ('x', 'y', 'z', 'w')

    def __init__(self, x, y, z, w):

        self.x = x 
        self.y = y 
        self.z = z 
        self.w = w 

    def __getitem__(self, i): 
        return getattr(self, Vec4._ALLOWED_ATTRIBUTES[i])

    @property
    def xyzw(self):
        return self.x, self.y, self.z, self.w

    @xyzw.setter
    def xyzw(self, xyzw):
        self.x, self.y, self.z, self.w = xyzw

    def __iter__(self):
        yield self.x 
        yield self.y
        yield self.z 
        yield self.w

class ListenableVector():
    """
    wraps a object around a vector which provides
    an on_change event 
    """
    PASSTHRU = (
        'xy', 'xyz', 'xyzw'
    )
    def __init__(self, vec):
        self.vec = vec

        # args: old_values, new_values
        self.on_change = Event()

    def __getattribute__(self, name):
        if name in ListenableVector.PASSTHRU:
            return getattr(self.vec, name)
        if name == 'vec' or name not in self.vec._ALLOWED_ATTRIBUTES:
            return super().__getattribute__(name)

        return getattr(self.vec, name)

    def __setattr__(self, name, value):
        if name in ListenableVector.PASSTHRU:
            old_values = tuple(self.vec)
            result = setattr(self.vec, name, value)
            self.on_change(tuple(self.vec), old_values)
            return result

        if name == 'vec' or name not in self.vec._ALLOWED_ATTRIBUTES:
            return super().__setattr__(name, value)

        old_values = tuple(self.vec)
        setattr(self.vec, name, value)

        self.on_change(self.vec, old_values)

    def __iter__(self):
        return self.vec.__iter__()

    def __getitem__(self, i):
        return self.vec[i]

    def __str__(self):
        return 'listenable {}'.format(self.vec)


class WatchableFactory():
    def __rmatmul__(self, x):
        print(x)
        return vec2(*x)
    def __matmul__(self, x):
        raise Exception('this is not allowed')
watchable = WatchableFactory()
print((2,2) @ watchable)
