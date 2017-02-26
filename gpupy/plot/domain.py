from gpupy.gl.common import attributes

from OpenGL.GL import * 

import re

class DomainError(Exception): pass
class DependencyError(DomainError): pass

class TextureDomain():
    """

    Allows to use gpupy.gl.texture's as plot 
    domains. 

    """
    # -- GLSL templates
    _GLSL_TEMPLATE_DOMAIN = """
        {fname:}({arg_type:} x) {{
            return texture(tx_{upref:}, x).{rgba:};
        }}
    """

    _GLSL_TEMPLATE_DECRL = "uniform sampler{d:}D tx_{upref:};"

    # -- attributes
    texture = attributes.GlTexture()

    def __init__(self, texture):
        self.texture = texture 

    def enable(self, n=0):
        self.texture.activate(n)

    def uniforms(self, program, upref):
        program.uniform('tx_{}'.format(upref), self.texture)

    def glsl_frg_domain(self, fname, upref, **kwargs):
        # XXX
        # - what about other vector types?
        c = self.texture.channels
        ret_type = 'float' if c == 1 else 'vec{}'.format(c)
        rgba = 'rgba'[0:c]
        d = self.texture.dimension
        arg_type = 'float' if d == 1 else 'vec{}'.format(d)
        tmpl = self.__class__._GLSL_TEMPLATE_DOMAIN
        return tmpl.format(ret_type=ret_type, 
                           arg_type=arg_type, 
                           fname=fname, 
                           rgba=rgba,
                           upref=upref)

    def glsl_frg_declr(self, upref):
        d = self.texture.dimension
        return self.__class__._GLSL_TEMPLATE_DECRL.format(d=d, upref=upref)

    def requires(self, domains):
        return set()

class FragmentTransformationDomain():
    """ 

    domain generated within fragment shader.
    note that this domain requires one calculation of the
    data on for each rendering. 

    this should be used

    a) to see some quick results
    b) to combine other fragment domains with an expression.

    """
    def __init__(self, glsl):
        self.glsl = glsl

    def glsl_frg_domain(self, fname, domain_fnames, **kwargs):
        glsl = str(self.glsl) 
        subst = {'${FNAME}': fname}
        subst.update({'${{DOMAIN:{}}}'.format(n): v for n, v in domain_fnames.items()})
        for k, v in subst.items():
            glsl = glsl.replace(k, v)
        return glsl

    def requires(self, domains):
        res = set(re.findall('\$\{DOMAIN:(.*?)\}', str(self.glsl)))
        frg_dom_names = set(name for name, d in domains.items() if hasattr(d, 'glsl_frg_domain'))
        if len(res - frg_dom_names):
            raise DependencyError('requires fragment domains: {}'.format(','.join(frg_dom_names)))