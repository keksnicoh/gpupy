from gpupy.gl.components import Component 
from gpupy.gl.common import Event 

class Widget(Component):
    """
    A widget is a component with a render() method. 
    like components it can be a widget node if it
    has a widgets attribute. 

    After tick the widget should be ready for rendering. 
    Rule: a tick must be followed by at least one rendering.

    Events:
        on_pre_tick
        on_post_tick
        on_pre_render
        on_post_render
    """

    def __init__(self):
        super().__init__()
        self.on_pre_render = Event()
        self.on_post_render = Event()

    def render(self):
        self.on_pre_render()
        self._render()
        self.on_post_render()
