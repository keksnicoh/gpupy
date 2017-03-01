#-*- coding: utf-8 -*-
"""
graphs are widgets which have the following properties:

XXX
---
not defined yet. still in experiment.

:author: keksnicoh
"""

from gpupy.gl.common import attributes
from gpupy.gl import components, Program, GPUPY_GL as G_

from OpenGL.GL import * 

from collections import OrderedDict

class DomainGraph(components.widgets.Widget):
    """ abstract class for graphs which are using
        the domain concept for plotting data. """

    main_domain = attributes.CastedAttribute(str)
    resolution = attributes.VectorAttribute(2, (1, 1))
    viewport = attributes.VectorAttribute(2, (1, 1))

    def __init__(self, domain=None):
        super().__init__()
        self.domains = OrderedDict()
        self.main_domain = None
        if domain is not None:
            self['domain'] = domain 

    def __setitem__(self, key, value):
        value.requires({n: d[0] for n, d in self.domains.items()})
        self.domains[key] = (value, 'd_'+str(key))
        if len(self.domains) == 1 and self.main_domain is None:
            self.main_domain = key

    def __getitem__(self, key):
        return self.domains[key][0]


class DomainProgram(Program):
    def prepare_domains(self, domains):
        frg_shader = self.get_shader(GL_FRAGMENT_SHADER)
        vrt_shader = self.get_shader(GL_VERTEX_SHADER)

        domain_sfnames = {'DOMAIN:{}'.format(dname): d[1] for dname, d in domains.items()}

        domain_fnames = {dname: d[1] for dname, d in domains.items()}
        frg_shader.substitutions.update(domain_sfnames)
        vrt_shader.substitutions.update(domain_sfnames)

        frg_subst = {
            'glsl_header': [], 
            'glsl_declr': [],
            'vrt_declr': [],
            'vrt_domain': [],
        }
        for prefix, (domain, fname) in domains.items():
            if hasattr(domain, 'glsl_header'):
                frg_subst['glsl_header'].append(domain.glsl_header(prefix))
            if hasattr(domain, 'glsl_declr'):
                frg_subst['glsl_declr'].append(domain.glsl_declr(fname=fname, upref=prefix, domain_fnames=domain_fnames))
            if hasattr(domain, 'glsl_vrt_declr'):
                frg_subst['vrt_declr'].append(domain.glsl_vrt_declr(fname))
            if hasattr(domain, 'glsl_vrt_domain'):
                frg_subst['vrt_domain'].append(domain.glsl_vrt_domain(fname))

        frg_shader.substitutions.update({k: '\n'.join(v) for k, v in frg_subst.items()})
        vrt_shader.substitutions.update({k: '\n'.join(v) for k, v in frg_subst.items()})

    def link(self):
        super().link()
        def _clean(src):
            return '\n'.join(l for l in src.split('\n') if len(l.strip()))
        G_.debug('compiled domain program')
        G_.debug('--------VERTEX------------')
        G_.debug(_clean(self.get_shader(GL_VERTEX_SHADER)._precompiled_source))
        G_.debug('--------FRAGMENT----------')
        G_.debug(_clean(self.get_shader(GL_FRAGMENT_SHADER)._precompiled_source))

       # self.texture.interpolation_linear()
    #   self.domains['texture'][0].enable(0)
    #    self.domains['texture'][0].uniforms(self.program, upref='texture')
    #    self.domains['blurp'][0].enable(1)
    #    self.domains['blurp'][0].uniforms(self.program, upref='texture')
     #   self.program.uniform('tex', self.texture