from gpupy.plot import plot2d, domain
from gpupy.plot.graph.glpoints import GlPointsGraph 

import numpy as np 

@plot2d 
def plot(plotter):

    # default behavior 
    data = np.array([(x, 2*np.sin(x)) for x in (x/1000 for x in range(-2000, 2000))], dtype=np.float32)
    plotter += GlPointsGraph(domain.VertexDomain(data))

    # struct access with custom kernel
    data = np.array([((x, 1*np.sin(10*x)), ) for x in (x/1000 for x in range(-2000, 2000))], dtype=np.dtype([('xy', (np.float32, 2))]))
    plotter += GlPointsGraph(domain.VertexDomain(data), kernel="vec2 kernel() { return ${DOMAIN}_xy; } ")

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
    plotter += GlPointsGraph(domain.VertexDomain(data), kernel="""vec2 kernel() { 
        float cx = ${DOMAIN}+0.4;
        v_col = vec4(sin(10*cx)*sin(10*cx),1,cos(10*cx)*cos(10*cx),1);
        gl_PointSize = 5*cos(10*cx)*cos(10*cx);
        float x = cartesian_x(${DOMAIN});
        return vec2(x, sin(20*x) * sin(10*x) * cos(2*x) * cos(2*x) * cos(4*x) * sin(x));
    }""")

    # composing domains
    datax = np.array([x for x in (x/1000 for x in range(-2000, 2000))], dtype=np.float32)
    datay = np.array([2*np.sin(x) for x in (x/1000 for x in range(-2000, 2000))], dtype=np.float32)
    fd = np.array([
        x for x in (x/1000 for x in range(-2000, 2000))
    ], dtype=np.float32)
    composed_graph = GlPointsGraph()
    composed_graph['x'] = domain.VertexDomain(datax)
    composed_graph['y'] = domain.VertexDomain(datay)
    composed_graph['f'] = domain.VertexDomain(fd)
    composed_graph.kernel = """
        vec2 kernel() {
            gl_PointSize = 3;
            v_col = vec4(sin(10*${DOMAIN:y})*sin(10*${DOMAIN:y}), cos(10*${DOMAIN:y})*cos(10*${DOMAIN:y}), 0.2, 1);
            return vec2(${DOMAIN:x}, ${DOMAIN:y} * ${DOMAIN:f});
        }
    """
    plotter += composed_graph

if __name__ == '__main__':
    plot()