#-*- coding: utf-8 -*-
"""
using texture utilities to create a random texture which
is regenerated each rendering cycle.

:author: Nicolas 'keksnicoh' Heimann
"""

from gpupy.gl.driver.glfw import GLFW_WindowFunction
from gpupy.gl.texture import Texture2D
from gpupy.gl.buffer import BufferObject, create_vao_from_program_buffer_object
from gpupy.gl.shader import Program, Shader
from gpupy.gl.camera import Camera, keyboard_flyaround
from gpupy.gl.mesh import mesh3d_rectangle
from OpenGL.GL import *
import numpy as np


class TextureContorller():
    def __init__(self, window):
        self.window = window
        window.on_init.append(self.init)
        window.on_cycle.append(self.draw)

    def init(self):
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA);

        camera = Camera(self.window.get_size(), projection=Camera.PROJECTION_ORTHOGRAPHIC)
        camera.translate(x=0, y=0, z=-1)
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
        program.declare_uniform('camera', camera, variable='camera')
        program.link()

        program.uniform_block_binding('camera', camera)
        rect_size     = self.window.get_size();
        rect_position = (-rect_size[0]/2, -rect_size[1]/2)

        self.texture            = Texture2D.from_numpy(np.random.random((500, 500, 3)).astype(np.float32))
        self.render_data        = BufferObject.to_device(mesh3d_rectangle(center=rect_position, *rect_size))
        self.vao                = create_vao_from_program_buffer_object(program, self.render_data)
        self.program            = program
        self.camera             = camera
        self.keyboard_flyaround = keyboard_flyaround()
        self.step               = 1
        self.last_random        = 1

        self.texture.interpolation_linear()

    def draw(self):
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        self.keyboard_flyaround(self.camera, self.window.keyboard.active)

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


@GLFW_WindowFunction
def main(window):
    texture_controller = TextureContorller(window)

if __name__ == '__main__':
    main()