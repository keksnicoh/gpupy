#-*- coding: utf-8 -*-
"""
example creates a glpoints graph using a cartesian
x domain and a random function domain for y-values.
:author: keksnicoh
"""

from gpupy.plot import plot2d
from gpupy.plot.domain import VertexDomain, RandomDomain
from gpupy.plot.graph.glpoints import GlPointsGraph 

@plot2d 
def plot(plotter):

    # domain on [0, 1] will be projected onto full cs
    # x-axes by using shader function cartesian_x
    domain = VertexDomain.arange(0, 1, 0.00001)

    # glpoints graph with custom kernel
    graph = GlPointsGraph(domain, kernel="""vec2 kernel() { 
        // point pixel size
        ${SIZE} = 2;

        // extend vertex domain over x axis
        float x = cartesian_x(${DOMAIN});

        // colorize 
        v_col = vec4(1 - ${domain.rand}(x), 1, ${domain.rand}(x), 1);

        // vertex coords
        return vec2(x, ${domain.rand}(x));
    }""")

    # add the random domain to the graph
    graph['rand'] = RandomDomain(timeseed=False)
    #graph['rand'] = dm.random()

    # add graph to plotter
    plotter += graph

if __name__ == '__main__':
    plot()