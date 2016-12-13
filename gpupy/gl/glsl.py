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
    'int'  : np.int32,
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
    """
    renders a string of glsl code which represents the data declaration
    of a structure. 

    Example:
    --------
    sub_dtype = np.dtype([...])
    dtype = np.dtype([
        ('a', np.float32),
        ('b', (np.float32, 4, 4)),
        ('c', np.int32, 2),
        ('d', sub_dtype)
    ])
    render_struct_item_from_dtype(dtype, {'derp': sub_dtype})

    Result:
    -------
        float a;
        mat4 b;
        ivec2 c;
        derp d;

    Arguments:
    ----------
    dtype: numpy dtype describing the fields 
    structs: existing structures which are used by dtype.
    length: broken at the moment

    Raises:
    -------
    GlslRenderError: whenever a field of the dtype could not
                     be transformed to glsl.

    XXX:
    - length parameter is not implemented well.
    """
    gl_code = ''

    for ndeclr in dtype.descr:
        shape = ndeclr[2] if len(ndeclr) > 2 else (1, )
        field, dtype_descr = ndeclr[0], ndeclr[1]

        # we have either a scalar, vector or struct as field type.
        if len(shape) == 1:

            # the type is a numpy structure.
            # check if the dtype is defined by one structure
            # within the structs argument. 
            if isinstance(dtype_descr, list):
                sub_dtype = np.dtype(dtype_descr)
                gl_type = None
                for struct_name, struct_dtype in structs.items():
                    if struct_dtype == sub_dtype:
                        if gl_type is None:
                            gl_type = struct_name
                        else:
                            # XXX:
                            # - enable the possibility to declare sub dtypes.
                            raise GlslRenderError((
                                'cannot match field "{}". Its type is the'
                                + 'same as the definition of "{}" and "{}" structs.'
                            ).format(field, gl_type, struct_name))

                if gl_type is None:
                    raise GlslRenderError('cannot render field "{}". No structure defined for the field.'.format(field))

            # should be a scalar or vector field type
            else:
                if not dtype_descr in SUPPORTED_VECOTR_TYPS:
                    raise GlslRenderError((
                        'invalid type ({}) declaration in dtype field "{}".'
                        ' Supported {} types are: {}'
                    ).format(dtype_descr, 
                             field, 
                             ('vector' if shape[0] > 1 else 'scalar'),
                             ', '.join(SUPPORTED_VECOTR_TYPS.values())))

                # check vector size
                if shape[0] == 1:
                    gl_type = SUPPORTED_VECOTR_TYPS[dtype_descr]
                elif shape[0] < 5:
                    gl_type = '{}{}'.format(NPVECTOR_TO_GLVECTOR[dtype_descr], shape[0])
                else:
                    raise GlslRenderError((
                        'invalid type declaration in dtype field "{}".'
                        ' {} components declrared but maximum is 4.'
                    ).format(field, shape[0]))

            # create scalar or vector declarations
            gl_code += "\t{} {}{};\n".format(gl_type, field, '[{:d}]'.format(length) if length is not None else '')

        # matrix types
        elif len(shape) == 2:

            # matrix size check
            if shape[0] > 4 or shape[1] > 4:
                raise GlslRenderError((
                    'invalid type declaration in dtype field "{}": '
                    'Matrix dimensions {}x{} exceed maximum of 4x4'
                ).format(field, shape[0], shape[1]))

            # matrix type check
            if dtype_descr not in SUPPORTED_MATRIX_TYPES:
                raise GlslRenderError((
                    'invalid type ({}) declaration in dtype field "{}". '
                    'Supported matrix types: {}'
                ).format(dtype_descr, field, ', '.join('{}={}'.format(*a) for a in SUPPORTED_MATRIX_TYPES.items())))

            # create matN or matNxM as well as dmatN or dmatNxM
            dimensions = '{}x{}'.format(*shape) if shape[0] != shape[1] else shape[0]
            gl_code += "\t{}{} {};\n".format(SUPPORTED_MATRIX_TYPES[dtype_descr], dimensions, field)

        else:
            raise GlslRenderError('unsupported field type in field "{}": {}'.format(field, dtype_descr))

    return gl_code

def find_structs_as_dtype(gl_code, keyword='uniform'):
    """ extract numpy dtype for many uniform block
        declarations from a given glsl code """
    uniform_dtypes = {}
    matches = re.findall(r'\s*'+re.escape(keyword)+'\s+(\w+)\s*\{(.*?)\}\s*(\w*)\s*(?:\[\s*(\d*)\s*\]|)\s*;', 
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
            raise GlslParseError((
                'invalid struct: member "{}" has unsupported type "{}". '
                'Supported types are: {}'
            ).format(declr_name, declr_type, ', '.join(GLTYPY_NUMPY_DTYPE)))

        if type(GLTYPY_NUMPY_DTYPE[declr_type]) is tuple:
            dtype_members.append((declr_name, GLTYPY_NUMPY_DTYPE[declr_type][0], GLTYPY_NUMPY_DTYPE[declr_type][1]))
        else:
            dtype_members.append((declr_name, GLTYPY_NUMPY_DTYPE[declr_type]))
    return dtype_members
