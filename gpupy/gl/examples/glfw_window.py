#-*- coding: utf-8 -*-
"""
opens a single glfw widow with the
void controller. 

:author: Nicolas 'keksnicoh' Heimann
"""
from gpupy.gl.glfw import bootstrap_gl, create_runner, GLFW_Window

if __name__ == '__main__':
    bootstrap_gl()
    windows = [GLFW_Window()]
    for window in create_runner(windows):
    	if not window():
    		windows.remove(window)

else:
	raise Exception('please run as __main__.')
