#-*- coding: utf-8 -*-
"""
using gpupy components to render a time dependent 
random texture on a 2d plane.

:author: keksnicoh
"""

from gpupy.gl import glfw
from gpupy.gl.glx.camera import Cartesian2D
from gpupy.gl.mesh import mesh3d_rectangle, StridedVertexMesh
from gpupy.gl.lib import attributes
from gpupy.gl import GPUPY_GL, create_program, Texture2D

from OpenGL.GL import *

import numpy as np


VERTEX_SHADER = """
    {% version %}
    {% uniform_block camera %}
    in vec4 vertex;
    in vec2 tex;
    out vec2 fragment_position;
    void main() {
        fragment_position = tex;
        gl_Position = camera.mat_projection * camera.mat_view * vertex;
    }
"""


FRAGMENT_SHADER = """
    {% version %}
    out vec4 frag_color;
    uniform sampler2D tex[1];
    in vec2 fragment_position;
    void main() {
        frag_color = texture(tex[0], fragment_position);
    }
"""


class TextWidget():
    size = attributes.VectorAttribute(2)

    def __init__(self, size):
        self.size = size
        self.init()


    def init(self):
        # note that in Widget init the context should be active!
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA);

        self.program  = create_program(vertex=VERTEX_SHADER, fragment=FRAGMENT_SHADER, link=False)

        # the shader uses {% uniform block %} tags which we must
        # declare before linking the program
        self.program.declare_uniform('camera', Cartesian2D.DTYPE, variable='camera')
        self.program.link()

        # we need to tell the shader which is is buffer base.
        # the GPUPY_GL.CONTEXT.buffer_base returns a free buffer
        # base which is reserved for the active context. 
        self.program.uniform_blocks['camera'] = GPUPY_GL.CONTEXT.buffer_base('gpupy.gl.camera')

        # the mesh represents VAO and VBO
        self.mesh = StridedVertexMesh(
            mesh3d_rectangle(center=(-self.size[0]/2, -self.size[1]/2), *self.size), 
            GL_TRIANGLES, 
            attribute_locations=self.program.attributes)

        # create texture and buffers
        self.texture = Texture2D.from_numpy(np.random.random((500, 500, 3)).astype(np.float32))
        self.texture.interpolation_linear()
        self.texture.activate(0)

        self.step        = 1
        self.last_random = 1


    def __call__(self):
        # a widget is something which is callable.

        # render me
        glClear(GL_COLOR_BUFFER_BIT)
        self.program.use()
        self.texture.reactivate()
        self.mesh.draw()
        self.texture.unbind()
        self.program.unuse()

        # texture update
        self._update_data()

        # to keep the widget alive return True
        return True


    def _update_data(self):
        # do some funny stuff
        if self.last_random > 0.1:
            channels, size = 4, 500
        elif self.last_random > 0.04:
            channels, size = 3, 300
        elif self.last_random > 0.02:
            channels, size = 2, 700
        else:
            channels, size = 1, 50
        new_data = np.random.random((size, size, channels))
        new_data[:][self.step%size] = 1
        new_data[:][(2*self.step)%size] = 1
        new_data[:][(3*self.step)%size] = 1
        new_data[:][(4*self.step)%size] = 1
        self.texture.load(new_data.astype(np.float32))
        self.last_random = new_data[0][0][0]
        self.step += 1


if __name__ == '__main__':
    glfw.bootstrap_gl()

    window = glfw.GLFW_Window()
    window.widget = TextWidget(size=window.size)
    camera = Cartesian2D(screensize=window.size)

    # window resize => rerender widget. 
    window.on_resize.append(lambda *e: window.widget())

    # let the camera roll
    window.on_cycle.append(lambda *e: camera.__setattr__('roll', camera.roll+0.01))

    # run the app
    glfw.run(window)

else:
    raise Exception('please run as __main__.')
