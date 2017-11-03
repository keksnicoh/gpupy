#-*- coding: utf-8 -*-
"""
ray casting demo using gpupy lib

still under construction yo 

:author: Nicolas 'keksnicoh' Heimann
"""
from gpupy.gl.mesh import mesh3d_cube, mesh3d_rectangle # XXX
from gpupy.gl.glfw import GLFW_window # XXX

from gpupy.gl.buffer import create_vao_from_program_buffer_object
from gpupy.gl.glx.camera import Perspective3D
from gpupy.gl.lib import attributes, Event
from gpupy.gl.lib.matrix import mat4_rot_y, mat4_translation, mat4_rot_x
from gpupy.gl import GPUPY_GL, BufferObject, Texture3D, Texture2D, Framebuffer, create_program
from OpenGL.GL import *

import numpy as np
import dicom 
import os 
from time import time 
import glob

CUBE_FRAMEBUFFER = (400, 400)
DATA = 'geometric1.npy'
#DATA = 'test.npy'

V_ITER = 200
V_DS = .0055
V_RAY = .2

def read_dicom_dir(dicom_dir, wildcard=''):
    shape = None
    layer = []
    os.chdir(dicom_dir)
    for file in glob.glob('IM*'):
        ds = dicom.read_file(os.path.join(dicom_dir, file))
        if shape is None:
            shape = ds.pixel_array.shape
        elif shape != ds.pixel_array.shape:
            #shape = ds.pixel_array.shape
            #layer = []
            raise Exception('dicom data "{}" has differn shape {} vs. {}'.format(file, shape, ds.pixel_array.shape))
        layer.append(ds.pixel_array)

    if shape is None:
        raise Exception('could not read {}/{}'.format(dicom_dir, wildcard))

    return np.array(layer, dtype=np.float32).reshape((len(layer), *shape))

class RaycastingDemoWidget():
    size = attributes.VectorAttribute(2)
    zoom = attributes.VectorAttribute(3, (1,1,1))
    rotation = attributes.VectorAttribute(3, (0, 0, 0))
    box_rotation = attributes.VectorAttribute(3, (0, 0, 0))

    def __init__(self, size, volumedata):
        self.size = size
        self.force_viewbox_render = True
        self.volumedata = volumedata
        self.init()


    @zoom.on_change
    @rotation.on_change
    def upload_mat_volume(self, *e):
        self.program_ray.uniform('mat_volume', 
            mat4_rot_x(self.rotation.x) 
            @ mat4_rot_y(self.rotation.y) 
            @ np.diag([self.zoom.x, self.zoom.x, self.zoom.x, 1])) 


    @box_rotation.on_change
    def upload_mat_model(self, *e):
        self.force_viewbox_render = True
        self.program_box.uniform('mat_model', 
            mat4_rot_x(self.box_rotation.x) 
            @ mat4_rot_y(self.box_rotation.y)) 

        
    def init(self):

        glEnable(GL_BLEND)
        glEnable(GL_DEPTH_TEST)
        glDepthFunc(GL_LESS)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA);
        glFrontFace(GL_CW); 


        self._create_shader()

        rect_size     = self.size;
        rect_position = (-rect_size[0]/2, -rect_size[1]/2)
        self.cube_buffer = BufferObject.to_device(mesh3d_cube((200, 200, 200), center=True))
        self.vao = create_vao_from_program_buffer_object(self.program_box, self.cube_buffer)


        # create texture for front and backside
        #
        # since we'll use the same camera inside the framebuffer we have
        # to put the framebuffer size to the size of the main window framebuffer.
        # w
        # otherwise we could scale the camera to compensate the difference in window
        # size and framebuffer size.
        self.texture_front = Texture2D.empty((*CUBE_FRAMEBUFFER, 4), np.float32)
        self.framebuffer_front = Framebuffer()
        self.framebuffer_front.color_attachment(self.texture_front)
        self.texture_back = Texture2D.empty((*CUBE_FRAMEBUFFER, 4), np.float32)
        self.framebuffer_back = Framebuffer()
        self.framebuffer_back.color_attachment(self.texture_back)

        # create framebuffer screen (this is the widget main screen)
        rect_size = [2,2]
        rect_position = (-rect_size[0]/2, -rect_size[1]/2)
        self.screen_buffer = BufferObject.to_device(mesh3d_rectangle(center=rect_position, *rect_size))
        self.screen_vao = create_vao_from_program_buffer_object(self.program_ray, self.screen_buffer)

        # create 3d texture 
        self.texture = Texture3D.from_numpy(self.volumedata)
        self.texture.interpolation_linear()
        self.texture.parameters.update({
            GL_TEXTURE_WRAP_S: GL_CLAMP_TO_BORDER,
            GL_TEXTURE_WRAP_T: GL_CLAMP_TO_BORDER,
            GL_TEXTURE_WRAP_R: GL_CLAMP_TO_BORDER 
        })

        self.program_ray.uniform({
            'tex': self.texture_front.activate(0),
            'back': self.texture_back.activate(1),
            'vol': self.texture.activate(2),  
            'v_ray': V_RAY,
            'v_iter': V_ITER,
            'mat_volume': np.array([
                0.5, 0, 0, 0,
                0, 0.5, 0, 0, 
                0, 0, 0.5, 0,
                0, 0, 0, 1.0
            ], dtype=np.float32) 
        })

        self.force_viewbox_render = True

        self.upload_mat_model()
        self.upload_mat_volume()

    def _create_shader(self):
        """ creates the ray casting shader and the
            raydirection box shader """
        self.program_box = create_program(
            vertex=BOX_VRT_SHADER, 
            fragment=BOX_FRG_SHADER, 
            link=False)
        self.program_box.declare_uniform('camera', Perspective3D.DTYPE, variable='camera')
        self.program_box.link()

        self.program_box.uniform_blocks['camera'] = GPUPY_GL.CONTEXT.buffer_base('gpupy.gl.camera')
        self.program_box.uniforms['mat_model'] = np.array([
            1, 0, 0, 0,
            0, 1, 0, 0, 
            0, 0, 1, 0,
            0, 0, 0, 1
        ], dtype=np.float32)

        self.program_ray = create_program(
            vertex=RAYCASTING_VRT_SHADER, 
            fragment=RAYCASTING_FRG_SHADER)


    def __call__(self):
        # check if we need to recalculate the culled
        # fron and back face frame buffers
        if self.force_viewbox_render:
            self._render_culled_box()
            self.force_viewbox_render = False

        # reset main frame
        glClearColor(0, 0, 0, 0)
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

        # box for debugging purpose
        glPolygonMode(GL_FRONT_AND_BACK, GL_LINE)
        self._render_box()
        glPolygonMode(GL_FRONT_AND_BACK, GL_FILL)

        # volumetric raycasting 
        self._render_raycast()

        return True 


    def _render_box(self):
        self.program_box.use()
        glBindVertexArray(self.vao)
        glDrawArrays(GL_TRIANGLES, 0, len(self.cube_buffer))
        glBindVertexArray(0)
        self.program_box.unuse()


    def _render_raycast(self):
        self.program_ray.use()
        glBindVertexArray(self.screen_vao)
        glDrawArrays(GL_TRIANGLES, 0, len(self.screen_buffer))
        glBindVertexArray(0)
        self.program_ray.unuse()

    
    def _render_culled_box(self):
        # prepare
        old_viewport = glGetIntegerv(GL_VIEWPORT)
        glViewport(0, 0, *CUBE_FRAMEBUFFER)
        glDisable(GL_DEPTH_TEST)
        glEnable(GL_CULL_FACE); 
        glClearColor(0, 0, 0, 0)
        self.program_box.use()

        # render front faces
        self.framebuffer_front.use()
        glCullFace(GL_FRONT); 
        glClear(GL_COLOR_BUFFER_BIT)
        glBindVertexArray(self.vao)
        glDrawArrays(GL_TRIANGLES, 0, len(self.cube_buffer))
        glBindVertexArray(0)
        self.framebuffer_front.unuse()

        # render back faces
        self.framebuffer_back.use()
        glClear(GL_COLOR_BUFFER_BIT)
        glCullFace(GL_BACK); 
        glBindVertexArray(self.vao)
        glDrawArrays(GL_TRIANGLES, 0, len(self.cube_buffer))
        glBindVertexArray(0)
        self.framebuffer_back.unuse()

        # restore
        self.program_box.unuse()
        glEnable(GL_DEPTH_TEST)
        glDisable(GL_CULL_FACE); 
        glViewport(*old_viewport)

from gpupy.gl.glfw import bootstrap_gl, create_runner, GLFW_Window

def main():
    global V_ITER, V_DS, V_RAY
    # 3d texture
    #volumedata = np.load(os.path.join(os.path.dirname(__file__), 'resources', DATA))
    #dicom_file = 'MR-MONO2-8-16x-heart'
    dicom_file = 'dragonfruit.dcm'
    #dicom_file = 'brokoli.dcm'
    #dicom_file = 'corn.dcm'
    ds = dicom.read_file(os.path.join(os.path.dirname(__file__), 'resources', dicom_file))
    volumedata = (ds.pixel_array / np.max(ds.pixel_array)).astype(np.float32)    
    volumedata = np.einsum('ijk->jki', volumedata)
  #  dicom_dir = os.path.join(os.path.dirname(__file__), 'resources', 'CT/SE000002')
  #  volumedata = read_dicom_dir(dicom_dir, 'IM*')
  #  volumedata = np.einsum('ijk->jki', volumedata / np.max(volumedata))

    bootstrap_gl()
    window = GLFW_Window()
    window.make_context()

    camera = Perspective3D(screensize=window.size, position=(0, 0, -400))

    texture_widget = RaycastingDemoWidget(camera.screensize, volumedata=volumedata)
    window.widget = texture_widget

    windows = [window]
    for window in create_runner(windows):    
        if window.active_keys:
            if 264 in window.active_keys:
                camera.position.z -= 10
                texture_widget.force_viewbox_render = True
            if 265 in window.active_keys:
                camera.position.z += 10
                texture_widget.force_viewbox_render = True



            # rotate volume if shift is active
            if 340 not in window.active_keys:
                if 65 in window.active_keys: #a
                    texture_widget.rotation.y += 0.1
                if 68 in window.active_keys: #d
                    texture_widget.rotation.y -= 0.1
                if 87 in window.active_keys: #w
                    texture_widget.rotation.x += 0.1
                if 83 in window.active_keys: #s
                    texture_widget.rotation.x -= 0.1
            else: # rotate box
                if 65 in window.active_keys: #a
                    texture_widget.box_rotation.y += 0.1
                if 68 in window.active_keys: #d
                    texture_widget.box_rotation.y -= 0.1
                if 87 in window.active_keys: #w
                    texture_widget.box_rotation.x += 0.1
                if 83 in window.active_keys: #s
                    texture_widget.box_rotation.x -= 0.1

            print_info = False
            if 32 in window.active_keys and 340 not in window.active_keys:
                texture_widget.zoom *= 1.01
            if 32 in window.active_keys and 340 in window.active_keys:
                texture_widget.zoom *= 0.99

            #1
            if 49 in window.active_keys and 93 in window.active_keys:
                V_ITER += 1
                texture_widget.program_ray.uniform('v_iter', V_ITER)
                print_info = True
            if 49 in window.active_keys and 47 in window.active_keys:
                V_ITER = max(0, V_ITER -1)
                texture_widget.program_ray.uniform('v_iter', V_ITER)
                print_info = True

            #2
            if 50 in window.active_keys and 93 in window.active_keys:
                V_DS += 0.00001
                texture_widget.program_ray.uniform('v_ds', V_DS)
                print_info = True
            if 50 in window.active_keys and 47 in window.active_keys:
                V_DS = max(0.0001, V_DS -0.0001)
                texture_widget.program_ray.uniform('v_ds', V_DS)
                print_info = True

            # 3
            if 51 in window.active_keys and 93 in window.active_keys:
                V_RAY = min(1, V_RAY + 0.001)
                texture_widget.program_ray.uniform('v_ray', V_RAY)
                print_info = True
            if 51 in window.active_keys and 47 in window.active_keys:
                V_RAY = max(0, V_RAY - 0.001)
                texture_widget.program_ray.uniform('v_ray', V_RAY)
                print_info = True

            if print_info:
                print('V_ITER={}, V_DS={}, V_RAY={}, MAX={}'.format(V_ITER, V_DS, V_RAY, V_ITER*V_DS))
                
        if not window():
            windows.remove(window)

BOX_VRT_SHADER = """
    {% version %}
    {% uniform_block camera %}
    in vec3 vertex;
    out vec3 frag_position;
    uniform mat4 mat_model;
    void main() {
        gl_Position = camera.mat_viewprojection *  mat_model * vec4(vertex, 1);    
        frag_position = vec3(vertex.x / 200+.5, vertex.y / 200+.5, -vertex.z/200+.5);
    }
"""

BOX_FRG_SHADER = """
    {% version %}
    out vec4 frag_color;
    vec3 position;
    in vec3 frag_position;
    void main() {
        position = frag_position;
        frag_color = vec4(position, 1);
    }
    
"""

RAYCASTING_VRT_SHADER = """
    {% version %}
    in vec4 vertex;
    in vec2 tex;
    out vec2 fragment_position;
    void main() {
        fragment_position = vec2(tex.x, -tex.y);
        gl_Position = vertex;
    }
"""

RAYCASTING_FRG_SHADER = """
    {% version %}    
    in vec2 fragment_position;
    out vec4 frag_color;

    uniform sampler2D tex;
    uniform sampler2D back;
    uniform sampler3D vol;
    uniform mat4 mat_volume; 

    // raay casting configuration
    uniform float v_ds  = .005f;
    uniform int v_iter  = 400;
    uniform float v_ray = .2f;
    uniform float v_absorbed = .95f;

    vec4 cf;
    vec4 cb;
    vec3 dir;
    vec3 p;
    vec4 c;
    vec4 dst;
    vec3 dS;
    void main() {
        cf = texture(tex, vec2(fragment_position.x, fragment_position.y));
        cb = texture(back, vec2(fragment_position.x, fragment_position.y));

        // if at least one is positive we look 
        // into the 3d texture volume
        if (cb.w > 0 || cf.w > 0) {
            // init 
            dst = vec4(0, 0, 0, 0);
            p = cf.xyz;
            dir = normalize(cb.xyz-p);
            dS = v_ds * dir;
            for (int i = 0; i < v_iter; i ++) {
                c = vec4(texture(vol, (mat_volume * vec4(p-0.5,1)).xyz+0.5).r);
                c.w *= v_ray;
                c.rgb *= c.w;
                dst = (1.0f - dst.a) * c + dst;
                p += dS;   
            }
            frag_color = dst;
        }

        // here we are outside the cube
        else {
            frag_color = vec4(0.1, 0.1, 0.2, 0.9);
        }
    }
"""

#Maximum Intensity Projection
RAYCASTING_FRG_SHADERe = """
    {% version %}    
    in vec2 fragment_position;
    out vec4 frag_color;

    uniform sampler2D tex;
    uniform sampler2D back;
    uniform sampler3D vol;
    uniform mat4 mat_volume; 
    
    // raay casting configuration
    uniform float v_ds  = .005f;
    uniform int v_iter  = 400;
    uniform float v_ray = .2f;
    uniform float v_absorbed = .95f;

    vec4 cf;
    vec4 cb;
    vec3 dir;
    vec3 p;
    float c;
    float dst;
    vec3 dS;
    void main() {
        cf = texture(tex, vec2(fragment_position.x, fragment_position.y));
        cb = texture(back, vec2(fragment_position.x, fragment_position.y));

        // if at least one is positive we look 
        // into the 3d texture volume
        if (cb.w > 0 || cf.w > 0) {
            // init 
            dst = .0f;
            p = cf.xyz;
            dir = normalize(cb.xyz-p);
            dS = v_ds * dir;
            for (int i = 0; i < v_iter && dst < .99f; i ++) {
                c = texture(vol, (mat_volume * vec4(p-0.5,1)).xyz+0.5).r;
                if (c > dst) {
                    dst = c;
                }
                p += dS;   
            }
            frag_color = vec4(dst, dst, dst, dst);
        }

        // here we are outside the cube
        else {
            frag_color = vec4(0.1, 0.1, 0.2, 0.9);
        }
    }
"""


if __name__ == '__main__':
    main()