from gpupy.plot import plot2d, domain, graph
from gpupy.plot.graph.fragmentgraph import FragmentGraph 
from gpupy.plot import nputil

from time import time
import numpy as np 
@plot2d 
def plot(plotter):
    # -- test texture
    keksnicoh = domain.colorwheel('keksnicoh')
    keksnicoh.smooth(False)

    # -- random sampler
    random = domain.random(timeseed=True)

    # -- plot simple texte
    #
    # uses the default fragment_kernel. Note that if not domain
    # is given one must define a custom fragment_kernel
    homer = domain.colorwheel('homer')

    # homer - original
    plotter += FragmentGraph(homer, cs=(1, 2, 0, 1))

    # homer - greyscale_luminosity
    plotter += FragmentGraph(
        domain=homer, 
        cs=(1, 2, -1, 0), 
        fragment_kernel="""vec4 fragment_kernel(vec2 c) {
            vec3 x = $D.domain(c);
            float _r=0.21*x.x+0.72*x.y+0.07*x.z; 
            return vec4(_r, _r, _r, 1);
        }""")
    # homer - greyscale_lightness
    plotter += FragmentGraph(
        domain=homer, 
        cs=(0, 1, 0, 1), 
        fragment_kernel="""vec4 fragment_kernel(vec2 c) {
            vec3 x = $D.domain(c);
            float M = max(x.x, max(x.y, x.z)); float m = min(x.x, min(x.y, x.z)); 
            return vec4(m+M, m+M,m+M,2)/2;
        }""")
    # homer - greyscale_avg
    plotter += FragmentGraph(
        domain=homer, 
        cs=(0, 1, -1, 0), 
        fragment_kernel="""vec4 fragment_kernel(vec2 c) {
            vec3 x = $D.domain(c);
            return vec4(x.x+x.y+x.z, x.x+x.y+x.z, x.x+x.y+x.z, 3) / 3;
        }""")


    # dynamic configuration space
    def upper_right(cs):
        return (cs[1]-(cs[1]-cs[0])*0.25, cs[1], cs[3]-(cs[3]-cs[2])*0.25, cs[3])
    plotter += FragmentGraph(keksnicoh, cs=plotter.cs.observe(upper_right))

    # -- 3 waves 
    graph_3waves =  FragmentGraph(
        domain = domain.random(timeseed=True),
        cs=(0, 2, 1, 3), 
        fragment_kernel="""
        uniform float time = 0;
        vec4 fragment_kernel(vec2 c) {
            vec2 w1 = (c - 0.5) * 10;
            vec2 w2 = w1 + vec2(0, 2);
            vec2 w3 = w1 - vec2(0, 2);
            return vec4(
                0.5+0.5*cos(10*sqrt(w1.x*w1.x+w1.y*w1.y)-30*time), 
                0.5+0.5*cos(10*sqrt(w2.x*w2.x+w2.y*w2.y)-30*time), 
                0.5+0.5*cos(10*sqrt(w3.x*w3.x+w3.y*w3.y)-30*time), 0.75+0.25*$D.domain(c));
        }""");

    initial_time = time()
    def timer():
        graph_3waves.program.uniform('time', time() - initial_time)
    graph_3waves.on_tick.append(timer)
    plotter += graph_3waves

    # builing a plane wave
    graph_plane = FragmentGraph(cs=(2, 8, -3, 3), fragment_kernel="""
    uniform float time = 0;
    vec4 fragment_kernel(vec2 c) {
        float y0 = -5;
        float dy = 1;
        float y1 = 5;
        float n = floor((y1-y0)/dy);
        c = (c - 0.5) * 20;
        vec2 w;
        float ampl = 0;
        for (float y = y0; y < y1; y += dy) {
            w = vec2(2*c.x, c.y+y);
            ampl += cos(10*sqrt(w.x*w.x+w.y*w.y)-30*time);
        }
        return vec4(4*ampl/n, 0, 0, 1);
    }""")

    initial_time = time()
    def timer():
        graph_plane.program.uniform('time', time() - initial_time)
    graph_plane.on_tick.append(timer)
    plotter += graph_plane


if __name__ == '__main__':
    plot()