from gpupy.gl.common import Event 
from gpupy.gl.common.vector import Vector
from functools import partial 
__all__ = ['bind', 'transform_observables', 'observable_event', 'observable_value']


def bind(observable, callback):
    """ binds an **observable** by applying a callback
        to the on_change event. It returns the
        **observables**`s current value

        if **observable** does not classify as an observable or
        **callback** is not callable a `ValueError` will be raised."""
    if (isinstance(observable, tuple) and len(observable) == 2 and isinstance(observable[1], Event)):
        val, on_change = observable
    elif hasattr(observable, 'on_change'):
        on_change = observable.on_change
        val = observable
    else:
        raise ValueError('argument #1 observable {} is not an observable'.format(observable))

    if not hasattr(callback, '__call__'):
        raise ValueError('argument #2 callback must be a callback')

    on_change.append(callback)

    return val


def observable_event(observable):
    if (isinstance(observable, tuple) and len(observable) == 2 and isinstance(observable[1], Event)):
        return observable[1]
    elif hasattr(observable, 'on_change'):
        return observable.on_change

def observable_value(observable):
    if (isinstance(observable, tuple) and len(observable) == 2 and isinstance(observable[1], Event)):
        return observable[0]
    elif hasattr(observable, 'on_change'):
        return observable
    else:
        return observable


def transform_observables(transformation, ctx_or_observables=None, observables=None):
    """ transforms a the value of a given list of **observables** by a
        given **transformation**. If **observable** is None the **ctx_or_observables**
        argument represents the list of observables.

        a context is an mutable object which can be an observable. 

        Example: simple observable
        ```python
            obs1 = vec2((1,1))
            obs2 = vec2((2,4))

            initial_tuple, event = transform_observable(lambda: (a.x, b.y), (obs1, obs2))
            print(intitial_tuple) # (1, 4)

            def _say_something(new_value):
                print(new_value)

            event.append(_say_something)
            obs1.x = 5 # (5, 4)
            initial_tuple # (1, 4)

        Example: mutable type (list) 
        ```python
            obs1 = vec2((1,1))
            obs2 = vec2((2,4))

            mutating_list, event = transform_observable(lambda: (a.x, b.y), [], (obs1, obs2))

            def _say_something(*e):
                print('__got changes??')
            event.append(_say_something)

            mutating_list # [1, 4]

            obs1.x = 5    # __got changes??
            mutating_list # [5, 4]

        Its does not make sense to pass an initial value if it is unmutable.

        ```python
            obs1 = vec2((1,1))
            obs2 = vec2((2,4))
            
            # will raise ValueError
            initial_tuple, event = transform_observable(lambda: (a.x, b.y), (1,2), (obs1, obs2))
        ```
    """

    if ctx_or_observables is None:
        if observables is None:
            raise ValueError('wh0t')
        return _transform_observables(None, None, transformation, *observables)

    if observables is None:
        if ctx_or_observables is None:
            raise ValueError('wh0t')
        return _transform_observables(None, None, transformation, *ctx_or_observables)

    if ctx_or_observables.__class__ in (int, str, float, tuple):
        raise ValueError('does not make sense sorryy')
    elif isinstance(ctx_or_observables, Vector):
        mutator = partial(ctx_or_observables.__class__.__dict__['values'].__set__, ctx_or_observables)
    elif hasattr(ctx_or_observables, '__mutate__'):
        mutator = ctx_or_observables.__mutate__
    elif hasattr(ctx_or_observables, 'update'):
        mutator = partial(getattr(ctx_or_observables, 'update'))
    elif hasattr(ctx_or_observables, '__setitem__'):
        mutator = partial(getattr(ctx_or_observables, '__setitem__'), slice(None, None, None))

    else:
        raise ValueError('do not know how to mutate ctx_or_observables')
    
    return _transform_observables(ctx_or_observables, mutator, transformation, *observables)

def _transform_observables(context, mutator, transformation, *observable):
    # the dispatcher arguments will be the observable values.
    dspargs = [None] * len(observable)

    # an context having a on_change attribute implies that 
    # it is itself mutable (otherwise one could not append event listeners).
    # => mutator must be callable
    if hasattr(context, 'on_change'):
        if not hasattr(mutator, '__call__'):
            raise ValueError('mutator')
        on_change = context.on_change
        __dispatch = mutator
    else:
        # a context without on_change attribute can either be mutable
        # or immutable. Here it is mutable if a mutator exists. 
        on_change = Event()
        if hasattr(mutator, '__call__'):
            def __dispatch(val):
                mutator(val)

                # context is mutable, so pass context itself as 
                # the first event argument.
                on_change(context)
        else:
            # it just does not make sense to use a context here, since it will be overwritten
            # directly when the initial valaue is transformed.
            if context is not None:
                raise ValueError('context must be None since it is implicitly given by transformation if mutator is None.')

            def __dispatch(val):
                # the context is immutable so pass the value
                # from the transformation as the event argument.
                on_change(val)

    # dispatch if the i-th observable has changes
    def _callback(i, context):
        dspargs[i] = context
        __dispatch(transformation(*dspargs))

    # initialize dispatching args and assign 
    # event handlers to observables.
    for i, s in enumerate(observable):
        dspargs[i] = bind(s, partial(_callback, i))

    # transform the initial value and dispatch
    val = transformation(*dspargs)
    __dispatch(val)

    # object is mutable and is an observable
    if hasattr(context, 'on_change'):
        return context 
    else:
        if hasattr(mutator, '__call__'):
            return (context, on_change) # mutable, no observable
        else:
            return (val, on_change)     # immutable, no observable

