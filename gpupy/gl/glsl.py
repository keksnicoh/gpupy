#-*- coding: utf-8 -*-
import numpy as np

from gpupy.gl.errors import GlError

import re

class GlslParseError(GlError):
    pass

class GlslRenderError(GlError):
    pass

GLTYPY_NUMPY_DTYPE = {
    'mat2'  : (np.float32, (2, 2)),
    'mat3'  : (np.float32, (3, 3)),
    'mat4'  : (np.float32, (4, 4)),
    'dmat2' : (np.float64, (2, 2)),
    'dmat3' : (np.float64, (3, 3)),
    'dmat4' : (np.float64, (4, 4)),
    'bool'  : np.bool,
    'float' : np.float32,
    'uint'  : np.uint32,
    'double': np.float64,
    'vec2'  : (np.float32, (2, )),
    'vec3'  : (np.float32, (3, )),
    'vec4'  : (np.float32, (4, )),
    'bvec2' : (np.bool, (2, )),
    'bvec3' : (np.bool, (3, )),
    'bvec4' : (np.bool, (4, )),
    'uvec2' : (np.uint32, (2, )),
    'uvec3' : (np.uint32, (3, )),
    'uvec4' : (np.uint32, (4, )),
    'ivec2' : (np.int32, (2, )),
    'ivec3' : (np.int32, (3, )),
    'ivec4' : (np.int32, (4, )),
    'dvec2' : (np.float64, (2, )),
    'dvec3' : (np.float64, (3, )),
    'dvec4' : (np.float64, (4, )),
}

SUPPORTED_VECOTR_TYPS = {
    '<i4': 'int', 
    '|b1': 'bool', 
    '<u4': 'uint', 
    '<f4': 'float', 
    '<f8': 'double'
}

SUPPORTED_MATRIX_TYPES = {
    '<f4': 'mat', 
    '<f8': 'dmat'
}

NPVECTOR_TO_GLVECTOR = {
    '<i4': 'ivec', 
    '|b1': 'bvec', 
    '<u4': 'uvec', 
    '<f4': 'vec', 
    '<f8': 'dvec'
}

def render_uniform_block_from_dtype(name, dtype, layout, length=None, structs={}, variable=None):
    """
    renders a glsl uniform block by a given dtype

    Arguments:
    ----
    - name the name of the uniform
    - dtype corresponding dtype
    - layout
    - length
    - structs
    - variable

    layout (<layout>) uniform <name> {
        <dtype>
    }[<length>] <variable>;
    """
    gl_code = "layout ({}) uniform {}\n{{\n".format(layout, name)
    gl_code += render_struct_items_from_dtype(dtype, structs=structs, length=length)

    if variable is not None:
        # XXX: is length a good idea in ubo??
        length = None
        gl_code += "}} {}{};\n".format(variable, '[{:d}]'.format(length) if length is not None else '')
    else:
        gl_code += '};\n'

    return gl_code


def render_struct_from_dtype(name, dtype):
    gl_code = "struct {}\n{{\n".format(name)
    gl_code += render_struct_items_from_dtype(dtype)
    gl_code += "};\n"
#    gl_code += "}} {};\n".format(name)

    return gl_code

def render_struct_items_from_dtype(dtype, structs={}, length=None):
    gl_code = ''

    for ndeclr in dtype.descr:
        shape = ndeclr[2] if len(ndeclr) > 2 else (1, )
        field, dtype_descr = ndeclr[0], ndeclr[1]

        if len(shape) == 1:
            # invalid vector type
            if isinstance(dtype_descr, list):
                sub_dtype = np.dtype(dtype_descr)
                sub_struct_name = None
                for struct_name, struct_dtype in structs.items():
                    if struct_dtype == sub_dtype:
                        sub_struct_name = struct_name
                        break

                if sub_struct_name is None:
                    raise Exception('FOO')
                    raise GlslRenderError('struct makes problems')

                gl_type = sub_struct_name
            else:
                if not dtype_descr in SUPPORTED_VECOTR_TYPS:
                    raise GlslRenderError(('invalid type ({}) declaration in dtype field "{}")'
                                             ' for uniform "{}". Supported {} types are: {}').format(
                                                dtype_descr, field, name, ('vector' if shape[0] > 1 else 'scalar'),
                                                 ', '.join(SUPPORTED_VECOTR_TYPS.values())))

                # check vector size
                if shape[0] == 1:
                    gl_type = SUPPORTED_VECOTR_TYPS[dtype_descr]
                elif shape[0] < 5:
                    gl_type = '{}{}'.format(NPVECTOR_TO_GLVECTOR[dtype_descr], shape[0])
                else:
                    raise GlslRenderError(('invalid type declaration in dtype field "{}" for uniform "{}".'
                                             ' {} components declrared but maximum is 4.').format(field, name, shape[0]))

            # create scalar or vector declarations
            gl_code += "\t{} {}{};\n".format(gl_type, field, '[{:d}]'.format(length) if length is not None else '')

        if len(shape) == 2:
            # matrix size check
            if shape[0] > 4 or shape[1] > 4:
                raise GlslRenderError(('invalid type declaration in dtype field "{}" for uniform "{}": '
                                         'Matrix dimensions {}x{} exceed maximum of 4x4').format(
                                         field, name, shape[0], shape[1]))

            # matrix type check
            if dtype_descr not in SUPPORTED_MATRIX_TYPES:
                raise GlslRenderError(('invalid type ({}) declaration in dtype field "{}" for uniform "{}". '
                                         'Supported matrix types are: {}').format(
                                         dtype_descr, field, name, ', '.join(SUPPORTED_MATRIX_TYPES.values())))

            # create matN or matNxM as well as dmatN or dmatNxM
            dimensions = '{}x{}'.format(*shape) if shape[0] != shape[1] else shape[0]
            gl_code += "\t{}{} {};\n".format(SUPPORTED_MATRIX_TYPES[dtype_descr], dimensions, field)
    return gl_code

def find_structs_as_dtype(gl_code):
    """ extract numpy dtype for many uniform block
        declarations from a given glsl code """
    uniform_dtypes = {}
    matches = re.findall(r'uniform\s+(\w+)\s*\{(.*?)\}\s*(\w*)\s*(?:\[\s*(\d*)\s*\]|)\s*;', 
                         gl_code, 
                         flags=re.S)
    for match in matches:
        uniform_block_name = match[0]
        uniform_block_var = match[2]
        uniform_block_size = int(match[3]) if match[3] != '' else 1
        dtype_members = extract_dtype_from_struct_declaration_string(match[1])
        uniform_dtype = np.dtype(dtype_members)
        uniform_dtypes[uniform_block_name] = uniform_dtype

    return uniform_dtypes

def struct_fields_to_dtype(struct_declr):
    declr_matches = re.findall(r'\s*(\w+)\s*(\w+)\s*;', struct_declr, flags=re.S)
    dtype_members = []
    for (declr_type, declr_name) in declr_matches:
        if not declr_type in GLTYPY_NUMPY_DTYPE:
            raise GlslParseError('invalid struct "{}" for member "{}". Allowed types are {}'.format(', '.join(GLTYPY_NUMPY_DTYPE)))

        if type(GLTYPY_NUMPY_DTYPE[declr_type]) is tuple:
            dtype_members.append((declr_name, GLTYPY_NUMPY_DTYPE[declr_type][0], GLTYPY_NUMPY_DTYPE[declr_type][1]))
        else:
            dtype_members.append((declr_name, GLTYPY_NUMPY_DTYPE[declr_type]))
    return dtype_members
