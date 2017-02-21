#-*- coding: utf-8 -*-
"""
open a single glfw window without any controller

:author: Nicolas 'keksnicoh' Heimann
"""
from gpupy.gl.glfw import GLFW_WindowFunction

@GLFW_WindowFunction
def main(window):
    print('we should see a window right now.')

if __name__ == '__main__':
    main()


