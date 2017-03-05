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

from OpenGL.GL import * 

from collections import OrderedDict

class GraphTick():
    def __init__(self):
        self.require_render = True

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

        glsl_subst = {
            'glsl_declr': [],
            'glsl_attr': [],
        }
        for prefix, (domain, fname) in domains.items():
            if hasattr(domain, 'glsl_declr'):
                glsl_subst['glsl_declr'].append(domain.glsl_declr(fname=fname, upref=prefix, domain_fnames=domain_fnames))
            if hasattr(domain, 'glsl_attributes'):
                glsl_subst['glsl_attr'].append(domain.glsl_attributes(fname))


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