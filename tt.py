class Descriptor():
    def __get__(self, instance_obj, objtype):

        raise Exception('avoid this')
    def decorate(self, f):
        print('decorate', f)
        return f

class A():
    my_attr = Descriptor()

class B():
    _A_my_attr = vars(A)['my_attr']
    @_A_my_attr.decorate
    def foo(self):
        print('hey, whatsup?')