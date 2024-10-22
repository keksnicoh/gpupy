#-*- coding: utf-8 -*-
"""
texture utilities

:author: Nicolas 'keksnicoh' Heimann
"""
from gpupy.gl import GPUPY_GL
from gpupy.gl.lib import imread, setter_dict
from OpenGL.GL import *
import numpy as np
import os 

# it is important to define at least those
# texture parameters. otherwise the texture
# interpolation yields (0, 0, 0, 0)
DEFAULT_TEXRURE_PARAMETERS = {
    GL_TEXTURE_MAG_FILTER: GL_NEAREST,
    GL_TEXTURE_MIN_FILTER: GL_NEAREST
}

LINEAR_FILTERS = {
    GL_TEXTURE_MAG_FILTER: GL_LINEAR,
    GL_TEXTURE_MIN_FILTER: GL_LINEAR
}

NEAREST_FILTERS = {
    GL_TEXTURE_MAG_FILTER: GL_NEAREST,
    GL_TEXTURE_MIN_FILTER: GL_NEAREST
}



def gl_texture_id(texture_id):
    """
    returns a valid texture_id from a given object
    or raises a ValueError
    """
    if hasattr(texture_id, 'gl_texture_id'):
        texture_id = texture_id.gl_texture_id

    if int(texture_id) != texture_id or texture_id < 1:
        raise ValueError('invalid texture id ({})'.format(texture_id))

    return texture_id

def gl_texture_unit(texture_unit):
    """
    returns a given texture_unit from a given object
    or raises a ValueError
    """
    if hasattr(texture_unit, 'gl_texture_unit'):
        texture_unit = texture_unit.gl_texture_unit

    if 33984 <= texture_unit < 33984+100: # XXX determine max tex unit...
        return texture_unit
    if 'GL_TEXTURE'+str(texture_unit) not in globals():
        raise ValueError('unvalid texture unit ({}). Please use GL_TEXTURE<N>'.format(texture_unit))

    return texture_unit

def to_device(ndarray, gl_target=None):
    pass

class AbstractTexture():
    def __init__(self,
        gl_texture_id=None,
        gl_texture_parameters=DEFAULT_TEXRURE_PARAMETERS):

        self.gl_texture_id = gl_texture_id
        self.gl_texture_parameters = gl_texture_parameters
        self.gl_texture_unit = None
        self._gl_texture_unit = None

        self._gl_format = None
        self._gl_internal_format = None
        self._gl_type = None
        self._data = None

        # -- for better user experience (XXX maybe remove me when this is not cool)
        self.parameters = setter_dict(self.parameter)

    @property
    def channels(self):
        channelmap = {GL_RED: 1, GL_RG: 2, GL_RGB: 3, GL_RGBA: 4}
        return channelmap[self._gl_format]

    @property
    def dimension(self):
        return self.__class__.DIMENSION
    
    def __del__(self):
        pass
        
    def __gl_tex_image__(self, gl_internal_format, size, gl_format, gl_type, data):
        """
        invokes the glTexImageND method.
        generally a texture must always have an internal format, a size, a format,
        a specific gl_type and some data (which might be None).
        """
        raise NotImplementedError('abstract method')

    def __get_size_and_channels_from_shape__(self, shape):
        """
        returns a valid size object as a function of the shape

        Ex.

           2d texture: shape (400, 100, 3) represents
           a texture with 400x100 pixels and 3 color channels.

           therefore this method would return ((400, 100), 3)
        """
        raise NotImplementedError('abstract method')

    @classmethod
    def from_numpy(cls, ndarray, *args, **kwargs):
        """
        creates a texture from numpy ndarray
        """
        texture = cls(*args, **kwargs)
        texture.load(ndarray)
        return texture

    @classmethod
    def to_device(cls, ndarray, *args, **kwargs):
        return cls.from_numpy(ndarray, *args, **kwargs)

    @classmethod
    def empty_like(cls, ndarray, *args, **kwargs):
        """
        creates an empty texture by using dtype and shape
        from a numpy array
        """
        texture = cls(*args, **kwargs)
        texture.format(ndarray.dtype, ndarray.shape)
        return texture

    @classmethod
    def empty(cls, shape, dtype, *args, **kwargs):
        """
        creates an empty texture by using dtype and shape
        """
        texture = cls(*args, **kwargs)
        texture.format(dtype, shape)
        return texture


    def gl_init_texture(self):
        """
        creates a new texture and assignes the
        gl_texture_parameters
        """
        self.gl_texture_id = glGenTextures(1)
        self._gl_texture_parameters()

    def load(self, ndarray):
        """
        loads texture from numpy array
        """
        self._push(ndarray, *self._numpy_to_gl_parameters(ndarray.dtype, ndarray.shape))

    def resize(self, size):
        """
        resize texture dimensons - (a new empty texture is created).
        """
        self._push(None, size, self._gl_type, self._gl_format, self._gl_internal_format)

    def format(self, np_type, np_shape):
        """
        format texture by given numpy dtype and numpy shape
        """
        self._push(None, *self._numpy_to_gl_parameters(np_type, np_shape))

    def set(self, data):
        self.load(data)

    def _push(self, ndarray, size, gl_type, gl_format, gl_internal_format):
        """
        setup opengl texture
        """
        if self.gl_texture_id is None:
            self.gl_init_texture()

        data = ndarray.flatten() if ndarray is not None else None

        with self:
            self.__gl_tex_image__(gl_internal_format, size, gl_format, gl_type, data)

        self._gl_format = gl_format
        self._gl_internal_format = gl_internal_format
        self._gl_type = gl_type
        self._data = ndarray

        self.size = size

    def __enter__(self):
        self.bind()

    def __exit__(self, exc_type, exc_value, exc_tb):
        self.unbind()

    def activate(self, unit=0):
        # deprecated, use bind(unit=) instead.
        self.bind(unit=unit)
        return unit

    def bind(self, unit=None):
        """
        binds the texture using glBindTexture

        if unit is a positive integer, the texture
        will be bound to the corresponding 
        texture unit. 
        """
        if unit is not None:
            unit_str = 'GL_TEXTURE%d' % unit
            gl_unit = globals()[unit_str]
            glActiveTexture(gl_unit)
            self.gl_texture_unit = unit
            self._gl_texture_unit = gl_unit

        glBindTexture(self.gl_target, self.gl_texture_id)

    if GPUPY_GL.CHECK_VALUES: # just think about this approach more ... 
        def reactivate(self):
            if self._gl_texture_unit is None or self.gl_texture_unit is None:
                raise RuntimeError('cannot reactivate since texture was never activated. (texture unit missing).')
            glActiveTexture(self._gl_texture_unit)

            try:
                glBindTexture(self.gl_target, gl_texture_id(self.gl_texture_id))
            except ValueError:
                raise RuntimeError((
                    'cannot reactivate since texture object '
                    'does not have a valid texture id ({})'
                ).format(self.gl_texture_id))
    else:
        def reactivate(self):
            glActiveTexture(self._gl_texture_unit)
            glBindTexture(self.gl_target, self.gl_texture_id)

    def unbind(self):
        """
        wrapper for glBindTexture
        """
        glBindTexture(self.gl_target, 0)

    def interpolation_nearest(self):
        self.gl_texture_parameters.update(NEAREST_FILTERS)
        with self:
            for p, v in NEAREST_FILTERS.items():
                glTexParameterf(self.gl_target, p, v)

    def interpolation_linear(self):
        self.gl_texture_parameters.update(LINEAR_FILTERS)
        with self:
            for p, v in LINEAR_FILTERS.items():
                glTexParameterf(self.gl_target, p, v)

    def tex_parameterf(self, pname, param):
        self.gl_texture_parameters[pname] = param
        with self:
            glTexParameterf(self.gl_target, pname, param)

    def interpolate_linear(self):
        self.interpolation_linear()

    def interpolate_nearest(self):
        self.interpolation_nearest()



    def parameter(self, p, v):
        self.gl_texture_parameters[p] = v

        with self:
            glTexParameterf(self.gl_target, p, v)
            
    def _gl_texture_parameters(self):
        """
        assign texture parameters to texture
        """
        with self:
            for p, v in self.gl_texture_parameters.items():
                glTexParameterf(self.gl_target, p, v)

    def _numpy_to_gl_parameters(self, dtype, np_shape):
        """
        converts numpy dtype and shape into a size, gl_type
        and format of the texture
        """
        size, channels = self.__get_size_and_channels_from_shape__(np_shape)
        gl_type, gl_format, gl_internal_format = self._find_texture_type_and_format(dtype, channels)

        GPUPY_GL.debug('Texture._numpy_to_gl_parameters() determined texture configuration gl_type={}, gl_format={}, gl_internal_format={} from {} shape ({})'.format(
            gl_type,
            gl_format,
            gl_internal_format,
            dtype,
            ', '.join(str(a) for a in np_shape)))

        return size, gl_type, gl_format, gl_internal_format


    def _find_texture_type_and_format(self, dtype, channels):
        """
        ommit type, format, internal_format as a function of
        dtype and channels.
        """
        if dtype == np.float32:
            gl_type = GL_FLOAT

            if channels == 1:
                gl_format = GL_RED
                gl_internal_format = GL_R32F
            elif channels == 2:
                gl_format = GL_RG
                gl_internal_format = GL_RG32F
            elif channels == 3:
                gl_format = GL_RGB
                gl_internal_format = GL_RGB32F
            elif channels == 4:
                gl_format = GL_RGBA
                gl_internal_format = GL_RGBA32F

        # -- complex numbers
        #
        # XXX is this correct? Does numpy represent complex numbers
        #     like below?
        #
        # one channel equals two floats, 
        # two channels ...   four floats,
        # therefore more channels are not supported.
        elif dtype == np.complex64:
            gl_type = GL_FLOAT 
            if channels == 1:
                gl_format = GL_RG
                gl_internal_format = GL_RG32F
            elif channels == 2:
                gl_format = GL_RGBA
                gl_internal_format = GL_RGBA32F
            else:
                raise ValueError('to many colorchannels for complex numbers')

        # -- double precision
        #
        # not supported at the moment
        # XXX fill missing dtypes
        elif dtype in [np.complex128, np.float64]:
            raise ValueError('double precision dtype {}: not supported'.format(dtype))

        # -- missing implementation
        else:
            raise ValueError('bad dtype {}. currently np.float32, np.complex64 supported'.format(dtype))

        return gl_type, gl_format, gl_internal_format

class Texture1D(AbstractTexture):
    DIMENSION = 1

    def __init__(self,
        gl_texture_id=None,
        gl_texture_parameters=DEFAULT_TEXRURE_PARAMETERS,
        is_array=False):

        AbstractTexture.__init__(self, gl_texture_id,
                                    gl_texture_parameters)

        self.gl_target = GL_TEXTURE_1D

        if self.gl_texture_id is not None:
            with self:
                self._gl_texture_parameters()

    def __get_size_and_channels_from_shape__(self, np_shape):
        """
        converts numpy dtype and shape into a size, gl_type
        and format of the texture
        """
        original_shape = np_shape
        if len(np_shape) == 1:
            np_shape = (np_shape[0], 1)
        elif len(np_shape) == 2:
            if np_shape[1] > 4:
                raise ValueError('ndarray can only have 4 color channels (third np_shape component). {} given'.format(np_shape[2]))
        elif len(np_shape) > 2:
            tail = np_shape[2:]
            if tail[0] != 1 or len(set(tail)) != 1:
                raise ValueError('shapes with len(shape) > 4 are only allowed when they are of the following form: (x,y,c,1,1,1,...)')

        return np_shape[0], np_shape[1]

    def __gl_tex_image__(self, gl_internal_format, size, gl_format, gl_type, data):
        """
        wrapper for glTexImage2D
        """
        GPUPY_GL.debug_wrap(glTexImage1D, self.gl_target,
                                       0,
                                       gl_internal_format,
                                       np.int32(size),
                                       0,
                                       gl_format,
                                       gl_type,
                                       data)

class Texture2D(AbstractTexture):
    """
    2d texture.

    ..code ::
        texture = Texture2D.from_numpy(ndarray)

    if texture allready exists it is possible to wrap
    an instance around it:

    .. code ::
        my_texture_id = glGenTextures(1)
        # ...
        texture = Texture2D(gl_texture_id=my_texture_id)
    """
    DIMENSION = 2

    @classmethod
    def imread(cls, name, flatten=False, mode=None, normalize=255.0, dtype=np.float32):
        data = imread(name, flatten=flatten, mode=mode, normalize=normalize, dtype=dtype)
        return cls.to_device(data)


    def __init__(self,
        gl_texture_id=None,
        gl_texture_parameters=DEFAULT_TEXRURE_PARAMETERS,
        multisample=False,
        array=False):

        """
        creates a GL_TEXTURE_2D_* texture

        :param gl_texture_id: an opengl texture id, if None a new texture will be generated
        :param gl_texture_parameters: a list of tuples p which are compatible to glTexParameterf(target, *p)
        :param multisample: level of multisampling. if False or 0 no multisampling is used.
        :param array: if the texture is actually an array of textures.
        """

        AbstractTexture.__init__(self, gl_texture_id, gl_texture_parameters)

        if multisample != False:
            raise NotImplementedError('multisample texture not implemented yet')

        self.array = array

        if self.array:
            self.gl_target = GL_TEXTURE_2D_ARRAY
        else:
            self.gl_target = GL_TEXTURE_2D

        if self.gl_texture_id is not None:
            with self:
                self._gl_texture_parameters()

    # API methods

    def __gl_tex_image__(self, gl_internal_format, size, gl_format, gl_type, data):
        """
        wrapper for glTexImage* functions
        """
        if self.array:
            GPUPY_GL.debug_wrap(glTexImage3D, self.gl_target,
                                           0,
                                           gl_internal_format,
                                           np.int32(size[1]),
                                           np.int32(size[2]),
                                           np.int32(size[0]),
                                           0,
                                           gl_format,
                                           gl_type,
                                           data)
        else:
            GPUPY_GL.debug_wrap(glTexImage2D, self.gl_target,
                                           0,
                                           gl_internal_format,
                                           np.int32(size[0]),
                                           np.int32(size[1]),
                                           0,
                                           gl_format,
                                           gl_type,
                                           data)

    def __get_size_and_channels_from_shape__(self, np_shape):

        # a 2d texture array must have shape (z, x, y [, c [, 1]*])
        if self.array:
            if len(np_shape) == 3:
                return np_shape, 1
            elif len(np_shape) == 4:
                if np_shape[3] > 4:
                    raise ValueError('ndarray can only have 4 color channels (third np_shape component). {} given'.format(np_shape[3]))
            elif len(np_shape) > 4:
                tail = np_shape[4:]
                if tail[0] != 1 or len(set(tail)) != 1:
                    raise ValueError('shapes with len(shape) > 5 are only allowed when they are of the following form: (z,x,y,c,1,1,1,...)')
            return np_shape[0:3], np_shape[3]

        # a 2d texture must have shape (x, y [, c [, 1]*])
        if len(np_shape) == 2:
            return np_shape, 1
        elif len(np_shape) == 3:
            if np_shape[2] > 4:
                raise ValueError('ndarray can only have 4 color channels (third np_shape component). {} given'.format(np_shape[2]))
        elif len(np_shape) > 3:
            tail = np_shape[3:]
            if tail[0] != 1 or len(set(tail)) != 1:
                raise ValueError('shapes with len(shape) > 4 are only allowed when they are of the following form: (x,y,c,1,1,1,...)')

        return np_shape[0:2], np_shape[2]


class Texture3D(AbstractTexture):
    """
    2d texture.

    ..code ::
        texture = Texture2D.from_numpy(ndarray)

    if texture allready exists it is possible to wrap
    an instance around it:

    .. code ::
        my_texture_id = glGenTextures(1)
        # ...
        texture = Texture2D(gl_texture_id=my_texture_id)
    """
    DIMENSION = 3

    def __init__(self,
        gl_texture_id=None,
        gl_texture_parameters=DEFAULT_TEXRURE_PARAMETERS,
        multisample=False):

        """
        creates a GL_TEXTURE_2D_* texture

        :param gl_texture_id: an opengl texture id, if None a new texture will be generated
        :param gl_texture_parameters: a list of tuples p which are compatible to glTexParameterf(target, *p)
        :param multisample: level of multisampling. if False or 0 no multisampling is used.
        :param array: if the texture is actually an array of textures.
        """

        AbstractTexture.__init__(self, gl_texture_id, gl_texture_parameters)

        if multisample != False:
            raise NotImplementedError('multisample texture not implemented yet')

        self.gl_target = GL_TEXTURE_3D


        if self.gl_texture_id is not None:
            with self:
                self._gl_texture_parameters()

    # API methods

    def __gl_tex_image__(self, gl_internal_format, size, gl_format, gl_type, data):
        """
        wrapper for glTexImage* functions
        """
        GPUPY_GL.debug_wrap(glTexImage3D, self.gl_target,
                                       0,
                                       gl_internal_format,
                                       np.int32(size[2]),
                                       np.int32(size[0]),
                                       np.int32(size[1]),
                                       0,
                                       gl_format,
                                       gl_type,
                                       data)

    def __get_size_and_channels_from_shape__(self, np_shape):

        # a 3d texture array must have shape (z, x, y [, c [, 1]*])
        if len(np_shape) == 3:
            return np_shape, 1
        elif len(np_shape) == 4:
            if np_shape[3] > 4:
                raise ValueError('ndarray can only have 4 color channels (third np_shape component). {} given'.format(np_shape[3]))
        elif len(np_shape) > 4:
            tail = np_shape[4:]
            if tail[0] != 1 or len(set(tail)) != 1:
                raise ValueError('shapes with len(shape) > 5 are only allowed when they are of the following form: (z,x,y,c,1,1,1,...)')
        return np_shape[0:3], np_shape[3]

