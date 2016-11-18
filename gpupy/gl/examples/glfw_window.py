#-*- coding: utf-8 -*-
"""
open a single glfw window without any controller

:author: Nicolas 'keksnicoh' Heimann
"""
from gpupy.gl.driver.glfw import GLFW_WindowFunction
from gpupy.gl.common import *

from OpenGL.GL import *

@GLFW_WindowFunction
def main(window):
    print('we should see a window right now.')

if __name__ == '__main__':
    main()


