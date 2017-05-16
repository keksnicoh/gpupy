from gpupy.plot import plot2d, domain, graph 
import numpy as np 
@plot2d 
def plot(plotter):

    g = graph.glpoints.GlPointsGraph()
    
    g['x'] = domain.VertexDomain.arange(0, 15, .0001, dtype=np.float32)
   # g['x'] = domain.arange(0, 15, .0001, dtype=np.float32)
    g['y'] = domain.TextureDomain.to_device_1d(np.sin(np.arange(0, 15, .01, dtype=np.float32)))
    #g['y'] = domain.tarray(np.sin(np.arange(0, 15, .01, dtype=np.float32)))
    g['y'].smooth(True)

    # just for fun we apply a function domain here...
    g['t'] = domain.FunctionDomain("""
        float ${FNAME}(float x) {
            return x*x;
        }
    """)
    g.kernel = """
        vec2 kernel() {
            v_col = vec4(0, 1, 1, 1);
            gl_PointSize = 3;
            return vec2(${domain.x}, ${domain.t}(${domain.y}(${domain.x}/15)));
        }
    """

    plotter += g


    f = lambda x: 0.1*x*np.cos(x) 
    h = lambda x: 0.1*x*np.sin(x)
    c = lambda x: np.sin(2*x)**2
    d = lambda x: 3+2*np.cos(5*x)*np.sin(2*x)
    data = np.array([(f(x),h(x),c(x),d(x)) for x in np.arange(0, 100, .1)], dtype=np.float32)

    g = graph.glpoints.GlPointsGraph(domain.TextureDomain.to_device_1d(data), kernel="""
        vec2 kernel() {
            vec4 d = ${DOMAIN}(${domain.arg});
            ${SIZE} = d.w;
            ${COLOR} = vec4(0.5+0.5*d.z, d.z, 1-d.z, d.w/5);
            return vec2(2,2) + d.xy/5;
        }
    """)
    g['arg'] = domain.VertexDomain(np.arange(0, 1, .0001, dtype=np.float32))
    plotter += g

    keksnioh = domain.TextureDomain.colorwheel('keksnicoh')
    def upper_right(cs):
        return (cs[1]-(cs[1]-cs[0])*0.25, cs[1], cs[3]-(cs[3]-cs[2])*0.25, cs[3])
    plotter += graph.frgfnc.Frag2DGraph(keksnioh, cs=plotter.cs.observe(upper_right))

if __name__ == '__main__':
    plot()