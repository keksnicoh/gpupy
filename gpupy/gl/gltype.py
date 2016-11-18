### DEPRECATED ###
# DEPRECATED
#-*- coding: utf-8 -*-
"""
opengl compatible types
:author: Nicolas 'keksnicoh' Heimann
"""

import numpy
def mat4(x):
    if hasattr(x, 'mat4'):
        return x.mat4
    return numpy.array(x[0:16], dtype=numpy.float32)
mat3 = lambda *x: numpy.array(x[0:9], dtype=numpy.float32) if not hasattr(x, 'mat3') else x.mat4
mat2 = lambda *x: numpy.array(x[0:4], dtype=numpy.float32) if not hasattr(x, 'mat2') else x.mat4
vec2 = lambda *x: numpy.array(x[0:2], dtype=numpy.float32) if not hasattr(x, 'vec2') else x.mat4
vec3 = lambda *x: numpy.array(x[0:3], dtype=numpy.float32) if not hasattr(x, 'vec3') else x.mat4
vec4 = lambda *x: numpy.array(x[0:4], dtype=numpy.float32) if not hasattr(x, 'vec4') else x.mat4

ivec2 = lambda x: numpy.array([int(round(a,0)) for a in x[0:2]], dtype=numpy.int32) if not hasattr(x, 'ivec2') else x.ivec2
ivec3 = lambda x: numpy.array([int(round(a,0)) for a in x[0:3]], dtype=numpy.int32) if not hasattr(x, 'ivec2') else x.ivec3
ivec4 = lambda x: numpy.array([int(round(a,0)) for a in x[0:4]], dtype=numpy.int32) if not hasattr(x, 'ivec2') else x.ivec4