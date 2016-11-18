"""
demo shows how to handle multiple windows

results:

- shader programs can only exists in one glfw context.
  each glfw context start shader ids ascending from 0.
- each glfw context has its own OpenGL state

@author Nicolas 'keksnicoh' Heimann <nicolas.heimann@gmail.com>
"""
from gpupy.gl.vendor.glfw import * 
from OpenGL.GL import * 
import numpy 

if not glfwInit(): 
    raise RuntimeError('glfw.Init() error')

glfwWindowHint(GLFW_CONTEXT_VERSION_MAJOR, 4);
glfwWindowHint(GLFW_CONTEXT_VERSION_MINOR, 1);
glfwWindowHint(GLFW_OPENGL_FORWARD_COMPAT, GL_TRUE);
glfwWindowHint(GLFW_OPENGL_PROFILE, GLFW_OPENGL_CORE_PROFILE);

window1 = glfwCreateWindow(400, 400)
if not window1: raise RuntimeError('glfw.CreateWindow() error')
window2 = glfwCreateWindow(400, 400)
if not window2: raise RuntimeError('glfw.CreateWindow() error')

vertex_position = numpy.array([
    0.5, 0.5, 0.5, -0.5, -0.5, -0.5, -0.5, 0.5, 0.5, 0.5
], dtype=numpy.float32)

VERT_SHADER_ID1 = "#version 410\nin vec2 vertex_position; void main() { gl_Position = vec4(vertex_position, 0, 1); }"
VERT_SHADER_ID2 = "#version 410\nin vec2 vertex_position2; void main() { gl_Position = vec4(vertex_position2, 0, 1); }"
FRAG_SHADER_ID1 = "#version 410\nout vec4 output_color; void main() { output_color = vec4(1,0,0,1); }"
FRAG_SHADER_ID2 = "#version 410\nout vec4 output_color; void main() { output_color = vec4(0,1,0,1); }"

# NOTE:
# 
# each gl operation in a specific window should
# be done after glfwMakeContextCurrent. 
#
# shader programs can only exists within a given context.
# note that both shader programs have id=1!
glfwMakeContextCurrent(window1)
program1 = glCreateProgram()
vertex_shader1 = glCreateShader(GL_VERTEX_SHADER)
glShaderSource(vertex_shader1, VERT_SHADER_ID1)
glCompileShader(vertex_shader1)
glAttachShader(program1, vertex_shader1)
fragment_shader1 = glCreateShader(GL_FRAGMENT_SHADER)
glShaderSource(fragment_shader1, FRAG_SHADER_ID1)
glCompileShader(fragment_shader1)
glAttachShader(program1, fragment_shader1)
glLinkProgram(program1)

glfwMakeContextCurrent(window2)
program2 = glCreateProgram()
vertex_shader2 = glCreateShader(GL_VERTEX_SHADER)
glShaderSource(vertex_shader2, VERT_SHADER_ID2)
glCompileShader(vertex_shader2)
glAttachShader(program2, vertex_shader2)
fragment_shader2 = glCreateShader(GL_FRAGMENT_SHADER)
glShaderSource(fragment_shader2, FRAG_SHADER_ID2)
glCompileShader(fragment_shader2)
glAttachShader(program2, fragment_shader2)
glLinkProgram(program2)

# NOTE:
#
# Again, use glfwMakeContextCurrent (see above)
glfwMakeContextCurrent(window1)
vert_attr1 = glGetAttribLocation(program1, 'vertex_position')

glfwMakeContextCurrent(window2)
vert_attr2 = glGetAttribLocation(program2, 'vertex_position2')

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

glfwMakeContextCurrent(window2)
vao2 = glGenVertexArrays(1)
vbo2 = glGenBuffers(1)

glBindBuffer(GL_ARRAY_BUFFER, vbo2)
glBufferData(GL_ARRAY_BUFFER, ArrayDatatype.arrayByteCount(vertex_position), vertex_position, GL_STATIC_DRAW)
glBindBuffer(GL_ARRAY_BUFFER, 0)
glBindVertexArray(vao2)
glBindBuffer(GL_ARRAY_BUFFER, vbo2)
glVertexAttribPointer(vert_attr2, 2, GL_FLOAT, GL_FALSE, 0, None)
glEnableVertexAttribArray(0)
glBindBuffer(GL_ARRAY_BUFFER, 0)
glBindVertexArray(0)

# to see that glfwMakeContextCurrent is very important.
print('PROGRAM IDS', program1, program2)
print('VAO IDS', vao1, vao2)
print('VBO IDS', vbo1, vbo2)

while not (glfwWindowShouldClose(window1) or glfwWindowShouldClose(window2)):
    glfwPollEvents()

    glfwMakeContextCurrent(window1)
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    glUseProgram(program1)
    glBindVertexArray(vao1)
    glDrawArrays(GL_LINE_STRIP, 0, 5)
    glBindVertexArray(0)
    glUseProgram(0)
    
    glfwMakeContextCurrent(window2)
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    glUseProgram(program1)
    glBindVertexArray(vao1)
    glDrawArrays(GL_LINE_STRIP, 0, 5)
    glBindVertexArray(0)
    glUseProgram(0)

    # glfwSwapBuffers does not need glfwMakeContextCurrent
    glfwSwapBuffers(window1)
    glfwSwapBuffers(window2)