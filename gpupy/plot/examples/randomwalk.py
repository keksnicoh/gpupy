from gpupy.plot import plot2d
from gpupy.plot.graph.frgfnc import Frag1DGraph
from gpupy.plot.domain import TextureDomain
import numpy as np 
@plot2d
def plot(plotter):
    # some 1d fragment tests

    # sine on dynamic configuration space
    rw = 1*np.ones((10000,), dtype=np.float32)
    dmn = TextureDomain.to_device_1d(rw)
    color = "vec4(abs(fc.x)+0.2, .4, 1-abs(fc.y)-.5, .1+exp(-2*abs(xsd)))"
    plotter['named_plot'] = Frag1DGraph(dmn, cs=(0,1,0,1),
        color_kernel=("color", {'alpha_f': .2, 'color_domain': 'color'}))

        #.glsl_transformation('x', 
        #cs=plotter.cs.observe(lambda cs: (cs[0], cs[1], -1, 1)))


if __name__ == '__main__':
    plot()