#-*- coding: utf-8 -*-
"""
shader library

    try:
        program         = Program()
        vertex_shader   = Shader(GL_VERTEX_SHADER, load_lib_file('glsl/id.vert.glsl'))
        fragment_shader = Shader(GL_FRAGMENT_SHADER, load_lib_file('glsl/id.frag.glsl'))

        program.shaders.append(vertex_shader)
        program.shaders.append(fragment_shader)
        program.link()
    except shader.Error as e:
        print('oh no, too bad..', e)

programs find out which attributes and uniforms are present in
given shaders.

XXX
- interface blocks
- register dtypes in some way?
- boolean types

:author: Nicolas 'keksnicoh' Heimann
"""

from gpupy.gl.errors import GlError
from gpupy.gl.gltype import *
from gpupy.gl.common import gpupy_gl_warning, gpupy_gl_hint, gpupy_gl_info
import re
from OpenGL.GL import *
import numpy as np
from copy import deepcopy

STRING_SHADER_NAMES = {
    GL_VERTEX_SHADER         : 'GL_VERTEX_SHADER',
    GL_GEOMETRY_SHADER       : 'GL_GEOMETRY_SHADER',
    GL_FRAGMENT_SHADER       : 'GL_FRAGMENT_SHADER',
    GL_TESS_CONTROL_SHADER   : 'GL_TESS_CONTROL_SHADER',
    GL_TESS_EVALUATION_SHADER: 'GL_TESS_EVALUATION_SHADER',
    GL_COMPUTE_SHADER        : 'GL_COMPUTE_SHADER',
}

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

class ShaderError(GlError):
    def __init__(self, shader, msg, *args, **kwargs):
        GlError.__init__(self, 'Shader({}): {}'.format(STRING_SHADER_NAMES[shader.type], msg), *args, **kwargs)

class ProgramError(GlError):
    pass


class Shader():
    """
    shader representation
    """
    def __init__(self, type, source, substitutions={}):
        """
        initializes shader by given source.
        matches all attributes and uniforms
        by using regex
        """

        # XXX more general solution
        self.substitutions = {
            'VERSION': 410
        }
        self.substitutions.update(substitutions)

        self.source = source
        self.type = type
        self.gl_id = None

        # a list of all uniforms within the shader
        self.uniforms = None
        self.structs = None

        self.attributes = None

        self._inject_gl_code = []
        # uniform declaration
        self.uniforms_require_declraration = {}
        self.uniforms_declarations = {}
        self.uniform_dtype = {} # contains information about uniform block dtypes
        self.uniform_blocks = [] # a list of all uniform blocks within the shader

        # struct declaration
        self.structs_require_declraration = {}
        self.structs_declarations = {}
        self.structs_dtype = {} # contains information about struct dtypes

        self.precomplied_source = None
        self.precompile()

        self._auto_declare_struct_ubo = {}

    def precompile(self):


        matches = re.findall(r'(in|out)\s+(\w+)\s+([\w]+).*?;', 
                             self.source, 
                             flags=re.MULTILINE)
        self.attributes = {k: (s, t) for s, t, k in matches}

        ### -- structs

        # find struct placeholders
        # {% struct <name> %}
        self.structs = []
        def struct_block_replacememt(match):
            struct_name = match.group(1)
            self.structs.append(struct_name)
            self.structs_require_declraration[struct_name] = '/*--###GPUPY-PRECOMPILE-STRUCT-TARGET-{}###--*/'.format(struct_name)
            return self.structs_require_declraration[struct_name]

        self.source = re.sub(r'\{\%\s+struct\s+([a-zA-Z0-9_]+)\s+\%\}', 
                              struct_block_replacememt, 
                              self.source, 
                              flags=re.MULTILINE)
        # Read struct block
        self.structs_dtype = self._find_struct_declarations(self.source)
        intersection_struct_block_declr = set(self.structs) & set(self.structs_dtype.keys())
        if len(intersection_struct_block_declr):
            raise ShaderError(self, ('a struct tag for "{}" was found. '
                               'But there is an explicit declaration within '
                               'glsl code defined as well.').format(', '.join(intersection_struct_block_declr)))

        self.structs.extend(self.structs_dtype.keys())

        ### -- uniforms and uniform blocks

        # find atomic uniforms
        self.uniforms = {k: (t, d) for t, k, d in re.findall(
            # example: uniform float dorp = 2;
            #          uniform vec3 burb;
            r'uniform\s+(\w+)\s+([\w]+)\s*=?\s*(.*?)(?:\[\d+\])?;', 
            self.source, 
            flags=re.MULTILINE)}

        # find uniform placeholders
        # {% uniform <name> %}
        def uniform_block_replacememt(match):
            uniform_name = match.group(1)
            self.uniform_blocks.append(uniform_name)
            self.uniforms_require_declraration[uniform_name] = '/*--###GPUPY-PRECOMPILE-UNIFORM-TARGET-{}###--*/'.format(uniform_name)
            return self.uniforms_require_declraration[uniform_name]

        self.source = re.sub(r'\{\%\s+uniform_block\s+([a-zA-Z0-9_]+)\s+\%\}', 
                             uniform_block_replacememt, 
                             self.source, 
                             flags=re.MULTILINE)

        # read explicit uniform block declarations
        self.uniform_dtype = self._find_uniform_declarations(self.source)

        # there should be no explicit uniform declaration if there is
        # a {% uniform %} tag within the shader.
        intersection_uniform_block_declr = set(self.uniform_blocks) & set(self.uniform_dtype.keys())
        if len(intersection_uniform_block_declr):
            raise ShaderError(self, ('a uniform_block tag for "{}" was found. '
                              'But there is an explicit declaration within '
                              'glsl code defined as well.').format(', '.join(intersection_uniform_block_declr)))

        self.uniform_blocks.extend(self.uniform_dtype.keys())

    def declare_struct(self, name, declr):
        """ declares a struct. 
            if declr is numpy dtype it will be rendered to glsl
            shader code.

            While rendering a numpy dtype the function tries
            to find bad declarations and raises ShaderError if
            bad declarations are found."""

        if not name in self.structs:
            raise ValueError('no struct "{}" found within shader. Available structs: {}'.format(
                name, ', '.join(self.structs)))

        if name in self._auto_declare_struct_ubo:
            gpupy_gl_warning('declaration of struct "{}" was allready done implicitly by the uniform_block declaration of "{}".'.format(name, self._auto_declare_struct_ubo[name]))
            gpupy_gl_hint('always declare structs before declaring uniform blocks to avoid leak of information!')

        if hasattr(declr, 'dtype'):
            declr = declr.dtype

        # declare struct block by numpy dtype
        if isinstance(declr, np.dtype):
            gl_code = render_struct_from_dtype(name, declr)
            dtype = declr

        # a gl_code declaration was given. It will be parsed to check
        # whether it matches with specified struct name.
        elif type(declr) is str:
            gl_code = declr
            uniform_dtype = self._find_struct_declarations(gl_code)
            if not name in uniform_dtype:
                raise ShaderError(self, 'struct name "{}" not defined in declaration: \n{}\n.'.format(name, gl_code))
            dtype = uniform_dtype[name]

        # invalid arguments
        else:
            raise ValueError('argument declr must be either a glsl code declaration or a numpy dtype')

        # register
        if name in self.structs_dtype and dtype != self.structs_dtype[name]:
            if not name in self.structs_declarations:
                gpupy_gl_warning((
                    'struct declaration for "{}" differs '
                    'from glsl declaration. ({})').format(name, STRING_SHADER_NAMES[self.type]))
                gpupy_gl_hint((
                    'you may use {% struct <name> %} tag to generate '
                    'struct declaration from numpy dtype within glsl code.'))
            else:
                gpupy_gl_warning((
                    'struct declaration for "{}" differs '
                    'from previous declaration. ({})').format(name, STRING_SHADER_NAMES[self.type]))

        self.structs_declarations[name] = gl_code
        self.structs_dtype[name] = dtype

    def declare_uniform(self, name, declr, layout='std140', variable=None, length=None):
        """ declares uniform interface block. if declr
            is numpy dtype it will be rendered to glsl
            shader code.

            While rendering a numpy dtype the function tries
            to find bad declarations and raises ShaderError if
            bad declarations are found."""

        if not name in self.uniform_blocks:
            raise ValueError('no uniform block "{}" found within shader. Available uniform blocks: {}'.format(
                name, ', '.join(self.uniform_blocks)))

        if hasattr(declr, 'dtype'):
            if hasattr(declr, '__len__'):
                length = len(declr)
            declr = declr.dtype

        # declare uniform block by numpy dtype
        if isinstance(declr, np.dtype):

            for a in declr.descr:
                field = a[0]
                fdtype = a[1]

                # the field type is a structure
                # we need to check whether the structure allready exists 
                # within the shader.
                if isinstance(a[1], list):
                    struct_dtype = np.dtype(a[1])
                    found_struct = None

                    # look for existing structures. 
                    for (def_struct, def_struct_dtype) in self.structs_dtype.items():
                        if struct_dtype == def_struct_dtype:
                            # if we find more than two identical structure we cannot
                            # identify the field structure. In such rare cases we 
                            # cannot proceed. If we would proceed we might allow sick
                            # naming bugs to develop.
                            if found_struct is not None:
                                gpupy_gl_hint('if there are two identical struct declarations with different names and one ')
                                gpupy_gl_hint('is used as a type of a field of a uniform block, then declare the other struct ')
                                gpupy_gl_hint('after the declaration of the uniform_block to allow identification of the uniform block field type:')
                                gpupy_gl_hint('')
                                gpupy_gl_hint('shader.declare_struct("A", dtype);')
                                gpupy_gl_hint('shader.declare_uniform(...);')
                                gpupy_gl_hint('shader.declare_struct("B", dtype);')
                                raise ShaderError(self, ('uniform block field "{}" type is a structure which is identical to '
                                                         'different defined structures ("{}" and "{}").'.format(field, def_struct, found_struct)))

                            gpupy_gl_info('declaration of uniform "{}" contains a struct for field "{}"'.format(name, field))
                            gpupy_gl_info('found matching struct definition "{}"'.format(def_struct))
                            found_struct = def_struct

                            if found_struct == field:
                                gpupy_gl_warning('there exists a struct with the same name as field "{}" which might lead to syntax errors'.format(found_struct))
                    
                    if found_struct is None:
                        gpupy_gl_warning('declaration of uniform "{}" contains a struct ("{}") for field "{}"'.format(name, a[0], field))
                        gpupy_gl_warning('no such structure was declared within the shader.'.format(name, a[0]))
                        gpupy_gl_hint('please use {% struct <name> %} tag with Shader.declare_struct() or')
                        gpupy_gl_hint('declare the struct explicitly within the shader.')
                        gpupy_gl_info('auto declare struct "{}" as "t_{}".'.format(a[0], a[0]))

                        struct_name = 't_{}'.format(a[0])
                        placeholder = '/*--###GPUPY-PRECOMPILE-STRUCT-INJECTION-TARGET-{}###--*/'
                        self._inject_gl_code.append(placeholder)
                        self.structs_require_declraration[struct_name] = placeholder
                        self.structs.append(struct_name)
                        self.declare_struct(struct_name, struct_dtype)

                        # if the user invokes declare_struct() in the future we can
                        # warn him that we allready defined the structure implicitly.
                        self._auto_declare_struct_ubo[struct_name] = name

            gl_code = render_uniform_block_from_dtype(name, declr, layout, length, self.structs_dtype, variable=variable)
            dtype = declr

        # a gl_code declaration was given. It will be parsed to check
        # whether it mathces with specified interface block name.
        elif type(declr) is str:
            gl_code = declr
            uniform_dtype = self._find_uniform_declarations(gl_code)

            if not name in uniform_dtype:
                raise ShaderError(self, 'uniform name "{}" not defined in declaration: \n{}\n.'.format(name, gl_code))

            dtype = uniform_dtype[name]

        # invalid arguments
        else:
            raise ValueError('argument declr must be either a glsl code declaration or a numpy dtype')

        # register
        if name in self.uniform_dtype and dtype != self.uniform_dtype[name]:
            if not name in self.uniforms_declarations:
                gpupy_gl_warning((
                    'uniform block declaration for "{}" differs '
                    'from glsl declaration. ({})').format(name, STRING_SHADER_NAMES[self.type]))
                gpupy_gl_hint((
                    'you may use {% uniform_block <name> %} tag to generate '
                    'uniform block declaration from numpy dtype within glsl code.'))
            else:
                gpupy_gl_warning((
                    'uniform block declaration for "{}" differs '
                    'from previous declaration. ({})').format(name, STRING_SHADER_NAMES[self.type]))

        self.uniforms_declarations[name] = gl_code
        self.uniform_dtype[name] = dtype

    def delete(self):
        """
        deletes gl shader if exists
        """
        if self.gl_id is not None:
            glDeleteShader(self.gl_id)
            self.gl_id = None

    def compile(self):
        """
        compiles shader and returns gl id
        """
        if self.gl_id is None:
            self.gl_id = glCreateShader(self.type)
            if self.gl_id < 1:
                self.gl_id = None
                raise ShaderError(self, 'glCreateShader returns an invalid id.')

            source = self.source.split('\n')
            for inject in reversed(self._inject_gl_code):
                source.insert(2, inject)
            source = '\n'.join(source)

            for name, code in self.substitutions.items():
                source = source.replace('/*{$%s$}*/'%name, str(code))

            # uniform declarations
            for name, replc in self.uniforms_require_declraration.items():
                if name not in self.uniforms_declarations:
                    raise ShaderError(self, 'tag {{% uniform_block {} %}} not defined. Did you use Shader.declare_uniform()?'.format(name))
                source = source.replace(replc, self.uniforms_declarations[name])

            # uniform declarations
            for name, replc in self.structs_require_declraration.items():
                if name not in self.structs_declarations:
                    raise ShaderError(self, 'tag {{% struct {} %}} not defined. Did you use Shader.declare_uniform()?'.format(name))
                source = source.replace(replc, self.structs_declarations[name])

            # substitutions
            source = re.sub(r'\{\%\s+version\s+\%\}', "#version {}".format(self.substitutions['VERSION']), source, flags=re.MULTILINE)

            self.precomplied_source = source 
            glShaderSource(self.gl_id, source)
            glCompileShader(self.gl_id)

            error_log = glGetShaderInfoLog(self.gl_id)
            if error_log:
                self.delete()
                raise ShaderError(self, '{}'.format(error_log))

        return self.gl_id

    def _find_struct_declarations(self, gl_code):
        """ extract numpy dtype for many uniform block
            declarations from a given glsl code """
        uniform_dtypes = {}
        matches = re.findall(r'struct\s+(\w+)\s*\{(.*?)\}\s*(\w*)\s*;', 
                             gl_code, 
                             flags=re.S)
        for match in matches:
            uniform_block_name = match[0]
            uniform_block_var = match[2]
            dtype_members = self._extract_dtype_from_struct_declaration_string(match[1])
            uniform_dtype = np.dtype(dtype_members)
            uniform_dtypes[uniform_block_name] = uniform_dtype

        return uniform_dtypes

    def _find_uniform_declarations(self, gl_code):
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
            dtype_members = self._extract_dtype_from_struct_declaration_string(match[1])
            uniform_dtype = np.dtype(dtype_members)
            uniform_dtypes[uniform_block_name] = uniform_dtype

        return uniform_dtypes

    def _extract_dtype_from_struct_declaration_string(self, struct_declr):
        declr_matches = re.findall(r'\s*(\w+)\s*(\w+)\s*;', struct_declr, flags=re.S)
        dtype_members = []
        for (declr_type, declr_name) in declr_matches:
            if not declr_type in GLTYPY_NUMPY_DTYPE:
                raise ShaderError(self, ('invalid struct "{}" for member'
                                       + ' "{}". Allowed types are {}').format(', '.join(GLTYPY_NUMPY_DTYPE)))

            if type(GLTYPY_NUMPY_DTYPE[declr_type]) is tuple:
                dtype_members.append((declr_name, GLTYPY_NUMPY_DTYPE[declr_type][0], GLTYPY_NUMPY_DTYPE[declr_type][1]))
            else:
                dtype_members.append((declr_name, GLTYPY_NUMPY_DTYPE[declr_type]))
        return dtype_members

class Program():
    """
    opengl render program representation
    """
    __LAST_USE_GL_ID = None

    def __init__(self):
        """
        initialize the state
        """
        self.shaders    = []
        self.gl_id      = None
        self.attributes = {}
        self.uniforms   = {}
        self._uniform_changes = {}
        self._uniform_values = {}
        self.uniform_block_index = {}
        self.uniform_dtype = None

    def use(self, flush_uniforms=True):
        """
        tells opengl state to use this program
        """
        if Program.__LAST_USE_GL_ID is not None and Program.__LAST_USE_GL_ID != self.gl_id:
            raise ProgramError('cannot use program {} since program {} is still in use'.format(
                self.gl_id, Program.__LAST_USE_GL_ID
            ))

        if self.gl_id != Program.__LAST_USE_GL_ID:
            glUseProgram(self.gl_id)
            Program.__LAST_USE_GL_ID = self.gl_id
            self.flush_uniforms()

    def unuse(self):
        """
        tells opengl state to unuse this program
        """
        if self.gl_id != Program.__LAST_USE_GL_ID:
            raise ProgramError('cannot unuse program since its not used.')

        glUseProgram(0)
        Program.__LAST_USE_GL_ID = None

    def delete(self):
        """
        deletes gl program if exists
        """
        if self.gl_id is not None:
            glDeleteProgram(self.gl_id)
            self.gl_id = None

    def link(self):
        """
        links all shaders together
        """
        # prepare
        self.gl_id = glCreateProgram()

        if self.gl_id < 1:
            self.gl_id = None
            raise ProgramError('glCreateProgram returns an invalid id')


        # find uniform block declarations from other shaders
        # for implicit usage of {% uniform_block <name> %} tag
        self.uniform_dtype = {}
        for shader in self.shaders:
            self.uniform_dtype.update(shader.uniform_dtype)

        for shader in self.shaders:
            # implicit type declarations
            if len(shader.uniforms_require_declraration):
                for name in shader.uniforms_require_declraration:
                    if not name in shader.uniforms_declarations and name in self.uniform_dtype:
                        shader.declare_uniform(name, self.uniform_dtype[name])

            shader.compile()
            glAttachShader(self.gl_id, shader.gl_id)
        glLinkProgram(self.gl_id)

        error_log = glGetProgramInfoLog(self.gl_id)
        if error_log:
            self.delete()
            raise ProgramError(error_log)

        self._configure_attributes()
        self._configure_uniforms()

        self._check_uniform_blocks()

        return self.gl_id

    def _check_uniform_blocks(self):
        for name, dtype in self.uniform_dtype.items():
            byte_count = 0
            for descr in dtype.descr:
                field = descr[0]
                field_offset = dtype.fields[field][1]

                # check for vec3 alignment
                if len(descr) == 3  and descr[2] == (3, ):
                    base_alignment = (field_offset/4) % 4
                    if base_alignment != 0:
                        gpupy_gl_warning('uniform block missalignment - Please checkout https://www.opengl.org/registry/doc/glspec45.core.pdf sec 7.6.2.2.')
                        gpupy_gl_warning('block identifier: {}'.format(name))
                        gpupy_gl_warning('field "{}" must start at alignment 0 but actually starts at {}:'.format(field, base_alignment))
                        for line in render_uniform_block_from_dtype(name, dtype, 'std140').split("\n"):
                            gpupy_gl_warning("\t\t{}".format(line))
                        gpupy_gl_hint('try to avoid vec3 since the opengl alignment does not matchup with C/C++ or python alignment.')
                        gpupy_gl_hint('in OpenGL a vec3 has an alignment of 4. One can add a padding before vec3 to provide a compatible alignment.')
                        gpupy_gl_hint('Example: ')
                        gpupy_gl_hint('   numpy: dtype = np.dtype([("a", np.float32, 3), ("padding", np.float32, 1), ("b", np.float32, 3)]')
                        gpupy_gl_hint('   shader: uniform A { vec3 a; float padding; vec3 b; }; ')
                        gpupy_gl_hint('good explanation: http://stackoverflow.com/a/38172697/2072459')


    def uniform(self, name, value, flush=False):
        if not name in self.uniforms:
            raise ProgramError('unkown uniform "{}"'.format(name))

        if flush or self.gl_id == Program.__LAST_USE_GL_ID:
            self._uniform(name, value)
        else:
            self._uniform_changes[name] = deepcopy(value)
        #
        #self.flush_uniforms()

    def declare_uniform(self, name, declr, variable=None, length=None):
        found_at_least_one = False
        for shader in self.shaders:
            if name in shader.uniform_blocks:
                shader.declare_uniform(name, declr, variable=variable, length=length)
                found_at_least_one = True


        if not found_at_least_one:
            raise ProgramError(('no uniform block "{}" found within program'.format(name)))

    def declare_struct(self, name, declr):
        found_at_least_one = False
        for shader in self.shaders:
            if name in shader.structs:
                shader.declare_struct(name, declr)
                found_at_least_one = True


        if not found_at_least_one:
            raise ProgramError(('no struct "{}" found within program'.format(name)))

    def flush_uniforms(self, force=False):
        for name, value in self._uniform_changes.items():
            was_changed = False
            if not force:
                if isinstance(value, np.ndarray):
                    was_changed = not np.array_equal(self._uniform_values[name], value)
                else:
                    was_changed = self._uniform_values[name] != value
            if force or was_changed:
                self._uniform(name, value)
        self._uniform_changes = {}

    def _uniform(self, name, value):
        type = self.uniforms[name][1]
        location = self.uniforms[name][0]

        # XXX
        # - remove deprecated mat*() calls
        if type == 'mat4':
            glUniformMatrix4fv(location, 1, GL_FALSE, mat4(value))
        elif type == 'mat3':
            glUniformMatrix3fv(location, 1, GL_FALSE, mat3(value))
        elif type == 'mat2':
            glUniformMatrix2fv(location, 1, GL_FALSE, mat2(value))
        elif type == 'float':
            glUniform1f(location, value)
        elif type == 'int':
            glUniform1i(location, value)
        elif type == 'vec2':
            glUniform2f(location, *value)
        elif type == 'vec3':
            glUniform3f(location, *value)
        elif type == 'vec4':
            glUniform4f(location, *value)
        elif type == 'sampler2D':
            glUniform1i(location, value)
        elif type == 'sampler1D':
            glUniform1i(location, value)
        elif type == 'sampler2DMS':
            glUniform1i(location, value)
        elif type == 'sampler2DArray':
            glUniform1i(location, value)
        elif type == 'bool':
            glUniform1i(location, value)
        else:
            raise NotImplementedError('oops! type "{}" not implemented by shader library.'.format(type))
        self._uniform_values[name] = value

    def get_vertex_shader(self):
        """
        returns vertex shader if appended
        """
        for shader in self.shaders:
            if shader.type == GL_VERTEX_SHADER:
                return shader

    def get_geometry_shader(self):
        """
        returns geometry shader shader if appended
        """
        for shader in self.shaders:
            if shader.type == GL_GEOMETRY_SHADER:
                return shader

    def _configure_attributes(self):
        """
        configures attributes cache
        """
        self.attributes = {}

        vertex_shader = self.get_vertex_shader()
        if vertex_shader is not None:
            input_attributes = {k: d for k, d in vertex_shader.attributes.items() if d[0] == 'in'}
            self.attributes.update({k: glGetAttribLocation(self.gl_id, k) for k in input_attributes})

       # geom_shader = self.get_geometry_shader()
       # if geom_shader is not None:
       #     input_attributes = {k: d for k, d in geom_shader.attributes.items() if d[0] == 'in'}
       #     self.attributes.update({k: glGetAttribLocation(self.gl_id, k) for k in input_attributes})

    def _configure_uniforms(self):
        """
        configures uniforms cache
        """
        self.uniforms = {}
        for shader in self.shaders:
            for k, u in shader.uniforms.items():
                # check whether any uniform is defined in 2 shaders with different types.
                if k in self.uniforms and self.uniforms[k][1] != u[0]:
                    raise ShaderError(shader, 'uniform "{name}" appears twice with different types: {t1}, {t2}'.format(
                        name=k,
                        t1=self.uniforms[k][1],
                        t2=u[0]
                    ))

                location = glGetUniformLocation(self.gl_id, k)
                if location == -1:
                    gpupy_gl_warning(('could not receive uniform location "{}". '
                                      'Maybe it was never used within main() function?').format(k))
                    gpupy_gl_hint(('uniforms must be used at least once within the main() function of the shader. '
                                   'Otherwise, one cannot recieve block index by glGetUniformLocation() function.'))
                self.uniforms[k] = (location, u[0], u[1])
                self._uniform_values[k] = None


            # uniform block
            for block_name in shader.uniform_blocks:
                block_index = glGetUniformBlockIndex(self.gl_id, block_name)
                if block_index == GL_INVALID_INDEX:
                    gpupy_gl_warning(('could not receive uniform_block location "{}". '
                                      'Maybe it was never used within main() function?').format(block_name))
                    gpupy_gl_hint(('uniform blocks must be used at least once within the main() function of the shader. '
                                   'Otherwise, one cannot recieve block index by glGetUniformBlockIndex() function.'))
                    continue

                self.uniform_block_index[block_name] = block_index


    def uniform_block_binding(self, name, index):
        if name not in self.uniform_block_index:
            raise ProgramError('invalid uniform block name "{}".'.format(name))
        shape = None
        if hasattr(index, 'shape'):
            shape = index.shape
        if hasattr(index, 'gl_buffer_base'):
            index = index.gl_buffer_base

       # if shape is not None:
       #     dd()
        glUniformBlockBinding(self.gl_id, self.uniform_block_index[name], index)


def render_uniform_block_from_dtype(name, dtype, layout, length=None, structs={}, variable=None):
    gl_code = "layout ({}) uniform {}\n{{\n".format(layout, name)
    gl_code += render_struct_items_from_dtype(dtype, structs=structs, length=length)

    if variable is not None:
        # XXX: is length a good idea in ubo??
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
    supported_vector_types = {'<i4': 'int', '|b1': 'bool', '<u4': 'uint', '<f4': 'float', '<f8': 'double'}
    supported_matrix_types = {'<f4': 'mat', '<f8': 'dmat'}
    np_to_glvector = {'<i4': 'ivec', '|b1': 'bvec', '<u4': 'uvec', '<f4': 'vec', '<f8': 'dvec'}

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
                    raise ShaderError(self, 'struct makes problems')

                gl_type = sub_struct_name
            else:
                if not dtype_descr in supported_vector_types:
                    raise ShaderError(self, ('invalid type ({}) declaration in dtype field "{}")'
                                             ' for uniform "{}". Supported {} types are: {}').format(
                                                dtype_descr, field, name, ('vector' if shape[0] > 1 else 'scalar'),
                                                 ', '.join(supported_vector_types.values())))

                # check vector size
                if shape[0] == 1:
                    gl_type = supported_vector_types[dtype_descr]
                elif shape[0] < 5:
                    gl_type = '{}{}'.format(np_to_glvector[dtype_descr], shape[0])
                else:
                    raise ShaderError(self, ('invalid type declaration in dtype field "{}" for uniform "{}".'
                                             ' {} components declrared but maximum is 4.').format(field, name, shape[0]))

            # create scalar or vector declarations
            gl_code += "\t{} {}{};\n".format(gl_type, field, '[{:d}]'.format(length) if length is not None else '')

        if len(shape) == 2:
            # matrix size check
            if shape[0] > 4 or shape[1] > 4:
                raise ShaderError(self, ('invalid type declaration in dtype field "{}" for uniform "{}": '
                                         'Matrix dimensions {}x{} exceed maximum of 4x4').format(
                                         field, name, shape[0], shape[1]))

            # matrix type check
            if dtype_descr not in supported_matrix_types:
                raise ShaderError(self, ('invalid type ({}) declaration in dtype field "{}" for uniform "{}". '
                                         'Supported matrix types are: {}').format(
                                         dtype_descr, field, name, ', '.join(supported_matrix_types.values())))

            # create matN or matNxM as well as dmatN or dmatNxM
            dimensions = '{}x{}'.format(*shape) if shape[0] != shape[1] else shape[0]
            gl_code += "\t{}{} {};\n".format(supported_matrix_types[dtype_descr], dimensions, field)
    return gl_code