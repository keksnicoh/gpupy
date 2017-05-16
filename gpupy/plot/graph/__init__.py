#-*- coding: utf-8 -*-
"""
graphs are widgets which have the following properties:


---
not defined yet. still in experiment.


Graph api:

properties:
- plotter: if exists, a plotter will assign itself
  to this attribute to ensure that the graph can
  only be attached to a single plotter. 
  Graphs which can be rendered within many
  plotters should not have this attribute.

- plot_type: to check if a certain graph type
  is supported by a plotter.

    plt2d : standard 2d plot
    plt3d : standard 3d plot

  should be an array.

:author: keksnicoh
"""

from gpupy.gl.common import attributes
from gpupy.gl import components, Program, GPUPY_GL as G_
from gpupy.plot.domain import safe_name
from OpenGL.GL import * 

from collections import OrderedDict

class GraphTick():
    def __init__(self):
        self.require_render = True

class _DomainInfo():
    def __init__(self, domain, prefix):
        self.prefix = prefix 
        self.domain = domain

    @property
    def glsl_identifier(self):
        return self.domain.glsl_identifier(self.prefix)
    

class Graph(components.widgets.Widget):

    resolution = attributes.VectorAttribute(2, (1, 1))
    viewport = attributes.VectorAttribute(2, (1, 1))

    def __init__(self):
        super().__init__()


    def tick(self, gtick):
        self.on_pre_tick(gtick)
        self.gtick(gtick)
        self.on_post_tick(gtick)

    def render(self):
        pass

    def gtick(self, gtick):
        pass


class DomainGraph(Graph):
    """ abstract class for graphs which are using
        the domain concept for plotting data. """

    main_domain = attributes.CastedAttribute(str)

    def __init__(self, domain=None):
        super().__init__()
        self.domains = OrderedDict()
        self.main_domain = None
        if domain is not None:
            self['domain'] = domain 

    def __setitem__(self, key, domain):
        safe_name(key)
        domain.requires(list(self.domains.keys()))
        self.domains[key] = _DomainInfo(domain, 'd_{}'.format(key))
        if len(self.domains) == 1 and self.main_domain is None:
            self.main_domain = key

    #    handler = self._domain_changed 
    #    event = observable_event(value)
    #    if event is not None and handler not in event:
    #        event.append(handler)

    def _domain_changed(self, domain):
        pass

    def __getitem__(self, key):
        return self.domains[key].domain


class DomainProgram(Program):
    def prepare_domains(self, domains):
        frg_shader = self.get_shader(GL_FRAGMENT_SHADER)
        vrt_shader = self.get_shader(GL_VERTEX_SHADER)

        # domain name substitutions
        domain_sfnames = {}
        for dname, _d in domains.items():
            print(_d.glsl_identifier)
            for ident, glsl_id, glsl_meta, glsl_type in _d.glsl_identifier:
                dname = [dname]
                if ident is not None:
                    dname.append(ident)
                domain_sfnames.update({'domain.{}'.format('.'.join(dname)): glsl_id})
        frg_shader.substitutions.update(domain_sfnames)
        vrt_shader.substitutions.update(domain_sfnames)

        # domain code substitutions
        glsl_subst = {'glsl_declr': [], 'glsl_attr': []}
        for dname, _d in domains.items():
            domain = _d.domain
            if hasattr(domain, 'glsl_declr'):
                glsl_subst['glsl_declr'].append(domain.glsl_declr(upref=_d.prefix))
            if hasattr(domain, 'glsl_attributes'):
                glsl_subst['glsl_attr'].append(domain.glsl_attributes(_d.prefix))
        frg_shader.substitutions.update({k: '\n'.join(v) for k, v in glsl_subst.items()})
        vrt_shader.substitutions.update({k: '\n'.join(v) for k, v in glsl_subst.items()})

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