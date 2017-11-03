#-*- coding: utf-8 -*-
"""
graphs are widgets which have the following properties:


---
not defined yet. still in experiment.


:author: keksnicoh
"""

from gpupy.gl.lib import attributes
from gpupy.gl import components, Program, Shader, GPUPY_GL as G_
from gpupy.plot.domain import safe_name
from OpenGL.GL import * 

from collections import OrderedDict
import os

class DomainGraph(components.widgets.Widget):
    """ 
    abstract class for graphs which are using
    the domain concept for plotting data. 

    """

    DEFAULT_DOMAIN_NAME = 'domain'

    resolution = attributes.VectorAttribute(2, (1, 1))
    viewport = attributes.VectorAttribute(2, (1, 1))

    def __init__(self, domain=None):
        """
        initializes the graph with one or many domains. 
        argument domain is an dict, it is interpreted as 
        (key, domain) pairs.
        """
        super().__init__()
        self.domains = OrderedDict()

        if isinstance(domain, dict):
            for k, v in domain.items():
                self[k] = v
        elif domain is not None:
            self[DomainGraph.DEFAULT_DOMAIN_NAME] = domain 


    def __setitem__(self, key, domain):
        """
        adds a domain to the graph
        """
        safe_name(key)
        domain.requires(list(self.domains.keys()))
        self.domains[key] = _DomainInfo(domain, 'd_{}'.format(key))


    def __getitem__(self, key):
        """
        returns a domain by key
        """
        return self.domains[key].domain


    def get_domain_glsl_substitutions(self):
        """
        returns a list of tuples 
          (glsl_substitution, glsl_identifier)

        where glsl_substitution is the name of the
        substitution e.g. ${name}
        """
        domain_sfnames = {}
        for dname, domain in self.domains.items():
            for field, glsl_id, glsl_meta, glsl_type in domain.glsl_identifier:
                substkey = 'D.'+dname
                if field is not None:
                    substkey += '.{}'.format(field)
                domain_sfnames.update({substkey: glsl_id})
        return domain_sfnames


    def _enable_domain_attrib_pointers(self):
        """
        enable all vertex attribute pointers
        from domains
        """
        for domain_info in self.domains.values():
            domain = domain_info.domain
            if hasattr(domain, 'attrib_pointers'):
                domain.attrib_pointers(domain_info.prefix, self.program.attributes)

class _DomainInfo():
    def __init__(self, domain, prefix):
        self.prefix = prefix 
        self.domain = domain

    @property
    def glsl_identifier(self):
        return self.domain.glsl_identifier(self.prefix)

    

class DomainProgram(Program):
    def __init__(self, vrt_file=None, frg_file=None):
        super().__init__()
        if vrt_file is not None:
            vert_path = os.path.join(os.path.dirname(__file__), vrt_file)
            vert_shader = Shader(GL_VERTEX_SHADER, open(vert_path).read())
            self.shaders.append(vert_shader)
        if frg_file is not None:
            frag_path = os.path.join(os.path.dirname(__file__), frg_file)
            frag_shader = Shader(GL_FRAGMENT_SHADER, open(frag_path).read())
            self.shaders.append(frag_shader)

    def prepare_domains(self, domains):
        
        frg_shader = self.get_shader(GL_FRAGMENT_SHADER)
        vrt_shader = self.get_shader(GL_VERTEX_SHADER)

        # -- domain name substitutions
        #
        # ${domain-name}         domain is scalar
        # ${domain-name}.key     domain is structurized
        #
        # note that substitutions might be available in multiple
        # shader stages (vertex, fragment, geo, ...). 
        domain_sfnames = {}
        for dname, _d in domains.items():
            for field, glsl_id, glsl_meta, glsl_type in _d.glsl_identifier:
                substkey = dname
                if field is not None:
                    substkey += '.{}'.format(field)
                domain_sfnames.update({substkey: glsl_id})

        frg_shader.substitutions.update(domain_sfnames)
        vrt_shader.substitutions.update(domain_sfnames)

        # -- GLSL code generation
        glsl_subst = {'glsl_declr': [], 'glsl_attr': []}
        for dname, _d in domains.items():
            domain = _d.domain
            if hasattr(domain, 'glsl_declr'):
                glsl_subst['glsl_declr'].append(domain.glsl_declr(upref=_d.prefix))
            if hasattr(domain, 'glsl_attributes'):
                glsl_subst['glsl_attr'].append(domain.glsl_attributes(_d.prefix))

        frg_shader.substitutions.update({k: '\n'.join(v) for k, v in glsl_subst.items()})
        vrt_shader.substitutions.update({k: '\n'.join(v) for k, v in glsl_subst.items()})
