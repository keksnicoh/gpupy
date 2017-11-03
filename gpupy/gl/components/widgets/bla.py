from gpupy.plot.plotter2d import Plotter2d
from gpupy.plot import domain, nputil
from gpupy.plot.graph.fragmentgraph import FragmentGraph

import numpy as np 

plot = Plotter2d()

    plot.cs = (np.min(np.real(Z)), 
                  np.min(np.max(Z)), 
                  np.min(np.imag(Z)), 
                  np.max(np.imag(Z)))
    maxf = np.max(plot.cs)
    plot += FragmentGraph(
        domain={
            'zs': domain.sarray(FZ),
            'c':  domain.colorwheel('homer')
        },
        # note that tuple conversion is required since
        # the configuration space is static for the graph
        # so it should not listen to the plot cs (which might
        # change).
        cs=tuple(plot.cs),

        # use c domain as colorwheel
        fragment_kernel="""vec4 fragment_kernel(vec2 z) {
            float L = """+str(maxf)+""";
            vec2 n = $D.zs(z) / (2*L) + vec2(0.5);
            return vec4($D.c(n), 1);
        }""")


Z = nputil.cplane(-7, 7, -3, 3, steps=300)
FZ = np.sin(Z)

@plot2d 
def plot(plotter):


if __name__ == '__main__':
    plot()