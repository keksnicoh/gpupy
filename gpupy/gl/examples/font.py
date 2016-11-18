#-*- coding: utf-8 -*-
"""
open a single glfw window without any controller

:author: Nicolas 'keksnicoh' Heimann
"""
from gpupy.gl import Gl
Gl.DEBUG = True

from gpupy.gl.driver.glfw import GLFW_WindowFunction
from gpupy.gl.common import *

from gpupy.gl.camera import Camera
from gpupy.gl.font.renderer import FontRenderer

from OpenGL.GL import *
from gpupy.gl.vendor.glfw import glfwWindowHint, GLFW_SAMPLES



@GLFW_WindowFunction
def main(window):
    camera = None
    font_renderer = 1
    bla = 'pmg'
    render_parameters = {'width': .07390000000000001, 'edge': 3.7589999999996966}
    def init():
        window.set_size((800, 800))
        global font_renderer
        global render_parameters
        camera = Camera(window.get_size())
        camera.translate(z=-0.1)
        font_renderer = FontRenderer()
        font_renderer.init()
        glfwWindowHint(GLFW_SAMPLES, 4);
        font_renderer.create_text('10 123 .,- ich BIN COOL gjklm 123456789+#-', size=10, position=(-150-240,-190-200))
        font_renderer.create_text('12 123 .,- ich BIN COOL gjklm 123456789+#-', size=12, position=(-150-240,-170-200))
        font_renderer.create_text('14 123 .,- ich BIN COOL gjklm 123456789+#-', size=14, position=(-150-240,-150-200))
        font_renderer.create_text('16 123 .,- ich BIN COOL gjklm 123456789+#-', size=16, position=(-150-240,-130-200))
        font_renderer.create_text('18 123 .,- ich BIN COOL gjklm 123456789+#-', size=18, position=(-150-240,-110-200))
        font_renderer.create_text('20 123 .,- ich BIN COOL gjklm 123456789+#-', size=20, position=(-150-240,-90-200))
        font_renderer.create_text('24 123 .,- ich BIN COOL gjklm 123456789+#-', size=24, position=(-150-240,-65-200))
        font_renderer.create_text('28 123 .,- ich BIN COOL gjklm 123456789+#-', size=28, position=(-150-240,-35-200))
        font_renderer.create_text('32 123 .,- ich BIN COOL gjklm 123456789+#-', size=32, position=(-150-240,-0-200))
        font_renderer.create_text('40 123 .,- ich BIN COOL gjklm 123456789+#-', size=40, position=(-150-240,40-200))
        font_renderer.create_text('48 123 .,- ich BIN COOL gjklm 123456789+#-', size=48, position=(-150-240,80-200))
        font_renderer.create_text('56 123 .,- ich BIN COOL gjklm 123456789+#-', size=56, position=(-150-240,120-200))
        font_renderer.create_text('64 123 .,- ich BIN COOL gjklm 123456789+#-', size=64, position=(-150-240,180-200))
        font_renderer.create_text('80 123 .,- ich BIN COOL gjklm 123456789+#-', size=80, position=(-150-240,250-200))
        font_renderer.create_text('100 123 .,- ich BIN COOL gjklm 123456789+#-', size=100, position=(-150-240,320-200))
        font_renderer.create_text('140 123 .,- ich BIN COOL gjklm 123456789+#-', size=140, position=(-150-240,400-200))
        glClearColor(1,1,1,1)

    def render():
        global font_renderer

        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

        if {87, 93} == window.keyboard.active:
            render_parameters['width'] += 0.001
            print(render_parameters)
        elif {69, 93} == window.keyboard.active:
            render_parameters['edge'] += 0.001
            print(render_parameters)
        elif {87, 47} == window.keyboard.active:
            render_parameters['width'] -= 0.001
            print(render_parameters)
        elif {69, 47} == window.keyboard.active:
            render_parameters['edge'] -= 0.001
            print(render_parameters)

        font_renderer.render()

    window.on_init.append(init)
    window.on_cycle.append(render)

if __name__ == '__main__':
    main()


