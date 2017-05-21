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
from gpupy.gl.glsl import Template

from OpenGL.GL import *
import numpy as np

class FragmentGraph(DomainGraph):

    DEFAULT_FRAGMENT_KERNEL = """
        vec4 fragment_kernel(vec2 txcoord) {
            return tovec4($D.domain(txcoord));
        }
    """


    FRAGMENT_KERNELS = {
        'expr': lambda e: "vec4 fragment_kernel(vec2 txcoord) { return "+e+"; }",
    }
    cs = attributes.VectorAttribute(4)

    # main domain name 
    fragment_kernel = attributes.CastedAttribute(str)

    def __init__(self, domain=None, 
                       cs=None, 
                       fragment_kernel=None):

        super().__init__(domain)

        self.cs = cs

        if 'domain' in self.domains:
            self.fragment_kernel = fragment_kernel or self.DEFAULT_FRAGMENT_KERNEL
        elif fragment_kernel is None:
            raise ValueError('argument fragment_kernel cannot be None without default domain')
        else:
            self.fragment_kernel = fragment_kernel

        self.mesh = None
        self.program = None 
        self._fkernel_template = None

    def init(self):
        self._build_kernel()
        self.program = self._build_shader()
        self.mesh = StridedVertexMesh(mesh3d_rectangle(), 
                                      GL_TRIANGLES, 
                                      attribute_locations=self.program.attributes)
        self.on_tick.once(self.sync_gpu)

    @cs.on_change
    def _properties_changed(self, *e):
        self.on_tick.once(self.sync_gpu)

    def _build_kernel(self):
        context = self.get_domain_glsl_substitutions()
        kernel = Template(self.fragment_kernel, context)
        kernel.context.update({
            'size': 'gl_PointSize',
            'color': 'v_col'})
        self._fkernel_template = kernel

    def _build_shader(self):
        prg = DomainProgram(vrt_file='fragmentgraph.vrt.glsl',
                            frg_file='fragmentgraph.frg.glsl')

        prg.declare_uniform('camera', components.camera.Camera2D.DTYPE, variable='camera')
        prg.declare_uniform('plot',   plotter2d.Plotter2d.UBO_DTYPE,    variable='plot')

        prg.prepare_domains(self.domains)
        prg.get_shader(GL_FRAGMENT_SHADER).substitutions.update({
            'fragment_kernel': self._fkernel_template.render(),
        })
        prg.link()
        prg.uniform_block_binding('plot',   G_.CONTEXT.buffer_base('gpupy.plot.plotter2d'))
        prg.uniform_block_binding('camera', G_.CONTEXT.buffer_base('gpupy.gl.camera'))

        self._src = prg.get_shader(GL_FRAGMENT_SHADER)._precompiled_source
        return prg

    def sync_gpu(self):
        cs = self.cs.values
        self.program.uniform('cs', cs)
        self.program.uniform('cs_size', (np.abs(cs[1]-cs[0]), np.abs(cs[3]-cs[2])))

    def render(self):
        # enable all domains
        domain.enable_domains(self.program, self.domains.items())

        # blending 
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)

        # draw mesh
        self.program.use()
        self.mesh.draw()
        self.program.unuse()

    @fragment_kernel.transformation 
    def set_color_kernel(self, ckrn):
        kernels = self.__class__.FRAGMENT_KERNELS
        ckrn_args, ckrn_kwargs = (), {}

        # we have ('kernel_name', ***)
        # i   ('kernel_name', {kwargs})          --> kernel(**kwargs)
        # ii  ('kernel_name', [args])            --> kernel(*args)
        # iii ('kernel_name', (args))            --> kernel(*args)
        # iv  ('kernel_name', (args), {kwargs})  --> kernel(*args, **kwargs)
        # v   ('kernel_name', x, y, z, ...)      --> kernel(x, y, z, ...)
        if isinstance(ckrn, tuple) \
        or isinstance(ckrn, list):
            if len(ckrn) == 2: # i - iii
                if isinstance(ckrn[1], dict):  
                    ckrn_kwargs = ckrn[1]
                elif isinstance(ckrn[1], tuple) \
                  or isinstance(ckrn[1], list):
                    ckrn_args = ckrn[1]
                else:
                    ckrn_args = (ckrn[1], )
            elif len(ckrn) == 3 \
             and isinstance(ckrn[2], dict) \
             and (isinstance(ckrn[1], tuple) 
               or isinstance(ckrn[1], list)):
                ckrn_args, ckrn_kwargs = ckrn[1:3] # iv
            elif len(ckrn) > 1: 
                ckrn_args = ckrn[1:] # v
            ckrn = ckrn[0]

        # if ckrn is registred, use it.
        if ckrn in kernels:
            ckrn = kernels[ckrn]

        # is it callable?
        if hasattr(ckrn, '__call__'):
            ckrn = ckrn(*ckrn_args, **ckrn_kwargs)
        elif len(ckrn_args) or len(ckrn_kwargs):
            msg = 'kernel {} is not callable, but kernel args (), kwargs () are defined.'
            raise RuntimeError(msg.format(ckrn, ckrn_args, ckrn_kwargs))
        return ckrn

#XXX rescue some old stufff
#
#    'greyscale_avg': """
#        vec4 color(float x) { return vec4(x, x, x, 1); }
#        vec4 color(vec2 x)  { return vec4(x.x+x.y, x.x+x.y, x.x+x.y, 2) / 2; }
#        vec4 color(vec3 x)  { return vec4(x.x+x.y+x.z, x.x+x.y+x.z, x.x+x.y+x.z, 3) / 3; }
#        vec4 color(vec4 x)  { return vec4(x.x+x.y+x.z, x.x+x.y+x.z, x.x+x.y+x.z, 3*x.w) / 3; }
#    """,
#    'greyscale_lightness': """
#        vec4 color(float x) { return vec4(x, x, x, 1); }
#        vec4 color(vec2 x)  { float M = max(x.x, x.y); float m = min(x.x, x.y); return vec4(m+M, m+M,m+M,2)/2; }
#        vec4 color(vec3 x)  { float M = max(x.x, max(x.y, x.z)); float m = min(x.x, min(x.y, x.z)); return vec4(m+M, m+M,m+M,2)/2; }
#        vec4 color(vec4 x)  { float M = max(x.x, max(x.y, x.z)); float m = min(x.x, min(x.y, x.z)); return vec4(m+M, m+M,m+M,2)/2; }
#    """,
#    'greyscale_luminosity': """
#        vec4 color(float x) { return vec4(x, x, x, 1); }
#        vec4 color(vec2 x)  { float _r=0.245*x.x+0.755*x.y; return vec4(_r, _r, _r, 1); }
#        vec4 color(vec3 x)  { float _r=0.21*x.x+0.72*x.y+0.07*x.z; return vec4(_r, _r, _r, 1); }
#        vec4 color(vec4 x)  { float _r=0.21*x.x+0.72*x.y+0.07*x.z; return vec4(_r, _r, _r, x.w); }
#    """,


