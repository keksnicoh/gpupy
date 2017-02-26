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
from gpupy.gl.common import *
from gpupy.gl.glsl import * 
from gpupy.gl.common.vector import * 
from gpupy.gl import GPUPY_GL

from gpupy.gl.texture import gl_texture_unit

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
        self.gl_shader_type = self.type
        self.gl_shader_id = None

        # a list of all uniforms within the shader
        self.uniforms = None

        # a list of all structure names within the shader
        self.structs = None

        # vertex attributes
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

        self._precompiled_source = self.source
        self.parse()

        self._auto_declare_struct_ubo = {}


    def parse(self):
        """
        prepares the shader by extracting all informations from given glsl code:
        - tags {% <name> ... %}
        - structures, attributrs, uniforms, uniform_blocks

        XXX:
        - cleanup: #1 parse glsl
                   #2 parse tags
        """
        try:
            self._prepare_attributes()
            self._prepare_structs()
            self._prepare_uniforms()
            self._prepare_uniform_blocks()

        except (GlslParseError, GlslRenderError) as e:
            raise ShaderError('parse error: {}'.format(e.message))

    def declare_struct(self, name, declr):
        """ declares a structure within glsl shader.
            
            arguments:
            ----------
            - name: the name of the structure
            - declr: structure declaration
               str: a glsl strutrue declaration
               numpy.dtype: structure declared by a numpy dtype
               instances with dtype attribute: same as numpy.dtype

            the {% struct <name> %} tag will be substituted by the
            declaration.

            examples:
            ---------
            >>> shader.declare_struct('test', np.dtype([
                ('test', np.float32),
                ('some_vector', (np.foat32, 4))
            ]))

            results in 

            struct test {
                float test;
                vec4 some_vector
            }

        """

        self._assert_struct_exists(name)
        self._check_auto_declared_ubo_structs(name)

        # numpy structs
        if hasattr(declr, 'dtype'):
            declr = declr.dtype
        if isinstance(declr, np.dtype):
            gl_code = render_struct_from_dtype(name, declr)
            dtype = declr

        # a gl_code declaration was given. It will be parsed to check
        # whether it matches with specified struct name.
        elif type(declr) is str:
            gl_code = declr
            uniform_dtype = self._find_struct_declarations(gl_code)
            if not name in uniform_dtype:
                self._serr('struct name "{}" not defined in declaration: \n{}\n.'.format(name, gl_code))
            dtype = uniform_dtype[name]

        # invalid arguments
        else:
            self._error_not_a_struct();

        # register
        if name in self.structs_dtype and dtype != self.structs_dtype[name]:
            if not name in self.structs_declarations:
                GPUPY_GL.warn((
                    'struct declaration for "{}" differs '
                    'from glsl declaration. ({})').format(name, STRING_SHADER_NAMES[self.type]))
                GPUPY_GL.hint((
                    'you may use {% struct <name> %} tag to generate '
                    'struct declaration from numpy dtype within glsl code.'))
            else:
                GPUPY_GL.warn((
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
                field, fdtype= a[0:2]

                # the field type is a structure
                # we need to check whether the structure allready exists 
                # within the shader.
                if isinstance(fdtype, list):
                    struct_dtype = np.dtype(fdtype)
                    found_struct = None

                    # look for existing structures. 
                    for (def_struct, def_struct_dtype) in self.structs_dtype.items():
                        if struct_dtype == def_struct_dtype:
                            # if we find more than two identical structure we cannot
                            # identify the field structure. In such rare cases we 
                            # cannot proceed. If we would proceed we might allow sick
                            # naming bugs to develop.
                            if found_struct is not None:
                                GPUPY_GL.hint('if there are two identical struct declarations with different names and one ')
                                GPUPY_GL.hint('is used as a type of a field of a uniform block, then declare the other struct ')
                                GPUPY_GL.hint('after the declaration of the uniform_block to allow identification of the uniform block field type:')
                                GPUPY_GL.hint('')
                                GPUPY_GL.hint('shader.declare_struct("A", dtype);')
                                GPUPY_GL.hint('shader.declare_uniform(...);')
                                GPUPY_GL.hint('shader.declare_struct("B", dtype);')
                                self._serr(('uniform block field "{}" type is a structure which is identical to '
                                                         'different defined structures ("{}" and "{}").'.format(field, def_struct, found_struct)))

                            GPUPY_GL.info('declaration of uniform "{}" contains a struct for field "{}"'.format(name, field))
                            GPUPY_GL.info('found matching struct definition "{}"'.format(def_struct))
                            found_struct = def_struct

                            if found_struct == field:
                                GPUPY_GL.warn('there exists a struct with the same name as field "{}" which might lead to syntax errors'.format(found_struct))
                    
                    if found_struct is None:
                        GPUPY_GL.warn('declaration of uniform "{}" contains a struct ("{}") for field "{}"'.format(name, a[0], field))
                        GPUPY_GL.warn('no such structure was declared within the shader.'.format(name, a[0]))
                        GPUPY_GL.hint('please use {% struct <name> %} tag with Shader.declare_struct() or')
                        GPUPY_GL.hint('declare the struct explicitly within the shader.')
                        GPUPY_GL.info('auto declare struct "{}" as "t_{}".'.format(a[0], a[0]))

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
            uniform_dtype = self.find_structs_as_dtype(gl_code)

            if not name in uniform_dtype:
                self._serr('uniform name "{}" not defined in declaration: \n{}\n.'.format(name, gl_code))

            dtype = uniform_dtype[name]

        # invalid arguments
        else:
            raise ValueError('argument declr must be either a glsl code declaration or a numpy dtype')

        # register
        if name in self.uniform_dtype and dtype != self.uniform_dtype[name]:
            if not name in self.uniforms_declarations:
                GPUPY_GL.warn((
                    'uniform block declaration for "{}" differs '
                    'from glsl declaration. ({})').format(name, STRING_SHADER_NAMES[self.type]))
                GPUPY_GL.hint((
                    'you may use {% uniform_block <name> %} tag to generate '
                    'uniform block declaration from numpy dtype within glsl code.'))
            else:
                GPUPY_GL.warn((
                    'uniform block declaration for "{}" differs '
                    'from previous declaration. ({})').format(name, STRING_SHADER_NAMES[self.type]))

        self.uniforms_declarations[name] = gl_code
        self.uniform_dtype[name] = dtype

    def delete(self):
        """
        deletes gl shader if exists
        """
        if self.gl_shader_id is not None:
            glDeleteShader(self.gl_shader_id)
            self.gl_shader_id = None


    def compile(self):
        """
        compiles shader and returns gl id
        """
        if self.gl_shader_id is None:
            self.gl_shader_id = glCreateShader(self.type)
            if self.gl_shader_id < 1:
                self.gl_shader_id = None
                self._serr('glCreateShader returns an invalid id.')

         #   self._precompiled_source = self._precompiled_source
            self._compile_tags()
            self._compile_substitutions()
            self.parse()
            self._compile_inject_gl_code()
            self._compile_structs()
            self._compile_uniform_blocks()

            

            glShaderSource(self.gl_shader_id, self._precompiled_source)
            glCompileShader(self.gl_shader_id)

            error_log = glGetShaderInfoLog(self.gl_shader_id)
            if error_log:
                self.delete()
                self._serr('{}'.format(error_log))

        return self.gl_shader_id

    def _compile_tags(self):
        # 
        # substitutions
        self._precompiled_source = re.sub(r'\{\%\s+version\s+\%\}', "#version {}".format(self.substitutions['VERSION']), self._precompiled_source, flags=re.MULTILINE)

        for n, v in self.substitutions.items():
            self._precompiled_source = self._precompiled_source.replace('${'+str(n)+'}', str(v))

    def _compile_structs(self):
        # uniform declarations
        for name, replc in self.structs_require_declraration.items():
            if name not in self.structs_declarations:
                self._serr('tag {{% struct {} %}} not defined. Did you use Shader.declare_uniform()?'.format(name))
            self._precompiled_source = self._precompiled_source.replace(replc, self.structs_declarations[name])

    def _compile_uniform_blocks(self):
        # uniform declarations
        for name, replc in self.uniforms_require_declraration.items():
            if name not in self.uniforms_declarations:
                self._serr('tag {{% uniform_block {} %}} not defined. Did you use Shader.declare_uniform()?'.format(name))
            self._precompiled_source = self._precompiled_source.replace(replc, self.uniforms_declarations[name])

    def _compile_substitutions(self):
        for name, code in self.substitutions.items():
            self._precompiled_source = self._precompiled_source.replace('/*{$%s$}*/'%name, str(code))

    def _compile_inject_gl_code(self):
        source = self._precompiled_source.split('\n')
        for inject in reversed(self._inject_gl_code):
            source.insert(2, inject)
        self._precompiled_source = '\n'.join(source)


    def _find_struct_declarations(self, gl_code):
        """
        finds all structs defined in the glsl code and 
        create numpy dtype from the declaration. 

            struct <name> {
                <dtype>
            } <variable>;

        """
        uniform_dtypes = {}
        matches = re.findall(r'struct\s+(\w+)\s*\{(.*?)\}\s*(\w*)\s*;', 
                             gl_code, 
                             flags=re.S)
        for match in matches:
            uniform_block_name = match[0]
            uniform_block_var = match[2]
            dtype_members = struct_fields_to_dtype(match[1])
            uniform_dtype = np.dtype(dtype_members)
            uniform_dtypes[uniform_block_name] = uniform_dtype

        return uniform_dtypes


    def _prepare_attributes(self):
        """
        finds attributes:
            in/out <type> <name>;

        and registers them at Shader.attributes
        """
        matches = re.findall(r'(in|out)\s+(\w+)\s+([\w]+).*?;', 
                             self._precompiled_source, 
                             flags=re.MULTILINE)
        self.attributes = {k: (s, t) for s, t, k in matches}  

    def _prepare_structs(self):
        """
        finds placeholders:
            {% struct <name> %} 

        XXX
            {% struct <name> as <alias> %}

        also lookup for existing structs within the glsl shader code.

        raises:
        ShaderError:
            if a struct tag {% struct <name> %} intersects with an explicit 
            declaration this method. 
        """
        self.structs = []
        def struct_block_replacememt(match):
            struct_name = match.group(1)
            self.structs.append(struct_name)
            self.structs_require_declraration[struct_name] = '/*--###GPUPY-PRECOMPILE-STRUCT-TARGET-{}###--*/'.format(struct_name)
            return self.structs_require_declraration[struct_name]

        self._precompiled_source = re.sub(r'\{\%\s+struct\s+([a-zA-Z0-9_]+)\s+\%\}', 
                              struct_block_replacememt, 
                              self._precompiled_source, 
                              flags=re.MULTILINE)
        # Read struct block
        self.structs_dtype = self._find_struct_declarations(self._precompiled_source)

        # check if an explicit declaration has the same name as a struct tag.
        intersection_struct_block_declr = set(self.structs) & set(self.structs_dtype.keys())
        if len(intersection_struct_block_declr):
            self._serr(('a struct tag for "{}" was found. '
                        'But there is an explicit declaration within '
                               'glsl code defined as well.').format(', '.join(intersection_struct_block_declr)))

        self.structs.extend(self.structs_dtype.keys())

    def _prepare_uniforms(self):
        """
        finds uniforms:

            uniform <type> <name>;

        and registers them at Shader.uniforms.

        XXX:
        - structured uniforms
        """

        # find atomic uniforms
        self.uniforms = {k: (t, d) for t, k, d in re.findall(
            # example: uniform float dorp = 2;
            #          uniform vec3 burb;
            r'uniform\s+(\w+)\s+([\w]+)\s*=?\s*(.*?)(?:\[\d+\])?;', 
            self._precompiled_source, 
            flags=re.MULTILINE)}

    def _prepare_uniform_blocks(self):
        """
        finds 

            {% uniform_block <name> %} 

        tags and registers them at Shader.uniform_blocks.

        raises:
        ShaderError: if an explicit uniform block declarations intersects with
                     a uniform block tag {% uniform_block <name> %}

        """

        # find uniform placeholders
        # 
        def uniform_block_replacememt(match):
            uniform_name = match.group(1)
            self.uniform_blocks.append(uniform_name)
            self.uniforms_require_declraration[uniform_name] = '/*--###GPUPY-PRECOMPILE-UNIFORM-TARGET-{}###--*/'.format(uniform_name)
            return self.uniforms_require_declraration[uniform_name]

        self._precompiled_source = re.sub(r'\{\%\s+uniform_block\s+([a-zA-Z0-9_]+)\s+\%\}', 
                             uniform_block_replacememt, 
                             self._precompiled_source, 
                             flags=re.MULTILINE)

        # read explicit uniform block declarations
        self.uniform_dtype = find_structs_as_dtype(self._precompiled_source)

        # there should be no explicit uniform declaration if there is
        # a {% uniform %} tag within the shader.
        intersection_uniform_block_declr = set(self.uniform_blocks) & set(self.uniform_dtype.keys())
        if len(intersection_uniform_block_declr):
            self._serr(('a uniform_block tag for "{}" was found. '
                        'But there is an explicit declaration within '
                        'glsl code defined as well.'
                        ).format(', '.join(intersection_uniform_block_declr)))

        self.uniform_blocks.extend(self.uniform_dtype.keys())


    def _assert_struct_exists(self, name):
        if not name in self.structs:
            raise ValueError('no struct "{}" found within shader. Available structs: {}'.format(
                name, ', '.join(self.structs)))

    def _check_auto_declared_ubo_structs(self, name):
        if name in self._auto_declare_struct_ubo:
            GPUPY_GL.warn((
                             'declaration of struct "{}" was allready done implicitly '
                             'by the uniform_block declaration of "{}".'
                             ).format(name, self._auto_declare_struct_ubo[name]))
            GPUPY_GL.hint((
                          'always declare structs before declaring uniform '
                          'blocks to avoid leak of information!'))

    def _error_not_a_struct(self):
        raise ValueError('argument declr must be either a glsl code declaration or a numpy dtype')

    def _serr(self, *args, **kwargs):
        raise ShaderError(self, *args, **kwargs)

class UniformManager():
    pass

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
        self.gl_shader_id      = None
        self.attributes = {}
        self.uniforms   = {}
        self._uniform_changes = {}
        self._uniform_values = {}
        self.uniform_block_index = {}
        self.uniform_dtype = None


    def get_shader(self, gl_type):
        for shader in self.shaders:
            if shader.gl_shader_type == gl_type:
                return shader

    def use(self, flush_uniforms=True):
        """
        tells opengl state to use this program
        """
        if Program.__LAST_USE_GL_ID is not None and Program.__LAST_USE_GL_ID != self.gl_shader_id:
            raise ProgramError('cannot use program {} since program {} is still in use'.format(
                self.gl_shader_id, Program.__LAST_USE_GL_ID
            ))

        if self.gl_shader_id != Program.__LAST_USE_GL_ID:
            glUseProgram(self.gl_shader_id)
            Program.__LAST_USE_GL_ID = self.gl_shader_id
            self.flush_uniforms()

    def unuse(self):
        """
        tells opengl state to unuse this program
        """
        if self.gl_shader_id != Program.__LAST_USE_GL_ID:
            raise ProgramError('cannot unuse program since its not used.')

        glUseProgram(0)
        Program.__LAST_USE_GL_ID = None

    def delete(self):
        """
        deletes gl program if exists
        """
        if self.gl_shader_id is not None:
            glDeleteProgram(self.gl_shader_id)
            self.gl_shader_id = None

    def link(self):
        """
        links all shaders together
        """
        # prepare
        self.gl_shader_id = glCreateProgram()

        if self.gl_shader_id < 1:
            self.gl_shader_id = None
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
            glAttachShader(self.gl_shader_id, shader.gl_shader_id)
        glLinkProgram(self.gl_shader_id)

        error_log = glGetProgramInfoLog(self.gl_shader_id)
        if error_log:
            self.delete()
            raise ProgramError(error_log)

        self._configure_attributes()
        self._configure_uniforms()

        self._check_uniform_blocks()

        return self.gl_shader_id

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
                        GPUPY_GL.warn('uniform block missalignment - Please checkout https://www.opengl.org/registry/doc/glspec45.core.pdf sec 7.6.2.2.')
                        GPUPY_GL.warn('block identifier: {}'.format(name))
                        GPUPY_GL.warn('field "{}" must start at alignment 0 but actually starts at {}:'.format(field, base_alignment))
                        for line in render_uniform_block_from_dtype(name, dtype, 'std140').split("\n"):
                            GPUPY_GL.warn("\t\t{}".format(line))
                        GPUPY_GL.hint('try to avoid vec3 since the opengl alignment does not matchup with C/C++ or python alignment.')
                        GPUPY_GL.hint('in OpenGL a vec3 has an alignment of 4. One can add a padding before vec3 to provide a compatible alignment.')
                        GPUPY_GL.hint('Example: ')
                        GPUPY_GL.hint('   numpy: dtype = np.dtype([("a", np.float32, 3), ("padding", np.float32, 1), ("b", np.float32, 3)]')
                        GPUPY_GL.hint('   shader: uniform A { vec3 a; float padding; vec3 b; }; ')
                        GPUPY_GL.hint('good explanation: http://stackoverflow.com/a/38172697/2072459')


    def uniform(self, name, value, flush=False):
        """
        set uniform *name* value to *value*. if *flush* then
        the change will be flushed to gpu directly. Otherwise
        the uniform changes will be send to gpu when the
        shader is in use.
        """
        if not name in self.uniforms:
            raise ProgramError('unkown uniform "{}"'.format(name))
        if flush or self.gl_shader_id == Program.__LAST_USE_GL_ID:
            self._uniform(name, value)
        else:
            self._uniform_changes[name] = deepcopy(value)

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

            # rethink this here, the problem is about the comparsion of objects.
            if not force:
                if isinstance(value, np.ndarray):
                    was_changed = not np.array_equal(self._uniform_values[name], value)
                else:
                    # if self._uniform_values[name] != value:
                    #   does not work if self._uniform_values[name]  is a list and 
                    #   value is a VectorN.
                    was_changed = value != self._uniform_values[name]

            if force or was_changed:
                self._uniform(name, value)
        self._uniform_changes = {}

    _DTYPE_TEXTURE_UNIT = {'sampler1D', 'sampler2D', 'sampler3D', 'sampler2DMS', 'sampler2DArray'}

    def _uniform(self, name, value):
        dtype = self.uniforms[name][1]
        location = self.uniforms[name][0]

        # XXX
        # - remove deprecated mat*() calls
        try:
            if dtype == 'float':
                glUniform1f(location, np.float32(value))
            elif dtype == 'vec2':
                glUniform2f(location, *np.array(value, dtype=np.float32))
            elif dtype == 'vec3':
                glUniform3f(location, *np.array(value, dtype=np.float32))
            elif dtype == 'vec4':
                glUniform4f(location, *np.array(value, dtype=np.float32))

            elif dtype == 'int':
                glUniform1i(location, *np.array(value, dtype=np.int32))
            elif dtype == 'ivec2':
                glUniform2i(location, *np.array(value, dtype=np.int32))
            elif dtype == 'ivec3':
                glUniform3i(location, *np.array(value, dtype=np.int32))
            elif dtype == 'ivec4':
                glUniform4i(location, *np.array(value, dtype=np.int32))

            elif dtype == 'mat4':
                glUniformMatrix4fv(location, 1, GL_FALSE, np.array(value, dtype=np.float32))
            elif dtype == 'mat3':
                glUniformMatrix3fv(location, 1, GL_FALSE, *np.array(value, dtype=np.float32))
            elif dtype == 'mat2':
                glUniformMatrix2fv(location, 1, GL_FALSE, *np.array(value, dtype=np.float32))

            elif dtype in self._DTYPE_TEXTURE_UNIT:
                glUniform1i(location, gl_texture_unit(value))

            elif dtype == 'bool':
                #XXX
                raise NotImplementedError('not sure how to handle boolean at the moment...')
                glUniform1i(location, glbool(glbool))
            else:
                raise NotImplementedError('oops! dtype "{}" not implemented by shader library.'.format(dtype))
            self._uniform_values[name] = value
        except TypeError:
            raise TypeError(name, value)
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
            self.attributes.update({k: glGetAttribLocation(self.gl_shader_id, k) for k in input_attributes})

       # geom_shader = self.get_geometry_shader()
       # if geom_shader is not None:
       #     input_attributes = {k: d for k, d in geom_shader.attributes.items() if d[0] == 'in'}
       #     self.attributes.update({k: glGetAttribLocation(self.gl_shader_id, k) for k in input_attributes})

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

                location = glGetUniformLocation(self.gl_shader_id, k)
                if location == -1:
                    GPUPY_GL.warn(('could not receive uniform location "{}". '
                                      'Maybe it was never used within main() function?').format(k))
                    GPUPY_GL.hint(('uniforms must be used at least once within the main() function of the shader. '
                                   'Otherwise, one cannot recieve block index by glGetUniformLocation() function.'))
                self.uniforms[k] = (location, u[0], u[1])
                self._uniform_values[k] = None


            # uniform block
            for block_name in shader.uniform_blocks:
                block_index = glGetUniformBlockIndex(self.gl_shader_id, block_name)
                if block_index == GL_INVALID_INDEX:
                    GPUPY_GL.warn(('could not receive uniform_block location "{}". '
                                      'Maybe it was never used within main() function?').format(block_name))
                    GPUPY_GL.hint(('uniform blocks must be used at least once within the main() function of the shader. '
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
        glUniformBlockBinding(self.gl_shader_id, self.uniform_block_index[name], index)

