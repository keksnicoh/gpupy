from gpupy.plot import plot2d, domain, nputil
from gpupy.plot.graph.fragmentgraph import FragmentGraph

import numpy as np 

Z = nputil.cplane(-7, 7, -3, 3, steps=300)
FZ = np.sin(Z)

@plot2d 
def plot(plotter):
    plotter.cs = (np.min(np.real(Z)), 
                  np.min(np.max(Z)), 
                  np.min(np.imag(Z)), 
                  np.max(np.imag(Z)))
    maxf = np.max(plotter.cs)
    plotter += FragmentGraph(
        domain={
            'zs': domain.sarray(FZ),
            'c':  domain.colorwheel('homer')
        },
        # note that tuple conversion is required since
        # the configuration space is static for the graph
        # so it should not listen to the plot cs (which might
        # change).
        cs=tuple(plotter.cs),

        # use c domain as colorwheel
        fragment_kernel="""vec4 fragment_kernel(vec2 z) {
            float L = """+str(maxf)+""";
            vec2 n = $D.zs(z) / (2*L) + vec2(0.5);
            return vec4($D.c(n), 1);
        }""")

if __name__ == '__main__':
    plot()