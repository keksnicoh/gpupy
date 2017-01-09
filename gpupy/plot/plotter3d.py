



plot = Plotter2d(camera.size)
plot.origin = (0, 1)
plot.configuration_space = [2, 2*pi]
plot.settings['axis.w'] = 'log'
plot.settings['axis.s'] = True
plot.settings['grid'] = True

plot.add_graph(Line2D(), domains=[x,y])
plot.add_graph(domains={'xy': xy}, transformation="y=xy.x/xy.y")
plot.add_graph(domains={'x': x, 'y': y}, transformation="codomain=x/y;", value="val")



class GraphLineProgram():
    VERTEX_SHADER = """
        ${header}
        ${variables}
        ${domains}
        void main() {
            gl_Position = ${transformation_vertex};
            color = ${transformation_color};
        }
    """

    GEOMETRY_SHADER = """

    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        se


domains={''}, transformations={''}, variables={''}



domains={'x': IntervalDomain([0,1])}, 
               transformations={
                    'transformation': (
                        'transformation.x * x', 
                        'sampler(y, vec2(x, y))'
                    ),
                    'color': {

                    }
               },

               variables={'y': 0})






plot.graph(x,y)
plot.glsl_function(x, "y=sin(x)")
plot.plot()
