#-*- coding: utf-8 -*-
"""
ray casting

:author: Nicolas 'keksnicoh' Heimann
"""

from gpupy.gl.driver.glfw import GLFW_WindowFunction
from gpupy.gl.texture import Texture3D, Texture2D
from gpupy.gl.buffer import BufferObject, create_vao_from_program_buffer_object
from gpupy.gl.shader import Program, Shader
from gpupy.gl.camera import Camera, keyboard_flyaround
from gpupy.gl.mesh import mesh3d_cube, mesh3d_rectangle
from gpupy.gl.framebuffer import Framebuffer
from OpenGL.GL import *
import numpy as np
from gpupy.gl import GlConfig
from functools import partial 

CUBE_TEXTURE_SIZE = (400, 400)

GlConfig.DEBUG = True
class RaycastingController():
    def __init__(self, window):
        self.window = window
        window.on_init.append(self.init)
        window.on_cycle.append(self.draw)
        window.on_resize.append(self.resize)

    def resize(self):
        self.camera.set_screensize(self.window.get_size())
        self.draw()
        
    def init(self):

        glEnable(GL_BLEND)
        glEnable(GL_DEPTH_TEST)
        glDepthFunc(GL_LESS)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA);
        glFrontFace(GL_CW); 
        
        camera = Camera(self.window.get_size(), 
                        projection=Camera.PROJECTION_PERSPECTIVE)
        camera.translate(x=0, y=-10, z=-300)
       # self.window.on_framebuffer_resize.append(camera.set_capturesize)

        ray_program = Program()
        ray_program.shaders.append(Shader(GL_VERTEX_SHADER, """
            {% version %}
            {% uniform_block camera %}
            in vec3 vertex;
            out vec3 frag_position;
            void main() {
                gl_Position = camera.mat_projection * camera.mat_view * vec4(vertex, 1);    
                frag_position = vec3(vertex.x / 100, vertex.y / 100, -vertex.z/100);
            }
        """))
        ray_program.shaders.append(Shader(GL_FRAGMENT_SHADER, """
            {% version %}
            out vec4 frag_color;
            vec3 position;
            in vec3 frag_position;
            void main() {
                position = frag_position;
                frag_color = vec4(position, 1);
            }
            
        """))
        ray_program.declare_uniform('camera', camera, variable='camera')
        ray_program.link()

        shader_program = Program()
        shader_program.shaders.append(Shader(GL_VERTEX_SHADER, """
            {% version %}
            in vec4 vertex;
            in vec2 tex;
            out vec2 fragment_position;
            void main() {
                fragment_position = tex;
                gl_Position = vertex;
            }
        """))
        shader_program.shaders.append(Shader(GL_FRAGMENT_SHADER, """
           {% version %}
            out vec4 frag_color;
            uniform sampler2D tex;
            uniform sampler2D back;
            uniform sampler3D vol;
            in vec2 fragment_position;

            vec4 cf;
            vec4 cb;
            vec3 dir;

            // sample size
            float ds = 0.005;

            // current beam position
            vec3 p;

            vec4 c;
            vec4 dst;

            float a;
            void main() {
                cf = texture(tex, fragment_position);
                cb = texture(back, fragment_position);

                if (cb.w > 0 || cf.w > 0) {
                    dst = vec4(0, 0, 0, 0);
                    p = cf.xyz;
                    dir = normalize(cb.xyz - cf.xyz);
                    for (int i = 0; i < 400; i ++) {
                        c = vec4(texture(vol, p).r);
                        c.w *= 0.2;
                        c.rgb *= c.w;
                        dst = (1.0f - dst.a) * c + dst;
                        if (dst.a > 0.95f) {
                            break;
                        }
                        p += ds * dir;   
                        if(p.x > 1.0f && p.y > 1.0f && p.z > 1.0f) {
                            break;
                        }
                    }
                    frag_color = dst;
                }
                else {
                    frag_color = vec4(0, 0, 0, 0);
                }
            }

        """))
        shader_program.link()

        ray_program.uniform_block_binding('camera', camera)
        rect_size     = self.window.get_size();
        rect_position = (-rect_size[0]/2, -rect_size[1]/2)

        self.cube_buffer = BufferObject.to_device(mesh3d_cube())
        self.vao = create_vao_from_program_buffer_object(ray_program, self.cube_buffer)
        
        self.shader_program = shader_program
        self.ray_program = ray_program

        self.camera = camera
        self.keyboard_flyaround = keyboard_flyaround()

        # create texture for front and backside
        #
        # since we'll use the same camera inside the framebuffer we have
        # to put the framebuffer size to the size of the main window framebuffer.
        # 
        # otherwise we could scale the camera to compensate the difference in window
        # size and framebuffer size.
        self.texture_front = Texture2D.empty((*CUBE_TEXTURE_SIZE, 4), np.float32)
        self.framebuffer_front = Framebuffer()
        self.framebuffer_front.color_attachment(self.texture_front)

        self.texture_back = Texture2D.empty((*CUBE_TEXTURE_SIZE, 4), np.float32)
        self.framebuffer_back = Framebuffer()
        self.framebuffer_back.color_attachment(self.texture_back)

        # e.g. retina support 
       # self.window.on_framebuffer_resize.append(self.texture_front.resize)
       # self.window.on_framebuffer_resize.append(self.texture_back.resize)
       # self.window.on_framebuffer_resize.append(partial(setattr, self, 'force_viewbox_render'))

        rect_size = [2,2]
        rect_position = (-rect_size[0]/2, -rect_size[1]/2)
        self.screen_buffer = BufferObject.to_device(mesh3d_rectangle(center=rect_position, *rect_size))
        self.screen_vao = create_vao_from_program_buffer_object(shader_program, self.screen_buffer)

        pn = 100
        ball_data = np.array(
            [(x == 20 and y==20 
           or x == 10 and z==20
           or x == 15 and z==20
           or x == 25 and z==20
           or x == 35 and z==20
           or x**2 + y**2 + z**2< 2000 and x**2 + y**2 + z**2 > 1500) and 1 for z in range(pn) for x in range(pn) for y in range(0, pn) ],
          #  [x > 10 and y > 10 and z > 10 and np.sqrt((x-pn/2)**2+(y-pn/2)**2+(z-pn/2)**2)/pn/2  for z in range(pn) for x in range(pn) for y in range(0, pn) ],

            dtype=np.float32).reshape((pn, pn, pn))
        self.texture = Texture3D.from_numpy(ball_data)
        self.texture.interpolation_linear()

        self.texture.parameter(GL_TEXTURE_WRAP_S, GL_CLAMP_TO_BORDER)
        self.texture.parameter(GL_TEXTURE_WRAP_T, GL_CLAMP_TO_BORDER)
        self.texture.parameter(GL_TEXTURE_WRAP_R, GL_CLAMP_TO_BORDER)

        self.shader_program.uniform('tex', self.texture_front.activate(0))
        self.shader_program.uniform('back', self.texture_back.activate(1))
        self.shader_program.uniform('vol', self.texture.activate(2))

        self.force_viewbox_render = True

    def draw(self):
       # print(glGetIntegerv(GL_VIEWPORT))
       # glViewport(0, 0, *self.window.get_framebuffer_size())
        moved_keyboard = self.keyboard_flyaround(self.camera, self.window.keyboard.active)
        if moved_keyboard or self.force_viewbox_render:
            old_viewport = glGetIntegerv(GL_VIEWPORT)
            glViewport(0, 0, *CUBE_TEXTURE_SIZE)
            glEnable(GL_CULL_FACE); 
            glClearColor(0, 0, 0, 0)
            self.ray_program.use()

            # render front faces
            self.framebuffer_front.use()
            glCullFace(GL_FRONT); 
            glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
            glBindVertexArray(self.vao)
            glDrawArrays(GL_TRIANGLES, 0, len(self.cube_buffer))
            glBindVertexArray(0)
            self.framebuffer_front.unuse()

            # render back faces
            self.framebuffer_back.use()
            glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
            glCullFace(GL_BACK); 
            glBindVertexArray(self.vao)
            glDrawArrays(GL_TRIANGLES, 0, len(self.cube_buffer))
            glBindVertexArray(0)
            self.framebuffer_back.unuse()

            self.ray_program.unuse()
            glDisable(GL_CULL_FACE); 
            self.force_viewbox_render = False
            glViewport(*old_viewport)
        glClearColor(0, 0, 0, 0)
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

        # render box
        self.ray_program.use()
        glBindVertexArray(self.vao)
        glDrawArrays(GL_TRIANGLES, 0, len(self.cube_buffer))
        glBindVertexArray(0)
        self.ray_program.unuse()

        # render 3d texture using ray casting
        self.shader_program.use()
        glBindVertexArray(self.screen_vao)
        glDrawArrays(GL_TRIANGLES, 0, len(self.screen_buffer))
        glBindVertexArray(0)
        self.shader_program.unuse()

@GLFW_WindowFunction
def main(window):
    texture_controller = RaycastingController(window)

if __name__ == '__main__':
    main()