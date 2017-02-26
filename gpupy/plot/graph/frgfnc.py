#-*- coding: utf-8 -*-
"""
graphs are widgets which have the following properties:

XXX
---
not defined yet. still in experiment.

:author: keksnicoh
"""
from . import DomainGraph, DomainProgram

from gpupy.plot import domain, plotter2d

from gpupy.gl.mesh import StridedVertexMesh, mesh3d_rectangle
from gpupy.gl.common import attributes
from gpupy.gl import GPUPY_GL as G_, Shader, components

from OpenGL.GL import *

from collections import OrderedDict
import os 

class Frag1DGraph(DomainGraph):
    """ 
    plots a 1d domain onto a plane using fragment shades.
    """
    DEFAULT_COLOR_KERNEL = 'test'

    configuration_space = attributes.VectorAttribute(4)
    frame               = attributes.ComponentAttribute()

    # main domain name 
    color_kernel = attributes.CastedAttribute(str)

    @classmethod
    def glsl_transformation(cls, glsl_expr, **kwargs):
        glsl = "float ${FNAME}(float x) { return " + str(glsl_expr) + "; }"
        return cls(domain.FragmentTransformationDomain(glsl), **kwargs)

    def __init__(self, domain=None, color_kernel=None):
        self.x_space = [0, 1]
        self.program = None 
        self.color_kernel = color_kernel or self.__class__.DEFAULT_COLOR_KERNEL  
        super().__init__(domain)


    def init(self):
        self._build_shader()
        self.mesh = StridedVertexMesh(mesh3d_rectangle(), 
                                      GL_TRIANGLES, 
                                      attribute_locations=self.program.attributes)
        self.program.uniform('u_x_space', self.x_space)

    def _build_shader(self):
        self.program = _p = DomainProgram()

        vert_path = os.path.join(os.path.dirname(__file__), 'frgfnc.vrt.glsl')
        _p.shaders.append(Shader(GL_VERTEX_SHADER, open(vert_path).read()))

        frg_path = os.path.join(os.path.dirname(__file__), 'frgfnc.frg.glsl')
        frg_src = open(frg_path).read().replace('${MAIN_DOMAIN}', self.main_domain)
        _p.shaders.append(Shader(GL_FRAGMENT_SHADER, frg_src))
        
        _p.declare_uniform('camera', components.camera.Camera2D.DTYPE, variable='camera')
        _p.declare_uniform('plot', plotter2d.Plotter2d.UBO_DTYPE, variable='plot')

        _p.prepare_domains(self.domains)
        _p.get_shader(GL_FRAGMENT_SHADER).substitutions.update({
            'clr_kernel': self.color_kernel,
        })
        _p.link()
            
        _p.uniform_block_binding('plot', G_.CONTEXT.buffer_base('gpupy.plot.plotter2d'))
        _p.uniform_block_binding('camera', G_.CONTEXT.buffer_base('gpupy.gl.camera'))


    @color_kernel.transformation 
    def set_color_kernel(self, ckrn):
        ckrn_args, ckrn_kwargs = (), {}

        # we have ('kernel_name', ***)
        # i   ('kernel_name', {kwargs})          --> kernel(**kwargs)
        # ii  ('kernel_name', [args])            --> kernel(*args)
        # iii ('kernel_name', (args))            --> kernel(*args)
        # iv  ('kernel_name', (args), {kwargs})  --> kernel(*args, **kwargs)
        # v   ('kernel_name', x, y, z, ...)      --> kernel(x, y, z, ...)
        if isinstance(ckrn, tuple) or isinstance(ckrn, list):
            if len(ckrn) == 2: # i - iii
                if isinstance(ckrn[1], dict):  
                    ckrn_kwargs = ckrn[1]
                elif isinstance(ckrn[1], tuple) or isinstance(ckrn[1], list):
                    ckrn_args = ckrn[1]
                else:
                    ckrn_args = (ckrn[1], )
            elif len(ckrn) == 3 \
             and isinstance(ckrn[2], dict) \
             and (isinstance(ckrn[1], tuple) or isinstance(ckrn[1], list)):
                ckrn_args, ckrn_kwargs = ckrn[1:3] # iv
            elif len(ckrn) > 1: 
                ckrn_args = ckrn[1:] # v
            ckrn = ckrn[0]

        # if ckrn is registred, use it.
        if ckrn in COLOR_KERNELS:
            ckrn = COLOR_KERNELS[ckrn]

        # is it callable?
        if hasattr(ckrn, '__call__'):
            ckrn = ckrn(*ckrn_args, **ckrn_kwargs)
        elif len(ckrn_args) or len(ckrn_kwargs):
            msg = 'kernel {} is not callable, but kernel args (), kwargs () are defined.'
            raise RuntimeError(msg.format(ckrn, ckrn_args, ckrn_kwargs))
        return ckrn


    def draw(self):
        self.program.use()
        self.mesh.draw()
        self.program.unuse()


test_color_kernel = """
vec4 color(vec2 fc,      // fragment coords (in plane: [0,1]x[0,1])
           float sd,     // signed distance
           float xsd) {  // signed distance relative to x-axis
    if (xsd > 0) { discard; }
    return vec4(fc.y+0.5, 0, 1-fc.y-.5, exp(-2*abs(xsd))); 
}
"""

def expr_ckern(expr):
    return "vec4 color(vec2 fc, float sd, float xsd) {  return "+expr+"; }"

def glsl_fbody(expr):
    return "vec4 color(vec2 fc, float sd, float xsd) {  "+expr+" }"

COLOR_KERNELS = {
    'test': test_color_kernel,
    'expr': expr_ckern,
    'function': glsl_fbody,
}
