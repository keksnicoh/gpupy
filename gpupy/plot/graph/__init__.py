#-*- coding: utf-8 -*-
"""
graphs are widgets which have the following properties:

XXX
---
not defined yet. still in experiment.

:author: keksnicoh
"""

from gpupy.gl.common import attributes
from gpupy.gl import components, Program

from OpenGL.GL import * 

from collections import OrderedDict

class DomainGraph(components.widgets.Widget):
    """ abstract class for graphs which are using
        the domain concept for plotting data. """

    main_domain = attributes.CastedAttribute(str)

    def __init__(self, domain=None):
        self.domains = OrderedDict()
        self.main_domain = None
        if domain is not None:
            self['domain'] = domain 

    def __setitem__(self, key, value):
        value.requires({n: d[0] for n, d in self.domains.items()})
        self.domains[key] = (value, 'd_'+key)
        if len(self.domains) == 1 and self.main_domain is None:
            self.main_domain = key

class DomainProgram(Program):
    def prepare_domains(self, domains):
        frg_shader = self.get_shader(GL_FRAGMENT_SHADER)

        domain_sfnames = {'DOMAIN:{}'.format(dname): d[1] for dname, d in domains.items()}
        domain_fnames = {dname: d[1] for dname, d in domains.items()}
        frg_shader.substitutions.update(domain_sfnames)

        frg_subst = {'frg_declr': [], 'frg_domain': []}
        for prefix, (domain, fname) in domains.items():
            if hasattr(domain, 'glsl_frg_declr'):
                frg_subst['frg_declr'].append(domain.glsl_frg_declr(prefix))
            if hasattr(domain, 'glsl_frg_domain'):
                frg_subst['frg_domain'].append(domain.glsl_frg_domain(fname=fname, upref=prefix, domain_fnames=domain_fnames))
    
        frg_shader.substitutions.update({
            'frg_declr': '\n'.join(frg_subst['frg_declr']),
            'frg_domain': '\n'.join(frg_subst['frg_domain']),
        })
       # self.texture.interpolation_linear()
    #   self.domains['texture'][0].enable(0)
    #    self.domains['texture'][0].uniforms(self.program, upref='texture')
    #    self.domains['blurp'][0].enable(1)
    #    self.domains['blurp'][0].uniforms(self.program, upref='texture')
     #   self.program.uniform('tex', self.texture)