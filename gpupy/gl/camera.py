#-*- coding: utf-8 -*-
"""
camera utils

XXX
 - optimize projection view matrix creation (i.e.: only create new matrix is neccessary.)
 - look_at method is still broken
 - orthigraphic projection: cannot move in z direction.
:author: Nicolas 'keksnicoh' Heimann
"""

from gpupy.gl.lib import *
from gpupy.gl.buffer import BufferObject
from gpupy.gl.matrix import *
import numpy as np
from gpupy.gl import GPUPY_GL

from OpenGL.GL import *

# some default values
DEFAULT_FOV  = 0.5 * 65.0 * np.pi / 180.0
DEFAULT_FAR  = 10000
DEFAULT_NEAR = 0.1

class Camera(object):
    """
    camera classification.
    A camera represents two matricies (project, view) to transform
    verticies from world to screen space.

    The data is uploaded into an uniform buffer object
    which is binded to the default binding index reserved 
    at GlConfig.STATE.RESERVED_BUFFER_BASE['gpupy.gl.camery'].

    .. code ::

       camera = Camera()
       camera.enable()

    The camera object classifies as an object which is bound to
    a opengl buffer base by using the Camera.gl_buffer_base attribute.
    It is therefore possible to pass the camera into a uniform
    block declaration of a shader

    .. code ::

       shader.declare_uniform('camera', camera)

    Note that within the shader one can then use

    .. code ::

       {% uniform_block camera %}

    This will generate the corresponding interface block of the camera.

    Technical details:
    ------------------
    Angles (yaw, pitch, roll):
    - yaw: angle to y-axis
    - pitch: angle to z-axis
    - roll: angle to x-axis

    Position: p

    The view matrix is given by

         R_roll * R_pitch * R_yaw * T_p

    where R is a rotation matrix and T a translation matrix.
    """
    DTYPE = np.dtype([
        ('mat_view',         np.float32, (4, 4)),
        ('mat_projection',   np.float32, (4, 4)),
        ('position',         np.float32, 3),
        ('yaw',              np.float32),

        ('direction',        np.float32, 3),
        ('pitch',            np.float32),

        ('direction_right',  np.float32, 3),
        ('roll',             np.float32),

        ('direction_top',    np.float32, 3),
    ])

    PROJECTION_ORTHOGRAPHIC = 0
    PROJECTION_PERSPECTIVE = 1

    def __init__(
        self,
        screensize=[2.0, 2.0],
        projection=PROJECTION_ORTHOGRAPHIC,
        dtype=DTYPE,
        fov=DEFAULT_FOV,
        far=DEFAULT_FAR,
        near=DEFAULT_NEAR,
        buffer_base=None):

        """
        :param screensize: the scaling of the screensize (XXX: better name?)
        :param projection: which kind of projection should be used.
           available:
           - PROJECTION_ORTHOGRAPHIC
           - PROJECTION_PERSPECTIVE

        :param dtype: the dtype of the camera buffer
        :param fov: field of view
        :param far: farest point
        :param near: nearest point
        :param buffer_base: the buffer base index which 
                            should be used by the uniform buffer.
        """

        self.screensize         = screensize#
        self.initial_screensize = screensize#ensure_vec2(int, screensize)
        self.projection         = projection
        self.dtype              = dtype
        self.buffer_base = buffer_base
        self._position = (0, 0, 0)
        self._rotation = (0, 0, 0)

        self.gl_buffer_base = None

        self.fov = fov
        self.near = near
        self.far = far
        self._update_symmetric_projection_screensize()

        (self.mat_projection, self.mat_view) = self.create_matricies()
        self._camera = None
        self.init_ubo()

        self._last_ubo = None 
    def _update_symmetric_projection_screensize(self):
        if self.projection == Camera.PROJECTION_ORTHOGRAPHIC:
            self.right = self.screensize[0] / 2.0
            self.left = - self.right

            self.top = self.screensize[1] / 2.0
            self.bottom = - self.top

        elif self.projection == Camera.PROJECTION_PERSPECTIVE:
            ratio   = float(self.screensize[0]) / self.screensize[1]
            tangent = np.tan(self.fov)
            height  = self.near * tangent
            width   = height * ratio

            self.right  = width
            self.left   = -width

            self.top    = height
            self.bottom = -height


    def init_ubo(self):
        """ initializes camera ubo """
        camera = np.zeros(1, self.dtype)

        self._ubo = BufferObject.to_device(camera, target=GL_UNIFORM_BUFFER)
        self._ubo.bind_buffer_base(self.buffer_base 
                                   if self.buffer_base is not None 
                                   else GPUPY_GL.CONTEXT.buffer_base('gpupy.gl.camera'))

        self.gl_buffer_base = self._ubo.gl_buffer_base
        self._camera = camera

        self._update_camera()

    @property
    def direction(self):
        """ returns camera view direction vector """
        yaw = self._rotation[1]
        pitch = self._rotation[0]
        return (-np.cos(pitch)*np.sin(yaw), np.sin(pitch), np.cos(pitch)*np.cos(yaw))


    @property
    def direction_right(self):
        """ returns right normal vector from camera space """
        yaw = self._rotation[1]-np.pi/2
        return (-np.sin(yaw), 0, np.cos(yaw))


    @property
    def direction_top(self):
        """ returns top normal vector from camera space """
        yaw = self._rotation[1]
        pitch = self._rotation[0]-np.pi/2
        return (-np.cos(pitch)*np.sin(yaw), np.sin(pitch), np.cos(pitch)*np.cos(yaw))

    def enable(self):
        """ enables the camera by binding the
            buffer target """
        self._last_ubo = glGetIntegerv(GL_UNIFORM_BUFFER_BINDING)
        self._ubo.bind_buffer_base(self.buffer_base)

    def disable(self):
        """ disables the camera by unbinding the
            buffer target """
        self._ubo.bind_buffer_base(0)
       # glBindBuffer(GL_UNIFORM_BUFFER, self._last_ubo)
       # glBindBufferBase(GL_UNIFORM_BUFFER, self._last_ubo)
    def create_matricies(self):
        """ creates projection and view matrix.

            view matrix:
               R_roll * R_pitch * R_yaw * T """
        reflection_xy   = mat4_reflection_xy()
        position_matrix = mat4_translation(*self._position)
        rot_roll        = mat4_rot_z(self._rotation[2])
        rot_yaw         = mat4_rot_y(self._rotation[1])
        rot_pitch       = mat4_rot_x(self._rotation[0])

        projection_matrix = self.create_projection_matrix()

        return (projection_matrix, rot_roll.dot(rot_pitch.dot(rot_yaw.dot(position_matrix.dot(reflection_xy)))).T)

    def set_screensize(self, framebuffer_size):
        self.screensize = framebuffer_size

    def create_projection_matrix(self):
        """ creates projection matricies. Thanks
            to http://www.songho.ca/opengl/gl_projectionmatrix.html """
        if self.projection == Camera.PROJECTION_ORTHOGRAPHIC:
            return np.array([
                2.0 / (self.right - self.left), 0,                                                    0,  - (self.right + self.left) / (self.right - self.left),
                0,                       -2.0 / (self.top - self.bottom),                              0,  - (self.top + self.bottom) / (self.top - self.bottom),
                0,                       0,                              -2.0  / (self.far - self.near),  - (self.far + self.near) / (self.far - self.near),
                0,                       0,                                                           0,                        1,
            ], dtype=np.float32).reshape((4, 4)).T

        elif self.projection == Camera.PROJECTION_PERSPECTIVE:
            print(self.near, self.right, self.left)
            a = np.array([
                2.0 * self.near / (self.right - self.left), 0,                                          (self.right + self.left) / (self.right - self.left), 0,
                0,                                          2.0 * self.near / (self.top - self.bottom), (self.top + self.bottom) / (self.top - self.bottom), 0,
                0,                                          0,                                          - (self.far + self.near) / (self.far - self.near),   -2.0 * self.far * self.near / (self.far - self.near),
                0,                                          0,                                          -1,                                                  0
            ], dtype=np.float32).reshape((4, 4)).T
            print(a)
            return a

        else:
            raise ValueError('invalid camera projection. Available camera projections: Camera.PROJECTION_ORTHOGRAPHIC, Camera.PROJECTION_PERSPECTIVE')


    def send(self, create_matricies=True):
        """ send current camera data to uniform buffer. """
        if create_matricies:
            (self.mat_projection, self.mat_view) = self.create_matricies()

        self._update_camera()
        self._ubo.set(self._camera)

    def _update_camera(self):
        """ update camera data """
        self._camera['mat_view']        = self.mat_view
        self._camera['mat_projection']  = self.mat_projection
        self._camera['yaw']             = self._rotation[1]
        self._camera['pitch']           = self._rotation[0]
        self._camera['roll']            = self._rotation[2]
        self._camera['position']        = self._position
        self._camera['direction']       = self.direction
        self._camera['direction_right'] = self.direction_right
        self._camera['direction_top']   = self.direction_top

    def set_screensize(self, screensize, send=True):
        """ will set a new screensize to the camera.
            note that this function will override the projection
            configuration r, l, t, b by assuming a symmetric
            viewport. """
        self.screensize = screensize
        self._update_symmetric_projection_screensize()
        send and self.send()


    def set_position(self, position, send=True):
        """ translates the camera to a given position """
        self._position = ensure_vec3(float, position)
        send and self.send()


    def translate(self, x=0, y=0, z=0, send=True):
        """ translates the camera by a given translation """
        self._position = (
            self._position[0] + float(x),
            self._position[1] + float(y),
            self._position[2] + float(z))

        send and self.send()


    def look_at(self, point):
        """ calculates camera rotation to look at a certain point
            at the current camera position """
        # XXX broken at the moment
        x = self._position
        v = np.subtract(point, x)
        l = np.linalg.norm(v)
        phi1 = np.arccos(v[2] / l)
        phi2 = np.arctan(np.sqrt(v[0] ** 2 + v[1] ** 2) / v[2])

        self._rotation = (
            -phi1,
            phi2,
            self._rotation[2])
        print(np.sqrt(v[0] ** 2 + v[1] ** 2) / v[2], v[1] / v[0], phi1, phi2)


    def rotate(self, pitch=0, yaw=0, roll=0, send=True):
        """ rotates the camera principal axes by given amount """
        self._rotation = (
            self._rotation[0] + float(pitch),
            self._rotation[1] + float(yaw),
            self._rotation[2] + float(roll))

        send and self.send()


    def set_rotation(self, rotation, send=True):
        """ sets camera principal axes """
        self._rotation = ensure_vec3(float, rotation)
        send and self.send()

def keyboard_flyaround(move_yaw=(83, 87), move_pitch=(65, 68), move_roll=32):
    def _handler(camera, keyboard):
        did_something = False
        if move_yaw[0] in keyboard:
            camera.translate(5*camera.direction_top[0], -5*camera.direction_top[1], 5*camera.direction_top[2])
            did_something = True
        if move_yaw[1] in keyboard:
            camera.translate(-5*camera.direction_top[0], 5*camera.direction_top[1], -5*camera.direction_top[2])
            did_something = True
        if move_pitch[0] in keyboard:
            camera.translate(-5*camera.direction_right[0], 5*camera.direction_right[1], -5*camera.direction_right[2])
            did_something = True
        if move_pitch[1] in keyboard:
            camera.translate(5*camera.direction_right[0], -5*camera.direction_right[1], 5*camera.direction_right[2])
            did_something = True
        if move_roll in keyboard and 340 in keyboard:
            camera.translate(-5*camera.direction[0], -5*camera.direction[1], -5*camera.direction[2])
            did_something = True
        elif move_roll in keyboard:
            camera.translate(x=5*camera.direction[0], y=5*camera.direction[1], z=5*camera.direction[2])
            did_something = True
        if 262 in keyboard:
            camera.rotate(yaw=-0.01)
            did_something = True
        if 263 in keyboard:
            camera.rotate(yaw=+0.01)
            did_something = True
        if 265 in keyboard:
            camera.rotate(pitch=+0.01)
            did_something = True
        if 264 in keyboard:
            camera.rotate(pitch=-0.01)
            did_something = True
        return did_something
    return _handler
