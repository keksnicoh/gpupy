#-*- coding: utf-8 -*-
"""
example creates a glprimitives graph over x axis.
y values are sampled from a random function domain within
the vertex shader.

:author: keksnicoh
"""

from gpupy.plot import plot2d
from gpupy.plot.domain import arange, random
from gpupy.plot.graph.glprimitives import GlPrimitivesGraph 

@plot2d 
def plot(plotter):

    plotter += GlPrimitivesGraph({
        # domain on [0, 1] will be projected onto full cs
        # x-axes by using shader function cartesian_x
        'x': arange(0, 1, 0.00001),

        # random domain
        'rand': random(timeseed=False),

    }, kernel="""vec2 kernel() { 
        // point pixel size
        $size = 2;

        // extend vertex domain over x axis
        float x = cartesian_x($D.x);

        // colorize 
        $color = vec4(1 - $D.rand(x), 1, $D.rand(x), 1);

        // vertex coords
        return vec2(x, $D.rand(x));
    }""")

    
if __name__ == '__main__':
    plot()