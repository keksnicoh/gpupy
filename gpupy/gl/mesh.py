#-*- coding: utf-8 -*-
"""
contains some function which creates basic geometric meshes.

:author: Nicolas 'keksnicoh' Heimann
"""
import numpy as np

from gpupy.gl import BufferObject

from OpenGL.GL import * 
from ctypes import c_void_p

# basic mesh dtype.
MESH_DTYPE = np.dtype([
    ('vertex', np.float32, 3),
    ('color', np.float32, 4),
    ('normal', np.float32, 3),
    ('tex', np.float32, 2),
])

class Mesh():
    """
    basic mesh class
    """
    def __init__(self, attribute_locations):
        self.attribute_locations = attribute_locations

    def init(self):
        raise NotImplementedError('abstract method')

    def draw(self):
        raise NotImplementedError('abstract method')

class StridedVertexMesh(Mesh):
    """
    strided mesh

    mesh has a single buffer with strided data e.g.

       1. (vertex1, color1, normal1, tex1)
       2. (vertex2, color2, normal2, tex2)
       3. (vertex3, color3, normal3, tex3)
           ...

    """
    def __init__(self, vertices, vertex_type=GL_TRIANGLES, attribute_locations={'vertex': 1, 'color': 2, 'normal': 3, 'tex': 4}):
        """
        Arguments:
            - vertices: strided numpy data (must have a dtype)

                ..code ::
                    np.array([...], dtype=np.dtype([
                        ('vertex', np.float32, 3), 
                        ('color', np.float32, 2), ...
                    ]))

            - vertex_type: how to interpret the data:

                    GL_TRIANGLES, GL_LINES, ...

            - attribute_locations: the locations of the attributes in the corresponding
                shader program.
        """
        super().__init__(attribute_locations)
        self.vertices = vertices
        self.buffer = None 
        self.vao = None
        self.vertex_type = GL_TRIANGLES
        self.init()

    def init(self):
        self.buffer = BufferObject.to_device(self.vertices)
        self.vao = glGenVertexArrays(1)

        glBindVertexArray(self.vao)
        self.buffer.bind()

        for attribute, location in self.attribute_locations.items():
            if self.buffer.dtype[attribute].subdtype is None:
                components = 1
            else:
                components = self.buffer.dtype[attribute].subdtype[1][0]

            glVertexAttribPointer(location, 
                                  components, 
                                  GL_FLOAT, 
                                  GL_FALSE, 
                                  self.buffer.dtype.itemsize, 
                                  c_void_p(self.buffer.dtype.fields[attribute][1]))
            glEnableVertexAttribArray(location)

        self.buffer.unbind()
        glBindVertexArray(0)

    def draw(self):
        """
        draws the vertex array object
        """
        glBindVertexArray(self.vao)
        glDrawArrays(self.vertex_type, 0, len(self.buffer))
        glBindVertexArray(0)


def mesh3d_cylinder(r=1, h=1, prec=50, color=(.5, .5, .5, 1)):
    if not callable(color):
        b = color
        del color
        color = lambda *a: b

    phi_range = [2 * np.pi / prec * phi for phi in range(prec+1)]
    phi_range[-1] = 0

    mesh = np.zeros(prec*12, dtype=MESH_DTYPE)

    index = 0
    for i in range(prec):
        mesh['vertex'][index] = (r*np.cos(phi_range[i]), 0, r*np.sin(phi_range[i]))
        mesh['color'][index] = color(phi)
        mesh['normal'][index] = (0, 1, 0)
        index += 1

        mesh['vertex'][index] = (r*np.cos(phi_range[i+1]), 0, r*np.sin(phi_range[i+1]))
        mesh['color'][index] = color(phi)
        mesh['normal'][index] = (0, 1, 0)
        index += 1

        mesh['vertex'][index] = (0, 0, 0)
        mesh['color'][index] = color(phi)
        mesh['normal'][index] = (0, 1, 0)
        index += 1

        mesh['vertex'][index] = (r*np.cos(phi_range[i]), -h, r*np.sin(phi_range[i]))
        mesh['color'][index] = color(phi)
        mesh['normal'][index] = (0, -1, 0)
        index += 1

        mesh['vertex'][index] = (r*np.cos(phi_range[i+1]), -h, r*np.sin(phi_range[i+1]))
        mesh['color'][index] = color(phi)
        mesh['normal'][index] = (0, -1, 0)
        index += 1

        mesh['vertex'][index] = (0, -h, 0)
        mesh['color'][index] = color(phi)
        mesh['normal'][index] = (0, -1, 0)
        index += 1

        # walls
        mesh['vertex'][index] = (r*np.cos(phi_range[i]), 0, r*np.sin(phi_range[i]))
        mesh['color'][index] = color(phi)
        mesh['normal'][index] = (r*np.cos(phi_range[i]), 0, r*np.sin(phi_range[i]))
        index += 1

        mesh['vertex'][index] = (r*np.cos(phi_range[i+1]), 0, r*np.sin(phi_range[i+1]))
        mesh['color'][index] = color(phi)
        mesh['normal'][index] = (r*np.cos(phi_range[i+1]), 0, r*np.sin(phi_range[i+1]))
        index += 1

        mesh['vertex'][index] = (r*np.cos(phi_range[i]), -h, r*np.sin(phi_range[i]))
        mesh['color'][index] = color(phi)
        mesh['normal'][index] = (r*np.cos(phi_range[i]), 0, r*np.sin(phi_range[i]))
        index += 1

        mesh['vertex'][index] = (r*np.cos(phi_range[i]), -h, r*np.sin(phi_range[i]))
        mesh['color'][index] = color(phi)
        mesh['normal'][index] = (r*np.cos(phi_range[i]), 0, r*np.sin(phi_range[i]))
        index += 1

        mesh['vertex'][index] = (r*np.cos(phi_range[i+1]), -h, r*np.sin(phi_range[i+1]))
        mesh['color'][index] = color(phi)
        mesh['normal'][index] = (r*np.cos(phi_range[i+1]), 0, r*np.sin(phi_range[i+1]))
        index += 1

        mesh['vertex'][index] = (r*np.cos(phi_range[i+1]), 0, r*np.sin(phi_range[i+1]))
        mesh['color'][index] = color(phi)
        mesh['normal'][index] = (r*np.cos(phi_range[i+1]), 0, r*np.sin(phi_range[i+1]))
        index += 1


    return mesh
def mesh3d_sphere(prec=50, r=1, color=(.5, .5, .5, 1)):
    """ creates a sphere mesh with a certain precision prec
        and a radius r """
    if not callable(color):
        b = color
        del color
        color = lambda *a: b

    theta_range = [np.pi / prec * theta for theta in range(prec+1)]
    theta_range[-1] = np.pi

    phi_range = [2 * np.pi / prec * phi for phi in range(prec+1)]
    phi_range[-1] = 0

    mesh = np.zeros((prec-1) * prec * 6, dtype=MESH_DTYPE)
    sphere_vec = lambda theta, phi: (r * np.sin(theta) * np.cos(phi), r * np.sin(theta) * np.sin(phi), r * np.cos(theta))
    index = 0
    for i in range(prec-1):
        for j in range(prec):
            v = sphere_vec(theta_range[i], phi_range[j])
            mesh['vertex'][index] = v
            mesh['color'][index] = color(theta_range[i], phi)
            mesh['normal'][index] = v
            index += 1

            v = sphere_vec(theta_range[i+1], phi_range[j])
            mesh['vertex'][index] = v
            mesh['color'][index] = color(theta_range[i+1], phi)
            mesh['normal'][index] = v
            index += 1

            v = sphere_vec(theta_range[i+1], phi_range[j+1])
            mesh['vertex'][index] = v
            mesh['color'][index] = color(theta_range[i+1], phi)
            mesh['normal'][index] = v
            index += 1

            v = sphere_vec(theta_range[i+1], phi_range[j])
            mesh['vertex'][index] = v
            mesh['color'][index] = color(theta_range[i+1], phi)
            mesh['normal'][index] = v
            index += 1

            v = sphere_vec(theta_range[i+1], phi_range[j+1])
            mesh['vertex'][index] = v
            mesh['color'][index] = color(theta_range[i+1], phi)
            mesh['normal'][index] = v
            index += 1

            v = sphere_vec(theta_range[i+2], phi_range[j+1])
            mesh['vertex'][index] = v
            mesh['color'][index] = color(theta_range[i+2], phi)
            mesh['normal'][index] = v
            index += 1

    return mesh

def mesh3d_rectangle(a=1, b=1, color=(1, 1, 1, 1), center=(0, 0)):
    if not callable(color):
        _color = color
        del color
        color = lambda a: _color

    mesh = np.zeros(6, dtype=MESH_DTYPE)

    i = 0
    mesh['vertex'][i] = (center[0], center[1], 0)
    mesh['color'][i] = color(i)
    mesh['normal'][i] = (0, 0, 1)
    mesh['tex'][i] = (0, 1)

    i += 1
    mesh['vertex'][i] = (center[0]+a, center[1], 0)
    mesh['color'][i] = color(i)
    mesh['normal'][i] = (0, 0, 1)
    mesh['tex'][i] = (1, 1)

    i += 1
    mesh['vertex'][i] = (center[0]+a, center[1]+b, 0)
    mesh['color'][i] = color(i)
    mesh['normal'][i] = (0, 0, 1)
    mesh['tex'][i] = (1, 0)

    i += 1
    mesh['vertex'][i] = (center[0]+0, center[1]+b, 0)
    mesh['color'][i] = color(i)
    mesh['normal'][i] = (0, 0, 1)
    mesh['tex'][i] = (0, 0)

    i += 1
    mesh['vertex'][i] = (center[0]+0, center[1], 0)
    mesh['color'][i] = color(i)
    mesh['normal'][i] = (0, 0, 1)
    mesh['tex'][i] = (0, 1)

    i += 1
    mesh['vertex'][i] = (center[0]+a, center[1]+b, 0)
    mesh['color'][i] = color(i)
    mesh['normal'][i] = (0, 0, 1)
    
    mesh['tex'][i] = (1, 0)
    return mesh

def mesh3d_cube(a=1, b=1, c=1, color=(1, 1, 1, 1)):
    if not callable(color):
        b = color
        del color
        color = lambda a: b
    mesh = np.zeros(12*3, dtype=MESH_DTYPE)
    i = 0
    mesh['vertex'][i] = (0, 0, 0)
    mesh['color'][i] = color(i)
    mesh['normal'][i] = (0, 0, 1)
    i += 1
    mesh['vertex'][i] = (100, 100, 0)
    mesh['color'][i] = color(i)
    mesh['normal'][i] = (0, 0, 1)
    i += 1
    mesh['vertex'][i] = (100, 0, 0)
    mesh['color'][i] = color(i)
    mesh['normal'][i] = (0, 0, 1)
    i += 1
    mesh['vertex'][i] = (0, 0, 0)
    mesh['color'][i] = color(i)
    mesh['normal'][i] = (0, 0, 1)
    i += 1
    mesh['vertex'][i] = (0, 100, 0)
    mesh['color'][i] = color(i)
    mesh['normal'][i] = (0, 0, 1)
    i += 1
    mesh['vertex'][i] = (100, 100, 0)
    mesh['color'][i] = color(i)
    mesh['normal'][i] = (0, 0, 1)

    i += 1
    mesh['vertex'][i] = (100, 0, -100)
    mesh['color'][i] = color(i)
    mesh['normal'][i] = (0, 0, -1)
    i += 1
    mesh['vertex'][i] = (100, 100, -100)
    mesh['color'][i] = color(i)
    mesh['normal'][i] = (0, 0, -1)
    i += 1
    mesh['vertex'][i] = (0, 0, -100)
    mesh['color'][i] = color(i)
    mesh['normal'][i] = (0, 0, -1)
    i += 1
    mesh['vertex'][i] = (100, 100, -100)
    mesh['color'][i] = color(i)
    mesh['normal'][i] = (0, 0, -1)
    i += 1
    mesh['vertex'][i] = (0, 100, -100)
    mesh['color'][i] = color(i)
    mesh['normal'][i] = (0, 0, -1)
    i += 1
    mesh['vertex'][i] = (0, 0, -100)
    mesh['color'][i] = color(i)
    mesh['normal'][i] = (0, 0, -1)

    i += 1
    mesh['vertex'][i] = (0, 100, 0)
    mesh['color'][i] = color(i)
    mesh['normal'][i] = (0, 1, 0)
    i += 1
    mesh['vertex'][i] = (0, 100, -100)
    mesh['color'][i] = color(i)
    mesh['normal'][i] = (0, 1, 0)
    i += 1
    mesh['vertex'][i] = (100, 100, -100)
    mesh['color'][i] = color(i)
    mesh['normal'][i] = (0, 1, 0)
    i += 1
    mesh['vertex'][i] = (0, 100, 0)
    mesh['color'][i] = color(i)
    mesh['normal'][i] = (0, 1, 0)
    i += 1
    mesh['vertex'][i] = (100, 100, -100)
    mesh['color'][i] = color(i)
    mesh['normal'][i] = (0, 1, 0)
    i += 1
    mesh['vertex'][i] = (100, 100, 0)
    mesh['color'][i] = color(i)
    mesh['normal'][i] = (0, 1, 0)
    i += 1


    mesh['vertex'][i] = (0, 0, -100)
    mesh['color'][i] = color(i)
    mesh['normal'][i] = (0, -1, 0)
    i += 1
    mesh['vertex'][i] = (0, 0, 0)
    mesh['color'][i] = color(i)
    mesh['normal'][i] = (0, -1, 0)
    i += 1
    mesh['vertex'][i] = (100, 0, -100)
    mesh['color'][i] = color(i)
    mesh['normal'][i] = (0, -1, 0)
    i += 1
    mesh['vertex'][i] = (0, 0, 0)
    mesh['color'][i] = color(i)
    mesh['normal'][i] = (0, -1, 0)
    i += 1
    mesh['vertex'][i] = (100, 0, 0)
    mesh['color'][i] = color(i)
    mesh['normal'][i] = (0, -1, 0)
    i += 1
    mesh['vertex'][i] = (100, 0, -100)
    mesh['color'][i] = color(i)
    mesh['normal'][i] = (0, -1, 0)
    i += 1



    mesh['vertex'][i] = (100, 0, -100)
    mesh['color'][i] = color(i)
    mesh['normal'][i] = (1, 0, 0)
    i += 1
    mesh['vertex'][i] = (100, 0, 0)
    mesh['color'][i] = color(i)
    mesh['normal'][i] = (1, 0, 0)
    i += 1
    mesh['vertex'][i] = (100, 100, -100)
    mesh['color'][i] = color(i)
    mesh['normal'][i] = (1, 0, 0)
    i += 1
    mesh['vertex'][i] = (100, 0, 0)
    mesh['color'][i] = color(i)
    mesh['normal'][i] = (1, 0, 0)
    i += 1
    mesh['vertex'][i] = (100, 100, 0)
    mesh['color'][i] = color(i)
    mesh['normal'][i] = (1, 0, 0)
    i += 1
    mesh['vertex'][i] = (100, 100, -100)
    mesh['color'][i] = color(i)
    mesh['normal'][i] = (1, 0, 0)
    i += 1

    mesh['vertex'][i] = (0, 0, 0)
    mesh['color'][i] = color(i)
    mesh['normal'][i] = (-1, 0, 0)
    i += 1
    mesh['vertex'][i] = (0, 0, -100)
    mesh['color'][i] = color(i)
    mesh['normal'][i] = (-1, 0, 0)
    i += 1
    mesh['vertex'][i] = (0, 100, -100)
    mesh['color'][i] = color(i)
    mesh['normal'][i] = (-1, 0, 0)
    i += 1
    mesh['vertex'][i] = (0, 0, 0)
    mesh['color'][i] = color(i)
    mesh['normal'][i] = (-1, 0, 0)
    i += 1
    mesh['vertex'][i] = (0, 100, -100)
    mesh['color'][i] = color(i)
    mesh['normal'][i] = (-1, 0, 0)
    i += 1
    mesh['vertex'][i] = (0, 100, 0)
    mesh['color'][i] = color(i)
    mesh['normal'][i] = (-1, 0, 0)
    i += 1


    return mesh