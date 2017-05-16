from gpupy.plot import plot2d, domain
from gpupy.plot.graph.glpoints import GlPointsGraph 

import numpy as np 

@plot2d 
def plot(plotter):

    # simple dynamic domain
    graph = GlPointsGraph(domain.arange(0, 1, 0.00001), kernel="""vec2 kernel() { 
        float x = cartesian_x(${DOMAIN});
        float y = ${domain.rand}(x);
        ${SIZE} = 2;
        v_col = vec4(1 - ${domain.rand}(x), 1, ${domain.rand}(x), 1);
        return vec2(x, y);
    }""")
    graph['rand'] = domain.RandomDomain(timeseed=False)

    plotter += graph



if __name__ == '__main__':
    plot()