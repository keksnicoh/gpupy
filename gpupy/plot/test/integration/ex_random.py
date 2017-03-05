from gpupy.plot import plot2d, domain
from gpupy.plot.graph.glpoints import GlPointsGraph 

import numpy as np 

@plot2d 
def plot(plotter):

    # simple dynamic domain
    data = np.arange(0, 1, 0.001, dtype=np.float32)
    graph = GlPointsGraph(domain.VertexDomain(data), kernel="""vec2 kernel() { 
        float x = ${DOMAIN};
        v_col = vec4(1 - ${DOMAIN:rand}(x), 1, ${DOMAIN:rand}(x), 1);
        return vec2(x, ${DOMAIN:rand}(x));
    }""")
    graph['rand'] = domain.RandomDomain()

    plotter += graph



if __name__ == '__main__':
    plot()