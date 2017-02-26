#-*- coding: utf-8 -*-
"""


from glsl_plotter import plotter
plotter(window_size=(400, 400)).plot('x**x', 'sin(x)')


:author: Nicolas 'keksnicoh' Heimann
"""

from gpupy.plot.plotter2d import Plotter2d
from OpenGL.GL import *
from gpupy.gl import *
from gpupy.gl.common.vector import *
import numpy as np
from gpupy.gl.components.camera import Camera2D
from gpupy.gl.glfw import GLFW_window
from time import time
from gpupy.plot.graph.frgfnc import Frag1DGraph, Frag2DGraph
from gpupy.plot.graph.glpoints import GlPointsGraph
from gpupy.plot import domain

from functools import partial
GPUPY_GL.DEBUG = True
class Plotter2dBasic():
    def __init__(self, window, plot):
        self.window = window
        window.on_ready.append(self.init)
        window.on_cycle.append(self.draw)
        window.on_resize.append(self.resize)
        window.on_cycle.append(partial(self.flag,False))
        self._plot = plot
        self._resizing = False
        self.t = time()
    def flag(self,unf, *e):
        if unf != self._resizing:
            sf = 0.5
            self.plotter.plot_resolution_factor = 1 if not unf else sf
            self._resizing = unf

    def resize(self, window):
        self.flag(True)
        self.draw(window)

    def init(self, window):
        size = window.size
        self.camera = Camera2D(screensize=size, position=size.observe_as_vec3(lambda v: (v[0]/2, v[1]/2, 0)))
        s = self.window.size
        self.plotter = Plotter2d(size, cs=(-4, 4, -4, 4))
        self._plot(self.plotter)
        self.plotter.init()
        self.plotter._plot_container.border = (2,2,2,2)
        self.plotter._plot_container.margin = (10, 10, 10, 10)
        self.border = 3 

    def draw(self, window):
        # very basic plot controlling
        dt = time()-self.t
        #self.plotter2.plot_resolution_factor = 0.8+0.5*np.sin(dt)

        check_cs = False
        speed = 0.05
        if 68 in self.window.active_keys: #d
            self.plotter.cs += (speed, speed, 0, 0)
        if 65 in self.window.active_keys: #a
            self.plotter.cs -= (speed, speed, 0, 0)
        if 87 in self.window.active_keys: #w
            self.plotter.cs += (0, 0, speed, speed)
        if 83 in self.window.active_keys: #s
            self.plotter.cs -= (0, 0, speed, speed)
        if 32 in self.window.active_keys and 340 in self.window.active_keys: #s
            check_cs = True
            self.plotter.cs += (-0.01, 0.01, -0.01, 0.01)
        elif 32 in self.window.active_keys: #s
            check_cs = True
            self.plotter.cs *= (0.99, 0.99, 0.99, 0.99)
        if False and check_cs:
            au = self.plotter.axes_unit
            css = self.plotter.cs_size
            n = (css.x/au.x, css.y/au.y)
            if n[0] > 10:
                self.plotter.axes_unit.x = css.x/5
            if n[1] > 10:
                self.plotter.axes_unit.y = css.y/5
            if n[0] < 5:
                self.plotter.axes_unit.x = css.x/10
            if n[1] < 5:
                self.plotter.axes_unit.y = css.y/10
            print(self.plotter.axes_unit)
        dt = time() - self.t
        self.plotter.tick()

        glClearColor(*self.plotter.background_color.values)
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        self.camera.enable()
        self.plotter.draw()

  
@GLFW_window
def main(window):
    texture_controller = Plotter2dBasic(window, plot)









def plot(plotter):
    # some 1d fragment tests
    plotter['jau'] = Frag1DGraph.glsl_transformation(
        'sin(x)', 
        cs=plotter.cs)
    plotter += Frag1DGraph.glsl_transformation(
        'cos(10*x)/(1+x*x)', 
        cs=plotter.cs, 
        color_kernel=('expr', "vec4(fc.y+0.5, 0, 1-fc.y-.5, exp(-2*abs(xsd)))"))
    plotter += Frag1DGraph.glsl_transformation(
        'sin(8*x)/(1.2+sin(x))', 
        cs=plotter.cs,
        color_kernel=('function', "if (xsd > 0) { discard; } return vec4(0, fc.y+0.5, 1-fc.y-.2, 0.2*exp(-2*abs(xsd))); "))
    plotter += Frag1DGraph.glsl_transformation(
        'x*x', 
        cs=plotter.cs, 
        color_kernel=('expr', "vec4(fc.x+0.2, .4, 1-fc.y-.5, exp(-2*abs(xsd)))"))

    import os

    nx = 700
    complex_plane = np.array([complex(5*x/nx,3*y/nx) for x in range(-nx, nx) for y in range(-nx, nx)], dtype=np.complex64).reshape((2*nx, 2*nx))

    data = np.sin(complex_plane)

    vd = data.view(np.float32).reshape((2*nx, 2*nx, 2))
    vdx = vd[:, :, 0]
    vdy = vd[:, :, 0]
    mx, Mx = np.max(vdx), np.min(vdx)
    my, My = np.max(vdy), np.min(vdy)
    vdx -= mx; vdx /= Mx - mx
    vdy -= my; vdy /= My - my





    # plot something with a colorwheel

    texture = Texture2D.to_device(vd)
    texture.interpolation_linear()
    gg = Frag2DGraph(domain.TextureDomain(texture), 
                     color_kernel=("color", {'alpha_f': .2, 
                                             'color_domain': 'color'}))
    gg['color'] = domain.TextureDomain.colorwheel()
    plotter += gg




    data = np.array([
        ((x, 2*np.sin(x)), ) for x in (x/1000 for x in range(-2000, 2000))
    ], dtype=np.dtype([
        ('point', (np.float32, 2))
    ]))


    datax = np.array([x for x in (x/1000 for x in range(-2000, 2000))], dtype=np.float32)
    datay = np.array([2*np.sin(x) for x in (x/1000 for x in range(-2000, 2000))], dtype=np.float32)

    fd = np.array([
        x for x in (x/1000 for x in range(-2000, 2000))
    ], dtype=np.float32)

    orrk = GlPointsGraph()
    orrk['x'] = domain.VertexDomain(datax)
    orrk['y'] = domain.VertexDomain(datay)
    orrk['f'] = domain.VertexDomain(fd)
    orrk.kernel = """
        vec2 kernel() {
            gl_PointSize = 3;
            v_col = vec4(sin(10*${DOMAIN:y})*sin(10*${DOMAIN:y}), cos(10*${DOMAIN:y})*cos(10*${DOMAIN:y}), 0.2, 1);
            return vec2(${DOMAIN:x}, ${DOMAIN:y} * ${DOMAIN:f});
        }
    """


    plotter +=orrk

    data = np.array([(x, 2*np.sin(x)) for x in (x/1000 for x in range(-2000, 2000))], dtype=np.float32)
    orrk = GlPointsGraph(domain.VertexDomain(data))
    orrk.kernel = "vec2 kernel() { return ${DOMAIN}.xy; } "
    orrk.cs = plotter.cs

    plotter +=orrk

    data = np.array([((x, 1*np.sin(10*x)), ) for x in (x/1000 for x in range(-2000, 2000))], dtype=np.dtype([('xy', (np.float32, 2))]))
    orrk = GlPointsGraph(domain.VertexDomain(data))
    orrk.kernel = "vec2 kernel() { return ${DOMAIN}_xy; } "
    orrk.cs = plotter.cs

    plotter +=orrk


    data = np.arange(0, 1, .0001, dtype=np.float32)
    orrk = GlPointsGraph(domain.VertexDomain(data))
    orrk.kernel = """vec2 kernel() { 
        float x = plot.cs.x + plot.cs_size.x * ${DOMAIN};
        return vec2(x, sin(20*x) * sin(10*x) * cos(2*x) * cos(2*x) * cos(4*x) * sin(x));
    } 
    """
    plotter +=orrk

    data = np.arange(0, 1, .0001, dtype=np.float32)
    orrk = GlPointsGraph(domain.VertexDomain(data))
    orrk['x'] = domain.TransformationDomain("""float ${FNAME}() { return plot.cs.x + plot.cs_size.x * ${DOMAIN}; } """)
    orrk.kernel = """vec2 kernel() { float x = ${DOMAIN:x}();return vec2(x, ${DOMAIN:y}(x));} """
    orrk['y'] = domain.TransformationDomain("""float ${FNAME}(float x) {return sin(20*x) * sin(10*x) * cos(2*x) * cos(2*x) * cos(4*x) * sin(x);}""")
    plotter +=orrk





    # apply keksnicoh 
    keksnioh = domain.TextureDomain.colorwheel('keksnicoh')
    def upper_right(cs):
        return (cs[1]-(cs[1]-cs[0])*0.25, cs[1], cs[3]-(cs[3]-cs[2])*0.25, cs[3])
    plotter += Frag2DGraph(keksnioh, cs=plotter.cs.observe(upper_right))
    plotter += Frag2DGraph(keksnioh, cs=(-4,-2,2,4), color_kernel="greyscale_avg")
    plotter += Frag2DGraph(keksnioh, cs=(-2,-0,2,4), color_kernel="greyscale_lightness")
    plotter += Frag2DGraph(keksnioh, cs=(-0,2,2,4), color_kernel="greyscale_luminosity")


if __name__ == '__main__':
    main()