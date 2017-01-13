class A():
    def __init__(self):
        self._t = None
        self._g = None
        self._d = {}
    def get_linear_transformation(self):
        return self._t
    def get_glsl_transformation(self):
        return self._g
    def linear_transformation(self, f):
        self._t = f(self) if hasattr(f, '__call__') else f
        return f

    def glsl_transformation(self, f):
        self._g = f(self)
        return f

    def declare(self, name, value=None):
        if hasattr(value, '__call__'):
            self._d[name] = value()
        if value is None:
            def _d(f):
                print('domain', name, f)
                self._d[name] = f()
            return _d
        print('FOO')

a = A()

@a.declare('x')
def load_funny_data():
    return 'FOO' #VBO CREATED !!! !!! !!!

@a.linear_transformation('data[0]')
def foo(a):
    print('OERK')
    return ('FOO', a)

@a.glsl_transformation
def foo(a):
    return "$y = $x * $x"


@a.declare('data'):
def load_cool_data():
    return "2-dim-domain"

print(a._d['x'])
print(a.get_linear_transformation())
print(a.get_linear_transformation())
print(foo(a))

print(a.get_glsl_transformation())