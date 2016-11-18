"""
demo shows how to handle simple framebuffers.

results:
- keeping viewport size constant within framebuffer
  is important to fit texture sizes. 

@author Nicolas 'keksnicoh' Heimann <nicolas.heimann@gmail.com>
"""
from gpupy.gl.vendor.glfw import * 
from OpenGL.GL import * 
import numpy 
from time import time
if not glfwInit(): 
    raise RuntimeError('glfw.Init() error')

glfwWindowHint(GLFW_CONTEXT_VERSION_MAJOR, 4);
glfwWindowHint(GLFW_CONTEXT_VERSION_MINOR, 1);
glfwWindowHint(GLFW_OPENGL_FORWARD_COMPAT, GL_TRUE);
glfwWindowHint(GLFW_OPENGL_PROFILE, GLFW_OPENGL_CORE_PROFILE);

window1 = glfwCreateWindow(400, 400)
if not window1: raise RuntimeError('glfw.CreateWindow() error')

vertex_position = numpy.array([
    0.8, 0.8, 0.8, -0.8, -0.8, -0.8, -0.8, 0.8, 0.8, 0.8
], dtype=numpy.float32)
screen_position = numpy.array([
            -0.95, 0.95, 
            -0.95, -0.95, 
            0.95, -0.95, 
            0.95, -0.95, 
            0.95, 0.95,
            -0.95, 0.95, 
], dtype=numpy.float32)

tex_position = numpy.array([
            0, 1,
            0, 0,
            1, 0,
            1, 0,
            1, 1,
            0, 1
], dtype=numpy.float32)
VERT_SHADER_ID = "#version 410\nin vec2 vertex_position; void main() { gl_Position = vec4(vertex_position, 0, 1); }"
FRAG_SHADER_ID = "#version 410\nout vec4 output_color; void main() { output_color = vec4(1,0,0,1); }"

VERT_SHADER_FRAME = """
#version 410
in vec2 vertex_position;
in vec2 tex_coords;
out vec2 frag_tex_coord;
void main() {
    frag_tex_coord = tex_coords;
    gl_Position = vec4(vertex_position, 0, 1); 
}
"""
FRAG_SHADER_FRAME = """
#version 410
uniform sampler2D tex[1];
in vec2 frag_tex_coord;
out vec4 output_color;
uniform float time;
vec2 transformed;
void main() {
    output_color = vec4(0.1,1,0,1);
    transformed = vec2(
        exp(-5*sin(time)*(pow(frag_tex_coord[0]-0.5,2)+pow(frag_tex_coord[1]-0.5,2)))*frag_tex_coord[0],
        exp(-5*sin(time)*(pow(frag_tex_coord[0]-0.5,2)+pow(frag_tex_coord[1]-0.5,2)))*frag_tex_coord[1]
    );
    output_color = texture(tex[0], transformed);
    output_color = mix(output_color, vec4(0, transformed ,1), 0.2);
}
"""

glfwMakeContextCurrent(window1)
program1 = glCreateProgram()
vertex_shader1 = glCreateShader(GL_VERTEX_SHADER)
glShaderSource(vertex_shader1, VERT_SHADER_ID)
glCompileShader(vertex_shader1)
glAttachShader(program1, vertex_shader1)
fragment_shader1 = glCreateShader(GL_FRAGMENT_SHADER)
glShaderSource(fragment_shader1, FRAG_SHADER_ID)
glCompileShader(fragment_shader1)
glAttachShader(program1, fragment_shader1)
glLinkProgram(program1)

program_frame = glCreateProgram()
vertex_shader_frame = glCreateShader(GL_VERTEX_SHADER)
glShaderSource(vertex_shader_frame, VERT_SHADER_FRAME)
glCompileShader(vertex_shader_frame)
glAttachShader(program_frame, vertex_shader_frame)
frag_shader_frame = glCreateShader(GL_FRAGMENT_SHADER)
glShaderSource(frag_shader_frame, FRAG_SHADER_FRAME)
glCompileShader(frag_shader_frame)
glAttachShader(program_frame, frag_shader_frame)
glLinkProgram(program_frame)

glfwMakeContextCurrent(window1)
vert_attr1 = glGetAttribLocation(program1, 'vertex_position')
vert_attr2 = glGetAttribLocation(program_frame, 'vertex_position')
tex_coords = glGetAttribLocation(program_frame, 'tex_coords')

# rectangle init
glfwMakeContextCurrent(window1)
vao1 = glGenVertexArrays(1)
vbo1 = glGenBuffers(1)

glBindBuffer(GL_ARRAY_BUFFER, vbo1)
glBufferData(GL_ARRAY_BUFFER, ArrayDatatype.arrayByteCount(vertex_position), vertex_position, GL_STATIC_DRAW)
glBindBuffer(GL_ARRAY_BUFFER, 0)
glBindVertexArray(vao1)
glBindBuffer(GL_ARRAY_BUFFER, vbo1)
glVertexAttribPointer(vert_attr1, 2, GL_FLOAT, GL_FALSE, 0, None)
glEnableVertexAttribArray(0)
glBindBuffer(GL_ARRAY_BUFFER, 0)
glBindVertexArray(0)

# framebuffer screen init
vao_frame = glGenVertexArrays(1)
vbo_frame = glGenBuffers(2)
glBindVertexArray(vao_frame)
glBindBuffer(GL_ARRAY_BUFFER, vbo_frame[0])
glBufferData(GL_ARRAY_BUFFER, ArrayDatatype.arrayByteCount(screen_position), screen_position, GL_STATIC_DRAW)
glVertexAttribPointer(vert_attr2, 2, GL_FLOAT, GL_FALSE, 0, None)
glEnableVertexAttribArray(0)
glBindBuffer(GL_ARRAY_BUFFER, 0)

glBindBuffer(GL_ARRAY_BUFFER, vbo_frame[1])
glBufferData(GL_ARRAY_BUFFER, ArrayDatatype.arrayByteCount(tex_position), tex_position, GL_STATIC_DRAW)
glVertexAttribPointer(tex_coords, 2, GL_FLOAT, GL_FALSE, 0, None)
glEnableVertexAttribArray(1)
glBindBuffer(GL_ARRAY_BUFFER, 0)
glBindVertexArray(0)

# framebuffer init
rgb_tex_id = glGenTextures(1)
glBindTexture(GL_TEXTURE_2D, rgb_tex_id);
glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, 800, 800, 0, GL_RGBA, GL_UNSIGNED_BYTE, None);
glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
glBindTexture(GL_TEXTURE_2D, 0);

framebuffer_id = glGenFramebuffers(1);
glBindFramebuffer(GL_DRAW_FRAMEBUFFER, framebuffer_id)
glDrawBuffer(GL_COLOR_ATTACHMENT0)
glFramebufferTexture(GL_FRAMEBUFFER, GL_COLOR_ATTACHMENT0, rgb_tex_id, 0);
rid = glGenRenderbuffers(1)

start_time = time()
gl_time = glGetUniformLocation(program_frame, 'time')

while not glfwWindowShouldClose(window1):
    timer = time() - start_time
    glfwPollEvents()

    # note:
    #
    # viewport changes after glfwPollEvents.
    # to restore viewport after framebuffer, persist
    # current viewport
    old_viewport = glGetIntegerv(GL_VIEWPORT)

    glBindFramebuffer(GL_DRAW_FRAMEBUFFER, framebuffer_id)

    # note:
    #
    # set viewport size still 800x800 to fit 
    # texture sizes
    glViewport(0, 0, 800, 800)

    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    glUseProgram(program1)
    glBindVertexArray(vao1)
    glDrawArrays(GL_LINE_STRIP, 0, 5)
    glBindVertexArray(0)
    glUseProgram(0)
    glBindFramebuffer(GL_DRAW_FRAMEBUFFER, 0)

    # note:
    # restore old viewport (before framebuffer frame)
    glViewport(*old_viewport)
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    glActiveTexture(GL_TEXTURE0);
    glBindTexture (GL_TEXTURE_2D, rgb_tex_id)

    glUseProgram(program_frame)
    glUniform1f(gl_time, timer)
    glBindVertexArray(vao_frame)
    glDrawArrays(GL_TRIANGLES, 0, 6)
    glBindVertexArray(0)
    glUseProgram(0)
    glfwSwapBuffers(window1)

