#-*- coding: utf-8 -*-
"""
using texture utilities to create a random texture which
is regenerated each rendering cycle.

:author: Nicolas 'keksnicoh' Heimann
"""

from gpupy.gl.glfw import bootstrap_gl, create_runner, GLFW_Window
from gpupy.gl.texture import Texture2D
from gpupy.gl.buffer import BufferObject, create_vao_from_program_buffer_object
from gpupy.gl.shader import Program, Shader
from gpupy.gl.glx.camera import Cartesian2D
from gpupy.gl.mesh import mesh3d_rectangle
from gpupy.gl.lib import attributes
from gpupy.gl import GPUPY_GL
from OpenGL.GL import *
import numpy as np


class TextureContorller():
    size = attributes.VectorAttribute(2)
    def __init__(self, size):
        self.size = size
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA);

        vertex_shader = Shader(GL_VERTEX_SHADER, """
            {% version %}
            {% uniform_block camera %}
            in vec4 vertex;
            in vec2 tex;
            out vec2 fragment_position;
            void main() {
                fragment_position = tex;
                gl_Position = camera.mat_projection * camera.mat_view * vertex;
            }
        """)
        fragment_shader = Shader(GL_FRAGMENT_SHADER, """
            {% version %}
            out vec4 frag_color;
            uniform sampler2D tex[1];
            in vec2 fragment_position;
            void main() {
                frag_color = texture(tex[0], fragment_position);
            }
        """)
        program = Program()
        program.shaders.append(vertex_shader)
        program.shaders.append(fragment_shader)
        program.declare_uniform('camera', Cartesian2D.DTYPE, variable='camera')
        program.link()

        program.uniform_block_binding('camera', GPUPY_GL.CONTEXT.buffer_base('gpupy.gl.camera'))
        rect_size     = self.size;
        rect_position = (-rect_size[0]/2, -rect_size[1]/2)

        self.texture            = Texture2D.from_numpy(np.random.random((500, 500, 3)).astype(np.float32))
        self.render_data        = BufferObject.to_device(mesh3d_rectangle(center=rect_position, *rect_size))
        self.vao                = create_vao_from_program_buffer_object(program, self.render_data)
        self.program            = program
        #self.keyboard_flyaround = keyboard_flyaround()
        self.step               = 1
        self.last_random        = 1

        self.texture.interpolation_linear()

    def __call__(self):
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        #self.keyboard_flyaround(self.camera, self.window.keyboard.active)

        self.program.use()
        self.texture.bind()
        glActiveTexture(GL_TEXTURE0);

        glBindVertexArray(self.vao)
        glDrawArrays(GL_TRIANGLES, 0, len(self.render_data))
        glBindVertexArray(0)

        self.texture.unbind()
        self.program.unuse()

        # do some funny stuff
        if self.last_random > 0.1:
            channels = 4
            size = 500
        elif self.last_random > 0.04:
            channels = 3
            size = 300
        elif self.last_random > 0.02:
            channels = 2
            size = 700
        else:
            channels = 1
            size = 50

        new_data = np.random.random((size, size, channels))
        new_data[:][self.step%size] = 1
        new_data[:][(2*self.step)%size] = 1
        new_data[:][(3*self.step)%size] = 1
        new_data[:][(4*self.step)%size] = 1

        self.texture.load(new_data.astype(np.float32))

        self.last_random = new_data[0][0][0]
        self.step += 1
        return True

def main():
    bootstrap_gl()
    window = GLFW_Window()
    windows = [window]
    camera = Cartesian2D(screensize=window.size)
 
    window.widget = TextureContorller(size=window.size)
    for window in create_runner(windows):
        if not window():
            windows.remove(window)



if __name__ == '__main__':
    main()
else:
    raise Exception('please run as __main__.')
