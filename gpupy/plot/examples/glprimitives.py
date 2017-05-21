from gpupy.plot import plot2d, domain
from gpupy.plot.graph.glprimitives import GlPrimitivesGraph 
from gpupy.gl import GPUPY_GL
import numpy as np 
GPUPY_GL.DEBUG = True

@plot2d 
def plot(plotter):

    # -- create some (x, y) data
    x = np.arange(-2, 2, 0.001, dtype=np.float32)
    data = np.dstack((x, np.sin(x)))[0]
    plotter += GlPrimitivesGraph(domain.to_gpu(data))

    # -- structurized data custom kernel
    struct_data = domain.array([
        ((0, 0), 10, (1, 0, 0, 1)),
        ((1, 0), 5,  (1, 0, 0, 1)),
        ((0, 1), 20, (0, 1, 0, 1)),
        ((2, 0), 22, (1, 0, 1, 1)),
        ((0, 2), 11, (.2, 0.2, 0.3, 1)),
    ], dtype=np.dtype([('xy',    np.float32, 2), 
                       ('size',  np.float32, 1), 
                       ('color', np.float32, 4)]))
    graph = GlPrimitivesGraph(struct_data, kernel="""
    vec2 kernel() {
        $size = $D.domain.size;
        $color = $D.domain.color;
        return $D.domain.xy;
    }""")
    plotter += graph

    # -- custom kernel allows to influence shading
    plotter += GlPrimitivesGraph(domain.array(x), kernel="""vec2 kernel() { 
        $size = 4;
        float x =  cartesian_x( $D.domain);
        $color  = vec4(1, 0.5+0.5*cos(3*x), 0.5+0.5*sin(10*x), 1);

        return vec2(x, 1/x);
    }""", mode="lines")
    
    # -- Kernel using a uniform which is changed
    #    dynamically each tick.
    from time import time
    initial_time = time()
    graph = GlPrimitivesGraph(domain.array(x), kernel="""
    uniform float time;
    vec2 kernel() { 
        float cx = $D.domain+0.4;
        $size = 1+5*cos(10*cx)*cos(10*cx);

        float x = cartesian_x($D.domain);
        float z = x + 1*time;
        float y = sin(20*z) * sin(10*z) * cos(2*z) * cos(2*z) * cos(4*z) * sin(z);

        $color = vec4(3*y,1-y,0,1);

        return vec2(x, y);
    }""")  

    def tick():
        graph.program.uniform('time', time() - initial_time)
    graph.on_tick.append(tick)

    plotter += graph
 
    # composing domains - SHITTY API
    composed_graph = GlPrimitivesGraph()
    composed_graph['x'] = domain.array(x)
    composed_graph['y'] = domain.array(2 * np.sin(x))
    composed_graph['z'] = domain.array(np.exp(-x**2))
    composed_graph.kernel = """vec2 kernel() {
        gl_PointSize = 3;
        return vec2($D.x, $D.y * $D.z);
    }"""
    plotter += composed_graph

if __name__ == '__main__':
    plot()