#-*- coding: utf-8 -*-
"""
using texture utilities to create a random texture which
is regenerated each rendering cycle.

:author: Nicolas 'keksnicoh' Heimann
"""

from gpupy.gl.glfw import GLFW_WindowFunction
from gpupy.gl.texture import Texture3D
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

        camera = Camera(self.window.get_size(), projection=Camera.PROJECTION_PERSPECTIVE)
        camera.translate(x=0, y=-200, z=-1000)
        vertex_shader = Shader(GL_VERTEX_SHADER, """
            {% version %}
            {% uniform_block camera %}

            in vec3 center;
            in vec3 upper_left;
            in vec3 upper_right;
            in float depth;

            out vec3 geom_center;
            out vec3 geom_ul;
            out vec3 geom_ur;
            out float geom_d;
            void main() {
                geom_center = center;
                geom_ur = upper_right;
                geom_ul = upper_left;
                geom_d = depth;
            }
        """)
        geometry_shader = Shader(GL_GEOMETRY_SHADER, """
            {% version %}
            {% uniform_block camera %}

            layout (points) in;
            layout (triangle_strip) out;
            layout (max_vertices=4) out;

            in vec3 geom_center[1];
            in vec3 geom_ul[1];
            in vec3 geom_ur[1];
            in float geom_d[1];

            out vec4 frg_col;
            out vec3 frg_pos;

            void main(void)
            {
            if (geom_ul[0].x == 0|| geom_ur[0].x == 0|| geom_center[0].x == 0) {} 

                gl_Position = camera.mat_projection*camera.mat_view*(vec4(camera.direction * geom_center[0].xyz, 1) + vec4(geom_center[0].xy + geom_ur[0].xy, geom_ur[0].z, 1));
                frg_col = vec4(1,0,0,geom_d[0]);
                frg_pos = vec3(0, 0, geom_d[0]);
                EmitVertex();

                gl_Position = camera.mat_projection*camera.mat_view*(vec4(camera.direction * geom_center[0].xyz, 1) + vec4(geom_center[0].xy - geom_ul[0].xy, geom_ul[0].z, 1));
                frg_col = vec4(0, 1,0,geom_d[0]);
                frg_pos = vec3(0, 1, geom_d[0]);

                EmitVertex();

                gl_Position = camera.mat_projection*camera.mat_view*(vec4(camera.direction * geom_center[0].xyz, 1) + vec4(geom_center[0].xy + geom_ul[0].xy, geom_ul[0].z, 1));
                frg_col = vec4(0,0,1,1);
                frg_pos = vec3(1, 0, geom_d[0]);

                EmitVertex();

                gl_Position = camera.mat_projection*camera.mat_view*(vec4(camera.direction * geom_center[0].xyz, 1) + vec4(geom_center[0].xy - geom_ur[0].xy, geom_ur[0].z, 1));
                frg_col = vec4(1,1,0,geom_d[0]);
                frg_pos = vec3(1, 1, geom_d[0]);

                EmitVertex();

                EndPrimitive();

            }

        """)
        fragment_shader = Shader(GL_FRAGMENT_SHADER, """
            {% version %}
            out vec4 frag_color;
            uniform sampler3D tex[1];
            in vec4 frg_col;
            in vec3 frg_pos;
            float val;
            void main() {
            if (frg_col.x == 1){}
                val = texture(tex[0], frg_pos).r;
                if (val < 0.15 || val > 0.16) {
                    frag_color = vec4(0, 1, 0, 0.01*val);
                }
                else {
                    frag_color = vec4(1, 0, 0, val);
                }
            }
            
        """)
        program = Program()
        program.shaders.append(vertex_shader)
        program.shaders.append(fragment_shader)
        program.shaders.append(geometry_shader)
        program.declare_uniform('camera', camera, variable='camera')
        program.link()

        program.uniform_block_binding('camera', camera)
        rect_size     = self.window.get_size();
        rect_position = (-rect_size[0]/2, -rect_size[1]/2)

        pn = 50
        ball_data = np.array(
            [np.sqrt((x-pn/2)**2+(y-pn/2)**2+(z-pn/2)**2)/pn/2  for z in range(pn) for x in range(pn) for y in range(0, pn) ],
            dtype=np.float32).reshape((pn, pn, pn))
        self.texture = Texture3D.from_numpy(ball_data)
        self.texture.interpolation_linear()

        ln = 200
        self.layer_buffer = BufferObject.to_device(np.array(
            [((0, 0, 100*float(x)/ln), (-100, 100, 100*float(x)/ln), (100, 100, 100*float(x)/ln), float(x)/ln) for x in range(0, ln)],
            dtype=np.dtype([
                ('center', np.float32, 3),
                ('upper_left', np.float32, 3),
                ('upper_right', np.float32, 3),
                ('depth', np.float32),
            ])))

        self.render_data        = BufferObject.to_device(mesh3d_rectangle(center=rect_position, *rect_size))
        self.vao                = create_vao_from_program_buffer_object(program, self.layer_buffer)
        self.program            = program
        self.camera             = camera
        self.keyboard_flyaround = keyboard_flyaround()


    def draw(self):
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        self.keyboard_flyaround(self.camera, self.window.keyboard.active)
        self.program.use()
        self.texture.bind()
        glActiveTexture(GL_TEXTURE0);
        self.program.uniform('tex', 0)

        glBindVertexArray(self.vao)
        glDrawArrays(GL_POINTS, 0, len(self.layer_buffer))
        glBindVertexArray(0)

        self.texture.unbind()
        self.program.unuse()

 

@GLFW_WindowFunction
def main(window):
    texture_controller = TextureContorller(window)

if __name__ == '__main__':
    main()