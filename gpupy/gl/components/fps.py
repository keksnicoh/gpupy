# will be an fps counter

from gpupy.gl.font.renderer import FontRenderer

from time import time 

class Fps():

    def __init__(self, font_renderer=None, size=50, color=(1, 1, 1, 1)):
        if font_renderer is None:
            font_renderer = FontRenderer()
            font_renderer.init()

        self.font_renderer = font_renderer
        self._text = self.font_renderer.create_text('0 FPS', size=size, color=color)
        self._t = 0
        self.last_time = time()
    def tick(self):
        t = time()
        dt = t - self.last_time
        if (t - self.last_time > 1):
            self._text.chars = '{:.2f} FPS'.format(self._t / dt)
            self._t = 0
            self.last_time = t 
        else:
            self._t += 1
    def draw(self):
        self.font_renderer.render_text(self._text)