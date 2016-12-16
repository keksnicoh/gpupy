#-*- coding: utf-8 -*-
"""
vertex buffer object and vertex array object utilities.
.. code ::
    np_data = np.array([...], dtype=np.dtype([
        ('vertex', np.float32, (3,)),
        ('color', np.float32, (4,)),
        ('some_magic_number', np.int32)
    ]))
    my_vbo = BufferObject.to_device(np_data)
    # assume that dtype names are shader input names
    vao = ArrayObject.link_shader_attributes(my_shader, my_vbo, another_vbo_with_more_attributes)

XXX
- define more complex stuff for ArrayObject. How to deal with strided data manually?
- ensure that also plain opengl can be combined with all the stuff here.
- UBO alignment warnings.
- what if there is a opengl buffer and we want to wrap this object around?
- array access: b[i], b[s:l], ... ???
:author: Nicolas 'keksnicoh' Heimann
"""
from gpupy.gl.errors import GlError

from OpenGL.GL import *

HAS_CL = False
try:
    import pyopencl as cl
    HAS_CL = True
except:

    pass 

import numpy as np

from operator import mul
from ctypes import c_void_p

# some link to docs to improve exceptions.
DOCS = {
    'glBindBuffer': 'https://www.opengl.org/sdk/docs/man/html/glBindBuffer.xhtml',
    'glBindBufferBase': 'https://www.opengl.org/sdk/docs/man/docbook4/xhtml/glBindBufferBase.xml',
}

def assert_cl(f):
    """
    for methods which require pyopencl
    """
    def _f(*args, **kwargs):
        if not HAS_CL:
            raise RuntimeError('pyopencl is required')
        if not cl.have_gl():
            raise RuntimeError('pyopengl.have_gl() returned False')
            
        return f(*args, **kwargs)
    return _f

class BufferObject():
    """
    Representaion of OpenGL VBO.
    Any BufferObject instance has opengl specific
    properties which can be used within gl* functions:
        target
        usage
        gl_vbo_id
        gl_buffer_base
    Also it adds some features of numpy api e.g.:
         shape, dtype, factory methods (empty_like ...),
    To push and pull data from host memory to gpu memory the
    methods set() and get() provide a wrapper for glBufferData
    and glGetBufferSubData. TODO: what if one wants to read/update
    only a part of the buffer.
    This class requires an OpenGL context to be active.
    """
    TARGET_TO_STR = {
        GL_ARRAY_BUFFER: 'GL_ARRAY_BUFFER',
        GL_ATOMIC_COUNTER_BUFFER: 'GL_ATOMIC_COUNTER_BUFFER',
        GL_COPY_READ_BUFFER: 'GL_COPY_READ_BUFFER',
        GL_COPY_WRITE_BUFFER: 'GL_COPY_WRITE_BUFFER',
        GL_DISPATCH_INDIRECT_BUFFER: 'GL_DISPATCH_INDIRECT_BUFFER',
        GL_DRAW_INDIRECT_BUFFER: 'GL_DRAW_INDIRECT_BUFFER',
        GL_ELEMENT_ARRAY_BUFFER: 'GL_ELEMENT_ARRAY_BUFFER',
        GL_PIXEL_PACK_BUFFER: 'GL_PIXEL_PACK_BUFFER',
        GL_PIXEL_UNPACK_BUFFER: 'GL_PIXEL_UNPACK_BUFFER',
        GL_QUERY_BUFFER: 'GL_QUERY_BUFFER',
        GL_SHADER_STORAGE_BUFFER: 'GL_SHADER_STORAGE_BUFFER',
        GL_TEXTURE_BUFFER: 'GL_TEXTURE_BUFFER',
        GL_TRANSFORM_FEEDBACK_BUFFER: 'GL_TRANSFORM_FEEDBACK_BUFFER',
        GL_UNIFORM_BUFFER: 'GL_UNIFORM_BUFFER',
    }

    _BOUND_BUFFER_BASES = []

    @classmethod
    def empty(cls, shape, dtype, target=GL_ARRAY_BUFFER):
        return cls(shape, dtype, target=target)

    @classmethod
    def empty_like(cls, data, target=GL_ARRAY_BUFFER):
        return cls(data.shape, data.dtype, target=target)

    @classmethod
    def zeros(cls, shape, dtype, target=GL_ARRAY_BUFFER):
        data = np.zeros(shape, dtype=dtype)
        return cls(data.shape, data.dtype, allocator=_create_new_vbo_allocator(data), target=target)

    @classmethod
    def zeros_like(cls, data, target=GL_ARRAY_BUFFER):
        data = np.zeros_like(data)
        return cls(data.shape, data.dtype, allocator=_create_new_vbo_allocator(data), target=target)

    @classmethod
    def ones(cls, shape, dtype, target=GL_ARRAY_BUFFER):
        data = np.ones(shape, dtype=dtype)
        return cls(data.shape, data.dtype, allocator=_create_new_vbo_allocator(data), target=target)

    @classmethod
    def ones_like(cls, data, target=GL_ARRAY_BUFFER):
        data = ones_like.ones(data)
        return cls(data.shape, data.dtype, allocator=_create_new_vbo_allocator(data), target=target)

    @classmethod
    def to_device(cls, data, target=GL_ARRAY_BUFFER, usage=GL_STATIC_DRAW):
        return cls(data.shape, data.dtype, allocator=_create_new_vbo_allocator(data), target=target, usage=usage)

    def arange(cls, target=GL_ARRAY_BUFFER, *args, **kwargs):
        data = numpy.arange(*args, **kwargs)
        return cls.to_device(data, target=target)

    def __init__(self, shape=None, dtype=None, target=GL_ARRAY_BUFFER, usage=GL_STATIC_DRAW, allocator=None):

        self.shape = shape if type(shape) is tuple else (shape, )
        self.dtype = np.dtype(dtype)
        self.itemsize = np.dtype(dtype).itemsize

        try:
            self.nbytes = self.itemsize*reduce(mul, self.shape)
        except:
            import functools
            self.nbytes = self.itemsize*functools.reduce(mul, self.shape)

        self._target = target
        self._usage = usage
        self._cl_array = None
        self._allocator = allocator or _create_new_vbo_allocator()

        self.gl_vbo_id = self._allocator(self.nbytes, self._target, self._usage)

        self.sync_with_vbo(True)

        self.gl_buffer_base = None

        self._has_updates = False

    def __len__(self):
        """
        returns first shape component
        """
        return self.shape[0]

    def sync_with_vbo(self, check=False):
        """
        syncronize buffer parameters to this instance:
          - BUFFER_SIZE
          - USAGE
        """
        glBindBuffer(self._target, self.gl_vbo_id)
        nbytes = glGetBufferParameteriv(self._target, GL_BUFFER_SIZE)
        if check and nbytes != self.nbytes:
            raise GlError('vbo({}) has size {}b but BufferObject requires its size to be {}b'.format(
                self.gl_vbo_id,
                nbytes,
                self.nbytes
            ))

        validate_nbytes_dtype(nbytes, self.itemsize)
        self._nbytes = nbytes

        usage = glGetBufferParameteriv(self._target, GL_BUFFER_USAGE)
        if check and self._usage is not None and usage != self._usage:
            raise GlError(
                'vbo({},usage={}) does not equal defined BufferObject.usage {}'.format(
                    self.gl_vbo_id,
                    usage,
                    self._usage
                )
            )
        self._usage = usage

        glBindBuffer(self._target, 0)

    def set(self, ndarray, offset=0, length=None):
        """
        upload data from host memory to gpu.
        """
        if ndarray.dtype != self.dtype:
            raise GlError('FOO')

        self.shape = ndarray.shape
        self.nbytes = ndarray.nbytes

        glBindBuffer(self._target, self.gl_vbo_id)
        glBufferData(self._target, self.nbytes, ndarray, self._usage)
        glBindBuffer(self._target, 0)

        self._has_updates = True

    def get(self):
        """
        loads data from gpu to host memory and maps
        it to numpy ndarray
        """
        glBindBuffer(self._target, self.gl_vbo_id)
        data = glGetBufferSubData(self._target, 0, self.nbytes)
        glBindBuffer(self._target, 0)
        return data.view(self.dtype).reshape(self.shape)

    @assert_cl
    def get_cl_array(self, queue):
        """
        returns pyopencl array allocated to the vbo.
        note that interoperatibility must be enabled.
        """
        if self._cl_buffer is None:
            self._cl_array = cl.array.Array(
                queue,
                self.shape,
                self.dtype, allocator=lambda b: cl.GLBuffer(ctx, cl.mem_flags.READ_WRITE, int(self.gl_vbo_id))
            )

        return self._cl_array

    def sort(self, use_cl=None):
        pass

    @assert_cl
    def sort_cl(self):
        pass

    def bind(self):
        glBindBuffer(self._target, self.gl_vbo_id)

    def unbind(self):
        glBindBuffer(self._target, 0)

    def bind_buffer_base(self, index=None):
        """
        wrapper for glBindBufferBase.
        raises an exception if buffer has wrong target.
        """
        valid_targets = [
            GL_ATOMIC_COUNTER_BUFFER,
            GL_TRANSFORM_FEEDBACK_BUFFER,
            GL_UNIFORM_BUFFER,
            GL_SHADER_STORAGE_BUFFER
        ]
        if self._target not in valid_targets:
            raise GlError('cannot use bind_buffer_base: bad target "{}". Allowed targets are {}. OpenGL Specs {}'.format(
                self.TARGET_TO_STR[self._target],
                ', '.join(self.TARGET_TO_STR[t] for t in valid_targets),
                DOCS['glBindBufferBase']))

        if index is None:
            if self.gl_buffer_base is None:
                raise GlError('argument index must be an integer if this buffer was never bound before.')
            index = self.gl_buffer_base

        glBindBufferBase(self._target, index, self.gl_vbo_id)
        self.gl_buffer_base = index


# checks whether nbytes are dividable by itemsize
# which is required when one loads data from GPU
# to host and host buffer has a specific itemsize (numpy dtype)
def validate_nbytes_dtype(nbytes, itemsize):
    if nbytes % itemsize > 0:
        raise GlError(
            'buffersize {}b must be dividable by itemsize {}b'.format(
                nbytes,
                itemsize
            )
        )

# inspired by pyopencl
def _create_new_vbo_allocator(data=None):
    def _alloc(nbytes, target, usage):
        vbo = glGenBuffers(1)
        glBindBuffer(target, vbo)
        glBufferData(target, nbytes, data, usage)
        glBindBuffer(target, 0)
        return vbo
    return _alloc

def create_vao_from_program_buffer_object(program, buffer_object):
    """
    creates a vao by reading the attributes of a shader program and links
    them to a given buffer_object dtype items.

    :param program: shader program
    :param buffer_object: buffer_object
    """
    buffer_object.bind()
    vao = glGenVertexArrays(1)
    glBindVertexArray(vao)
    for (attribute, pointer) in program.attributes.items():
        if buffer_object.dtype[attribute].subdtype is None:
            components = 1
        else:
            components = buffer_object.dtype[attribute].subdtype[1][0]
        glVertexAttribPointer(pointer, components, GL_FLOAT, GL_FALSE, buffer_object.dtype.itemsize, c_void_p(buffer_object.dtype.fields[attribute][1]))
        glEnableVertexAttribArray(pointer)

    glBindVertexArray(0)
    buffer_object.unbind()

    return vao



