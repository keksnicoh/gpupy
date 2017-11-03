#-*- coding: utf-8 -*-
"""
camera glx module. contains several camara components
which uses uniform buffer object.

a camera is an object which can be enabled and disabled 
and co exists with a uniform buffer object at a certain
buffer base.
"""
from gpupy.gl import GPUPY_GL, BufferObject
from gpupy.gl.lib import attributes
from gpupy.gl.lib.matrix import mat4_reflection_xy, mat4_translation, \
    mat4_rot_z, mat4_rot_y, mat4_rot_x

from OpenGL.GL import *

import numpy as np


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


    def commit(self):
        """ update camera data """
        self._ubo.set(self.__buffer__())


class Perspective3D(Camera):
    """
    3d perspective camera

    Attributes:
        fov (float): field of view angle
        frustum (float[2]): near and far plane 
        screensize (float[2]): coordinate space of near plane
        position (float[3]): camera position
        rotation (float[3]): roll, pitch, yaw

    Examples:

        XXX

    """
    screensize = attributes.VectorAttribute(2, (1, 1))
    rotation = attributes.VectorAttribute(3, (0, 0, 0))
    position = attributes.VectorAttribute(3, (0, 0, 0))
    frustum = attributes.VectorAttribute(2, (0.1, 10000)) 
    fov = attributes.CastedAttribute(float, 0.5 * 65.0 * np.pi / 180.0) 

    DTYPE = np.dtype([
        ('mat_view',         np.float32, (4, 4)),
        ('mat_projection',   np.float32, (4, 4)),
        ('mat_viewprojection',   np.float32, (4, 4)),
        ('position',         np.float32, 3),
        ('yaw',              np.float32),
        ('direction',        np.float32, 3),
        ('pitch',            np.float32), 
        ('direction_right',  np.float32, 3),
        ('roll',             np.float32),
        ('direction_top',    np.float32, 3),
    ])

    def __init__(self, screensize, position=(0, 0, 0), rotation=(0, 0, 0), buffer_base = None):

        super().__init__(Perspective3D.DTYPE, buffer_base or GPUPY_GL.CONTEXT.buffer_base('gpupy.gl.camera'))
        self._camera = np.zeros(1, dtype=Perspective3D.DTYPE)
        self._mat_projection = None 
        self._mat_view = None

        self.screensize = screensize
        self.position = position
        self.rotation = rotation
        
        self.direction = (0, 0, 0)
        self.right = (0, 0, 0)
        self.top = (0, 0, 0)

        self.commit()

    # -- api --
    def __buffer__(self):
        # camera position and rotation matrix
        reflection_xy   = mat4_reflection_xy()
        position_matrix = mat4_translation(*self.position)
        rot_roll        = mat4_rot_z(self.rotation[2])
        rot_yaw         = mat4_rot_y(self.rotation[1])
        rot_pitch       = mat4_rot_x(self.rotation[0])
        mat_view = (rot_roll @ rot_pitch @ rot_yaw @ position_matrix @ reflection_xy)

        # perspective projection
        (n, f), ratio  = self.frustum, self.screensize[0] / self.screensize[1]
        h = n * np.tan(self.fov)
        w = h * ratio
        mat_proj = np.array([
            n/w, 0, 0, 0,
            0, n/h, 0, 0,
            0, 0, - (f + n) / (f - n), -2.0 * f * n / (f - n),
            0, 0, -1, 0
        ], dtype=np.float32).reshape((4, 4))

        # ubo
        self._camera['mat_view']        = mat_view.T
        self._camera['mat_projection']  = mat_proj.T
        # remember.. (AB)^T = (B^T)(A^T) 
        self._camera['mat_viewprojection'] = (mat_proj @ mat_view).T 

        self._camera['roll'], \
        self._camera['pitch'], \
        self._camera['yaw'] = self.rotation

        self._camera['position']        = self.position

        self._camera['direction']       = self.direction
        self._camera['direction_right'] = self.right
        self._camera['direction_top']   = self.top

        return self._camera

    # -- camera control events --
    @position.on_change
    @screensize.on_change
    @rotation.on_change
    def _attributes_changed(self, *e):
        self.commit()




