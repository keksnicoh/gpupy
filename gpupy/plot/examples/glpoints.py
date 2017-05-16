from gpupy.plot import plot2d, domain
from gpupy.plot.graph.glpoints import GlPointsGraph 
from gpupy.gl import GPUPY_GL
import numpy as np 
GPUPY_GL.DEBUG = True

@plot2d 
def plot(plotter):

    # default behavior 
    data = np.array([
        (x, 2*np.sin(x)) for x in (x/1000 for x in range(-2000, 2000))
    ], dtype=np.float32)
    plotter += GlPointsGraph(domain.VertexDomain(data))

    # struct access with custom kernel
    data = np.array([
        ((x, 1*np.sin(10*x)), ) for x in (x/1000 for x in range(-2000, 2000))
    ], dtype=np.dtype([('xy', (np.float32, 2))]))
    plotter += GlPointsGraph(domain.VertexDomain(data), kernel="vec2 kernel() { return ${DOMAIN}; } ")
    #plotter += GlPointsGraph(dm.array(data), kernel="vec2 kernel() { return ${DOMAIN}; } ")

    # simple dynamic domain
    data = np.arange(0, 1, .0001, dtype=np.float32)
    plotter += GlPointsGraph(domain.VertexDomain(data), kernel="""vec2 kernel() { 
        v_col = vec4(1,1,1,1);
        gl_PointSize = 4;
        float x = cartesian_x(${DOMAIN});
        return vec2(x, 1/x);
    }""")


    # some fancy stuff and dynamic domain
    data = np.arange(0, 1, .0001, dtype=np.float32)
    g=GlPointsGraph(domain.VertexDomain(data), kernel="""vec2 kernel() { 
        float cx = ${DOMAIN}+0.4;
        gl_PointSize = 1+5*cos(10*cx)*cos(10*cx);
        float x = cartesian_x(${DOMAIN});
        float z = x + 1*ticker_test;
        float y = sin(20*z) * sin(10*z) * cos(2*z) * cos(2*z) * cos(4*z) * sin(z);
        v_col = vec4(3*y,1-y,0,1);
        return vec2(x, y);
    }""")
    
    g._dynamic_test = True
    plotter += g
    # composing domains
    datax = np.array([x for x in (x/1000 for x in range(-2000, 2000))], dtype=np.float32)
    datay = np.array([2*np.sin(x) for x in (x/1000 for x in range(-2000, 2000))], dtype=np.float32)
    fd = np.array([
        x for x in (x/1000 for x in range(-2000, 2000))
    ], dtype=np.float32)
    composed_graph = GlPointsGraph()
    composed_graph['x'] = domain.VertexDomain(datax)
    #composed_graph['x'] = datax
    composed_graph['y'] = domain.VertexDomain(datay)
    #composed_graph['y'] = datay
    composed_graph['f'] = domain.VertexDomain(fd)
    #composed_graph['f'] = fd
    composed_graph.kernel = """
        vec2 kernel() {
            gl_PointSize = 3;
            v_col = vec4(sin(10*${domain.y})*sin(10*${domain.y}), cos(10*${domain.y})*cos(10*${domain.y}), 0.2, 1);
            return vec2(${domain.x}, ${domain.y} * ${domain.f});
        }
    """
    #plotter += composed_graph

if __name__ == '__main__':
    plot()