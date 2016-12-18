#-*- coding: utf-8 -*-
"""
EXPERIMENTAL - CAMERAS WILL LISTEN TO VECTOR EVENTS
"""
from gpupy.gl import GlConfig
from gpupy.gl.common import *
from gpupy.gl.buffer import BufferObject
from gpupy.gl.matrix import *
from gpupy.gl.vector import * 
import numpy as np

from OpenGL.GL import *

class Camera(object):
    """

    """

    def __init__(
        self,
        dtype,
        buffer_base=None):

        self.dtype              = dtype 
        self.gl_buffer_base = buffer_base
        self._ubo = None 

        self._ubo = BufferObject.zeros(1, self.dtype, target=GL_UNIFORM_BUFFER)
        self._ubo.bind_buffer_base(self.gl_buffer_base)


    def enable(self):
        """ enables the camera by binding the
            buffer target """
        self._ubo.bind_buffer_base(self.gl_buffer_base)

    def disable(self):
        """ disables the camera by unbinding the
            buffer target """
        self._ubo.bind_buffer_base(0)

    def __matricies__(self):
        raise NotImplementedError('abstract method')

    def commit(self):
        """ update camera data """
        self._ubo.set(self.__buffer__())




class Camera2D(Camera):
    DTYPE = np.dtype([
        ('mat_view',         np.float32, (4, 4)),
        ('mat_projection',   np.float32, (4, 4)),
        ('position',         np.float32, 3),
        ('roll',             np.float32),
        ('direction',        np.float32, 3),
        ('_b1',             np.float32), 
        ('direction_right',  np.float32, 3),
        ('_b2',             np.float32),
        ('direction_top',    np.float32, 3),
    ])

    def __init__(self, screensize, position=(0, 0, 0), roll=0, matrix_dimension=4, buffer_base=None):
        super().__init__(Camera2D.DTYPE, buffer_base or GlConfig.STATE.RESERVED_BUFFER_BASE['gpupy.gl.camera'])
        self._camera = np.zeros(1, dtype=Camera2D.DTYPE)
        self._mat_projection = None 
        self._mat_view = None

        self._screensize = vec2(screensize)
        self.initial_screensize = vec2(self._screensize.xy)

        self._position = vec3(position)
        self._roll = roll

        self._create_view_matrix()
        self._create_projection_matrix()
        
        self._screensize.on_change.append(self.screensize_changed)
        self._position.on_change.append(self.position_changed)

        self.commit()

    # -- api --
    def __matricies__(self):
        return self._mat_projection, self._mat_view

    def __buffer__(self):
        self._camera['mat_view']        = self._mat_view
        self._camera['mat_projection']  = self._mat_projection
        self._camera['roll']            = self.roll
        self._camera['position']        = self.position.xyz
        self._camera['direction']       = (0, 0, -1)
        self._camera['direction_right'] = (1, 0, 0)
        self._camera['direction_top']   = (0, 1, 0)
        return self._camera

    # -- camera control properties --
    @property
    def position(self):
        return self._position

    @position.setter
    def position(self, value):
        self._position.xyz = value

    @property
    def screensize(self):
        return self._screensize
    
    @screensize.setter
    def screensize(self, value):
        self._screensize.xy = value

    @property 
    def roll(self):
        return self._roll 

    @roll.setter
    def roll(self, roll):
        old_roll = roll
        self._roll = roll
        self.roll_changed(self.roll, old_roll)

    # -- camera control events --

    def roll_changed(self, roll, old_value):
        self._create_view_matrix()
        self.commit()

    def position_changed(self, position, old_value):
        self._create_view_matrix()
        self.commit()

    def screensize_changed(self, screensize, old_value):
        self._create_projection_matrix()
        self.commit()

    # -- matrix methods 

    def _create_view_matrix(self):
        self._mat_view = np.array([
            1, 0, 0, -self.position.x,
            0, 1, 0, -self.position.y,
            0, 0, 1, 0,
            0, 0, 0, 1,
        ], dtype=np.float32).reshape((4, 4)).T

    def _create_projection_matrix(self):
        self._mat_projection = np.array([
            2.0 / self.screensize.x, 0,                         0, 0,
            0,                       -2.0 / self.screensize.y,  0, 0,
            0,                       0,                         1, 0,
            0,                       0,                         0, 1,
        ], dtype=np.float32).reshape((4, 4)).T


