from gpupy.plot import plot2d
from gpupy.plot.graph.frgfnc import Frag1DGraph

@plot2d
def plot(plotter):
    # some 1d fragment tests

    # sine on dynamic configuration space
    plotter['named_plot'] = Frag1DGraph.glsl_transformation('sin(x)', 
        cs=plotter.cs.observe(lambda cs: (cs[0], cs[1], -1, 1)))

    print(plotter['named_plot']) # access via key

    # lets plot a parapula within [-5, 5, -2, 25]
    func = 'x*x'
    color = "vec4(abs(fc.x)+0.2, .4, 1-abs(fc.y)-.5, .1+exp(-2*abs(xsd)))"
    cs = (-5, 5, -2, 25)
    graph = Frag1DGraph.glsl_transformation(func, cs=cs, color_kernel=('expr', color))
    plotter += graph

    print(plotter[id(graph)]) # access via object id

if __name__ == '__main__':
    plot()