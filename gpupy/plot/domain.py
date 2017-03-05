#-*- coding: utf-8 -*-
"""
domain module provides an abstraction layer 
for plot domains. 
:author: keksnicoh
"""

# XXX
# - generic domain names? prefixes...

from gpupy.gl.common import attributes, imread
from gpupy.gl.glsl import dtype_is_struct, dtype_vector, dtype_fields_glsl
from gpupy.gl import Texture3D, Texture2D, Texture1D

from OpenGL.GL import * 
import numpy as np 

from ctypes import c_void_p
import re
import os
from time import time

class DomainError(Exception): 
    pass
class DependencyError(DomainError): 
    pass
class DomainNameError(DomainError): 
    pass

_name_rgx = re.compile('^[a-zA-Z_][a-zA-Z_0-9]*$') #XXX think more about this...
def safe_name(name):
    if not _name_rgx.match(name):
        raise DomainNameError('invaid domain name "{}"'.format(name))
    return name

class AbstractDomain():
    """
    basic domain API
    """
    # ON CHANGE EVENT

    def requires(self, domains):
        """
        checks whether all required domains are available.
        if not, this method should raise a DependencyError.
        """
        pass

    def enable(self, txunits, program, upref):
        """
        enables the domain such that the shadering
        pipeline is setup
        """
        pass


class SequencialDomain(AbstractDomain):
    """
    defines the API for discrete domains like
    vertex attributes
    """
    def glsl_attributes(self):
        """
        returns the glsl attribute declaration
        """
        raise NotImplementedError('abstract method')  

    def attribute_pointers(self, aname, attr_locations):
        """
        binds vertex attribute pointers to the currently
        bound VAO
        """
        raise NotImplementedError('abstract method') 

    def __len__(self):
        """
        we should always know the length of the series.
        """
        raise NotImplementedError('abstract method')

class ContinuousDomain(AbstractDomain):
    """
    defines the API for a continuos domain like
    functions or texture samplers.
    """
    def glsl_declr(self, fname, upref, **kwargs):
        """
        returns the glsl declrations 
        """
        raise NotImplementedError('abstract method') 
    


class VertexDomain(SequencialDomain):
    """
    vertex domain provides vertex attributes for 
    glsl shader by a given BufferObject
    """
    buffer = attributes.BufferObjectAttribute()

    def __init__(self, data):
        self.buffer = data

    # -- sequencial domain API 

    def glsl_attributes(self, aname):
        shape = self.buffer.shape
        dtype = self.buffer.dtype

        if dtype_is_struct(dtype):
            glsl_fields = dtype_fields_glsl(dtype)
            tmpl = 'in {gltype:} {aname:}_{field:};'
            return '\n'.join(tmpl.format(gltype=t, field=f, aname=aname) for t, f in glsl_fields)
        else:
            # XXX support matrix?
            oshape = shape
            if len(shape) == 1:
                shape = (shape, 1)
            gltype = dtype_vector(dtype, shape[1])
            return "in {gltype:} {aname:};".format(gltype=gltype, aname=aname)

    def attrib_pointers(self, aname, attribute_locations):
        buff = self.buffer
        buff.bind()

        # dtype is a structure => strided
        if dtype_is_struct(buff.dtype):
            dom_attrs = [(d[0], aname+'_'+d[0]) for d in buff.dtype.descr]
            for field, attr in dom_attrs:
                sdtype = buff.dtype[field].subdtype is None
                components = 1 if sdtype else buff.dtype[field].subdtype[1][0]
                glVertexAttribPointer(attribute_locations[attr], 
                                      components, 
                                      GL_FLOAT, 
                                      GL_FALSE, 
                                      buff.dtype.itemsize, 
                                      c_void_p(buff.dtype.fields[field][1]))
                glEnableVertexAttribArray(attribute_locations[attr])

        # vector buffer
        else:
            dim = buff.shape[1] if len(buff.shape) > 1 else 1
            glVertexAttribPointer(attribute_locations[aname], 
                                  dim, 
                                  GL_FLOAT, 
                                  GL_FALSE, 
                                  0, 
                                  None)
            glEnableVertexAttribArray(attribute_locations[aname]) 

    def __len__(self):
        return len(self.buffer)


class TextureDomain(ContinuousDomain):
    """

    Allows to use gpupy.gl.texture's as plot 
    domains. 

    """
    # -- GLSL templates
    _GLSL_TEMPLATE_DOMAIN = """
        {ret_type:} {fname:}({arg_type:} x) {{
            return texture(tx_{upref:}, x).{rgba:};
        }}
    """

    _GLSL_TEMPLATE_DECRL = "uniform sampler{d:}D tx_{upref:};"

    WHEELS = {
        'complex': os.path.join(os.path.dirname(__file__), 'graph', 'res', 'cwheel_cmplx.jpg'),
        'keksnicoh': os.path.join(os.path.dirname(__file__), 'graph', 'res', 'keksnicoh.png'),
    }

    DEFAULT_WHEEL = 'complex'

    # -- attributes
    texture = attributes.GlTexture()
    cs = attributes.VectorAttribute(4, (0, 1, 0, 1))

    @classmethod
    def load_image(cls, path, smooth=True, periodic=False):
        txt = imread(path, mode="RGB")
        d = cls(Texture2D.to_device(txt))
        d.periodic(periodic)
        d.smooth(smooth)
        return d

    @classmethod
    def colorwheel(cls, wheel=DEFAULT_WHEEL):
        if wheel not in cls.WHEELS:
            err = 'unkown wheel "{}". Available wheels: {}'
            raise ValueError(err.format(wheel, ','.join(cls.WHEELS)))
        return cls.load_image(cls.WHEELS[wheel])

    @classmethod
    def to_device_1d(cls, data, smooth=True, periodic=False):
        d = cls(Texture1D.to_device(data))
        d.periodic(periodic)
        d.smooth(smooth)
        return d

    @classmethod
    def to_device_2d(cls, data, smooth=True, periodic=False):
        d = cls(Texture2D.to_device(data))
        d.periodic(periodic)
        d.smooth(smooth)
        return d

    @classmethod
    def to_device_3d(cls, data, smooth=True, periodic=False):
        d = cls(Texture3D.to_device(data))
        d.periodic(periodic)
        d.smooth(smooth)
        return d

    # -- 

    def __init__(self, texture, cs=None):
        self.texture = texture 
        if cs is not None:
            self.cs = cs

    def periodic(self, periodic=False):
        if periodic:
            self.texture.tex_parameterf(GL_TEXTURE_WRAP_S, GL_REPEAT)
            self.texture.tex_parameterf(GL_TEXTURE_WRAP_T, GL_REPEAT)
        else:
            self.texture.tex_parameterf(GL_TEXTURE_WRAP_S, GL_CLAMP_TO_EDGE)
            self.texture.tex_parameterf(GL_TEXTURE_WRAP_T, GL_CLAMP_TO_EDGE)

    def smooth(self, smooth=True):
        if smooth:
            self.texture.interpolate_linear()
        else:
            self.texture.interpolate_nearest()

    # -- domain API 
    def enable(self, txunits, program, upref):
        self.texture.activate(len(txunits))
        txunits.append(self)
        program.uniform('tx_{}'.format(upref), self.texture)

    # -- function domain API 

    def glsl_declr(self, fname, upref, **kwargs):
        # XXX
        # - what about other vector types?
        c = self.texture.channels
        ret_type = 'float' if c == 1 else 'vec{}'.format(c)
        rgba = 'rgba'[0:c]
        d = self.texture.dimension
        arg_type = 'float' if d == 1 else 'vec{}'.format(d)
        tmpl = self.__class__._GLSL_TEMPLATE_DOMAIN
        declr = tmpl.format(ret_type=ret_type, 
                            arg_type=arg_type, 
                            fname=fname, 
                            rgba=rgba,
                            upref=upref)
        header = self.__class__._GLSL_TEMPLATE_DECRL.format(d=d, upref=upref)
        return header + '\n\n' + declr

class RandomDomain(ContinuousDomain):
    # XXX
    # currently just basic, find a better random
    # implementation here.
    def enable(self, txunits, program, upref):
        t = time()
        program.uniform('rd_d_{}'.format(upref), t - np.floor(t))
        program.uniform('rd2_d_{}'.format(upref), t - np.floor(t))

    def glsl_declr(self, fname, domain_fnames, **kwargs):
        tmpl = """
            uniform float rd_${FNAME};
            uniform float rd2_${FNAME};
            float ${FNAME}(vec2 co){
                co.x += rd_${FNAME};
                co.y += rd2_${FNAME};

                return fract(sin(dot(co.xy, vec2(12.9898,78.233))) * 43758.5453);
            }   
            float ${FNAME}(float co){
                return ${FNAME}(vec2(co, co));
            }   
        """
        return tmpl.replace('${UNAME}', fname).replace('${FNAME}', fname)


class FunctionDomain(ContinuousDomain):
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

    # -- domain API 

    def requires(self, domains):
        res = set(re.findall('\$\{DOMAIN:(.*?)\}', str(self.glsl)))
        frg_dom_names = set(name for name, d in domains.items() if hasattr(d, 'glsl_declr') or hasattr(d, 'glsl_attributes'))
        if len(res - frg_dom_names):
            raise DependencyError('requires fragment domains: {}'.format(','.join(res)))

    # -- function domain API

    def glsl_declr(self, fname, domain_fnames, **kwargs):
        glsl = str(self.glsl) 
        subst = {'${FNAME}': fname}
        subst.update({'${{DOMAIN:{}}}'.format(n): v for n, v in domain_fnames.items()})
        for k, v in subst.items():
            glsl = glsl.replace(k, v)
        return glsl

