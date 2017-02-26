#-*- coding: utf-8 -*-
"""
descriptor library.

:author: keksnicoh
"""

from gpupy.gl.common.observables import *
from gpupy.gl.common.vector import vecn
from gpupy.gl.common import Event 
from gpupy.gl import BufferObject

from weakref import WeakKeyDictionary
from functools import partial 
__all__ = [ 'Attribute', 'CastedAttrbiute', 'ComputedAttribute', 'VectorAttribute']


class Attribute():
    """
    an attribute is a property with additional features:

    - observer pattern:
      Any attribute has an on_change Event which allows to 
      listen for changes.
    - transformation:
      The value assigned to the attribute will be transformed
      by a given transformation if there is a transformation defined.

    ```python
    class A():
        dorp = Attribute(default=4)
        @dorp.on_change
        def something_happend(self, value):
            print('new value of dorp: {}'.format(value))
        @dorp.transformation
        def the_cool_transformation(self, value):
            return value * 2

        a = A()
        a.dorp = 2
        # new value of dorp: 4
    ```

    If one assigns an observable to the attribute, the attribute
    starts watching the observables for changes. If observation is
    active, setting an attribute value explicitly will raise a
    RuntimeError. Therefore one should never modify Attributes directly
    from inside the class. 

    """
    def __init__(self, default=None):
        self._default = default 
        self._on_change = []
        self._val = WeakKeyDictionary()
        self._instance_on_change = None
        self._transformation = None

    def on_change(self, f):
        self._on_change.append(f)
        return f

    def transformation(self, f):
        self._transformation = f
        return f

    def get_observable(self, instance_obj):
        if not instance_obj in self._val:
            self._register(instance_obj, None)
        attr = self._val[instance_obj]
        if hasattr(attr.val, 'on_change'):
            return attr.val 
        return (attr.val, attr.on_change)

    # -- API methods
    def __create__(self, val):
        return val, Event()

    def __assign__(self, attr_value, val):
        trigger_on_change = False
        if attr_value.val != val:
            trigger_on_change = True
        attr_value.val = val
        if trigger_on_change:
            attr_value.on_change(attr_value.val)

    # -- descriptor api

    def __set__(self, instance_obj, val):
        if not instance_obj in self._val:
            if val is not None:
                self._register(instance_obj, None, val)
           # self._val[instance_obj].on_change(self._val[instance_obj].val)
        else:
            self.__assign__(self._val[instance_obj], self._val[instance_obj].transformation(val))
            attr_val = self._val[instance_obj]
            val_on_change = observable_event(val)

            # check whether the observables event differs from
            # the previous registered host event. This happens
            # if another obserable was assigned to the attribute
            # so we have to detach event listers from the previous
            # host observables event.
            if val_on_change is not attr_val.host_on_change:
                if attr_val.host_on_change is not None and val_on_change is not None:
                    old_event = attr_val.host_on_change
                    if attr_val.host_listener in old_event:
                        old_event.remove(attr_val.host_listener)

                # bind to new host observable if possible
                if val_on_change is not None:
                    val_on_change.append(attr_val.host_listener)
                    attr_val.host_on_change = val_on_change

    def __get__(self, instance_obj, obj_type):
        if not instance_obj in self._val:
            self._register(instance_obj, obj_type)
        return self._val[instance_obj].val

    def _register(self, instance_obj, obj_type, val=None):
      #  if val is None and self._default is None:
      #      raise RuntimeError('attribute cannot be created without a default')

        transformation = lambda x: x
        if self._transformation is not None:
            transformation = partial(self._transformation, instance_obj)
        
        val = val if val is not None else self._default

        trans_value = transformation(observable_value(val))
        host_on_change = observable_event(val)

        attr_val = _AttributeValue(*self.__create__(trans_value), host_on_change)
        attr_val.transformation = transformation
        attr_val.host_listener = partial(self.__set__, instance_obj)
        attr_val.listener = [partial(f, instance_obj) for f in self._on_change]
        attr_val.on_change += attr_val.listener

        if attr_val.host_on_change is not None:
            attr_val.host_on_change.append(attr_val.host_listener)
        
        self._val[instance_obj] = attr_val


class CastedAttribute(Attribute):
    """
    a casted attribute has an **cast** callable
    which ensures that the values assigned to the 
    attribute are of some specific kind.

    ```python
        integer_attr = CastedAttribute(int, 0)
    ```
    """
    def __init__(self, cast, default=None):
        self._cast = cast 
        super().__init__(default)

    def __create__(self, val):
        return (self._cast(val) if val is not None else None), Event()

    def __assign__(self, attr_value, val):
        trigger_on_change = False
        if attr_value.val != val:
            trigger_on_change = True
        attr_value.val = self._cast(val) if val is not None else None
        if trigger_on_change:
            attr_value.on_change(attr_value.val)


class VectorAttribute(Attribute):

    def __init__(self, dimensions, default=None):
        self._dimensions = dimensions
        super().__init__(default)

    def __create__(self, val):
        if len(val) != self._dimensions:
            raise ValueError('wrong dimensions dude {}'.format(val))
        vector = vecn(val, use_instance=False)
        return vector, vector.on_change

    def __assign__(self, attr_value, val):
        attr_value.val.values = val

class ComputedAttribute(Attribute):
    """
    A computed attributes depends on a list of attributes
    and can have a descriptor which describes the attribute itself.

    ```python 
        from gpupy.gl.common import attributes
        class A():
            some_vector = attributes.VectorAttribute(2)
            scaling = attributes.CastedAttribute(int, 1)

            scaled_vector = attributes.ComputedAttribute(scaling, some_vector, 
                descriptor=attributes.VectorAttribute(2))

            @scaled_vector.transformation
            def scale(self, scaling, vector):
                return scaling * vector.xy
    ```

    Computed attribute does not allow to assign values explicitly. They are 
    watching the other attributes for changes, therefore all given
    argument descriptor must return (via. __get__) an observable or provide 
    the get_observable method.
    """


    def __init__(self, *fields, descriptor=None, some_test=None, transformation=None):
        self._attr = fields 
        self._descriptor = descriptor or Attribute()
        self._expl_transformation = transformation
        super().__init__()

    def transformation(self, f):
        if self._expl_transformation is not None:
            raise RuntimeError(('it is not allowed to define a transformation via.'
                              + ' decorator since there is allready one transformation'
                              + ' defined in the attribute configuration.'))
        return super().transformation(f)

    def __get__(self, instance_obj, obj_type):
        if not instance_obj in self._val:
            self._register(instance_obj, obj_type)
        return self._descriptor.__get__(instance_obj, obj_type)

    def __set__(self, *a):
        raise RuntimeError('it is not allowed to set the value of an computed attribute explicitly.')

    def _register(self, instance_obj, obj_type, val=None):
        if val is not None:
            raise RuntimeError('a computed attribute cannot have a default value.'.format(val))

        if self._expl_transformation is not None:
            tr = self._expl_transformation  
        else:
            tr = partial(self._transformation, instance_obj)

        # set initial value - this also ensures that the argument
        # attributes are loaded properly.
        argv_init = tuple(a.__get__(instance_obj, obj_type) for a in self._attr)
        self._descriptor.__set__(instance_obj, tr(*argv_init))

        # list of observables which the computed attribute depends on.
        attr_obs = tuple(o if observable_event(o) is not None else self._attr[i].get_observable() 
                         for i, o in enumerate(argv_init))

        # create obersvable
        obs = self._descriptor.get_observable(instance_obj)
        observable = transform_observables(tr, obs, attr_obs)

        # attach event listeners
        event = observable_event(observable) 
        event += [partial(f, instance_obj) for f in self._on_change]

        self._val[instance_obj] = observable

class ComponentAttribute(Attribute):
    """
    a component attribute is a attribute which contains another
    component. the on_change decorator allows to watch for the 
    attributes of the assigned component. 

    ```python
    class Derp(Component):
        ork = attributes.ComponentAttribute()

        # watch for ork.cool_attribute changes.
        ork.on_change('cool_attribute'):
        def derp(*e):
            print('i was called...')
    ```

    It is not allowed to apply transformations on component attributes.
    """
    def __init__(self):
        self._watch_attr = {}
        super().__init__(self)

    def transformation(self, f):
        raise RuntimeError('not allowed')

    def __set__(self, instance_obj, val):
        if not hasattr(val, '_'):
            raise ValueError('not a component {}'.format(val))

        if instance_obj in self._val:
            # nothing to do here.
            if self._val[instance_obj] is val:
                return

            # detach old event listeners 
            for attr, handlers in self._watch_attr.items():
                event = getattr(self._val[instance_obj]._, attr).on_change
                for handler in handlers:
                    event.remove(partial(handler, instance_obj))
            self._val[instance_obj] = None 

        self._val[instance_obj] = val

        # attach new event handlers
        for attr, handlers in self._watch_attr.items():
            if not hasattr(val, attr):
                raise RuntimeError('invalid component attribute ' + attr)
            event = getattr(self._val[instance_obj]._, attr).on_change
            for handler in handlers:
                event.append(partial(handler, instance_obj))

    def __get__(self, instance_obj, obj_type):
        if not instance_obj in self._val:
            raise ValueError('ComponentAttribute was not initialized with a value.')
        return self._val[instance_obj]

    def on_change(self, attr):
        def _wrap(f):
            if attr not in self._watch_attr:
                self._watch_attr[attr] = []
            self._watch_attr[attr].append(f)
            return f
        return _wrap

from gpupy.gl.texture import Texture1D, Texture2D, Texture3D, AbstractTexture

class GlTexture(Attribute):
    """
    stores a gpupy.gl.texture.AbstractTexture instance.

    when a texture object is defined the attribute setter
    passes the value to gpupy.gl.texture.AbstractTexture.set(data).

    initially a texture must be defined:
    i) use to_device kwarg to define a function which creates
       a texture from a numpy.ndarray

       ```python
       texture = attributres.GlTextures(to_device=Texture2d.to_device)
       ```

    ii) set a texture object
        ```python
        obj.texture = Texture2d(...)

    """
    def __init__(self, to_device=None):
        if to_device is not None and not hasattr(to_device, '__call__'):
            raise ValueError()

        self.to_device = to_device 
        super().__init__()

    def __set__(self, instance_obj, val):
        hastex = instance_obj in self._val
        if not hastex:
            _t = self._register(instance_obj, None, val)
        else:
            _t = self._val[instance_obj]
            _t.set(val)
            self.on_change(_t)

    def __get__(self, instance_obj, obj_type):
        if not instance_obj in self._val:
            self._register(instance_obj, obj_type)
        return self._val[instance_obj]

    def _register(self, instance_obj, obj_type, val=None):
        has_to_device = self.to_device is not None
        val_is_tex = isinstance(val, AbstractTexture)

        if val_is_tex:
            _t = val 
        elif not val_is_tex and has_to_device:
            _t = self.to_device(val)
        else:
            raise ValueError('invalid texture.')

        self._val[instance_obj] = _t
        return _t

class BufferObjectAttribute(Attribute):
    def __init__(self):
        super().__init__()

    def __get__(self, instance_obj, obj_type):
        if not instance_obj in self._val:
            self._register(instance_obj, obj_type)
        return self._val[instance_obj]

    def __set__(self, instance_obj, val):
        hasbuf = instance_obj in self._val 
        isbuf = isinstance(val, BufferObject)
        if not hasbuf:
            _b = self._register(instance_obj, None, val)
        elif isbuf:
            self._val[instance_obj] = val 
            self.on_change(val)
        else:
            self._val[instance_obj].set(val)

    def _register(self, instance_obj, obj_type, val=None):
        if isinstance(val, BufferObject):
            self._val[instance_obj] = val
        else:
            self._val[instance_obj] = BufferObject.to_device(val)

        return self._val[instance_obj]

class ObservablesAccessor():
    def __init__(self, host):
        self.__host = host
    def __getattr__(self, name):
        return self.__host.__class__.__dict__[name].get_observable(self.__host)

class _AttributeValue():
    """ internal attribute descriptor representation of an attribute """
    def __init__(self, val, on_change, host_on_change):
        self.val = val 
        self.on_change = on_change
        self.host_on_change = host_on_change
        self.transformation = None
        self.listener = None
        self.host_listener = None