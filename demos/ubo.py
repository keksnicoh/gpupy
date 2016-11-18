"""
displays a square numpy matrix by using
textures.

@author Nicolas 'keksnicoh' Heimann <nicolas.heimann@gmail.com>
"""
from gpupy.gl.vendor.glfw import * 
from OpenGL.GL import * 
import numpy as np 
from time import time


from ctypes import c_void_p

size_data = np.array([
    (0.05,0.05,),
    (0.0,0.0,),
    (0.5,0.2,),
    (0.0,0.0,),
    (0.4,0.4,),
    (0.0,0.0,),
    (0.3,0.6,),
    (0.0,0.0,),

], dtype=np.float32)

VERT_SHADER = """
#version 410
in vec2 vertex_position;
in int quad_size;
out int geom_quad_size;
void main() {
    geom_quad_size = quad_size;
    gl_Position = vec4(vertex_position.xy, 0, 1);
}
"""
FRAG_SHADER = """
#version 410
out vec4 output_color;
void main() {
    output_color = vec4(1,0,0,1);
}
"""
GEOM_SHADER = """
#version 410
struct mydata {
    vec2 size;
    float a;
    float b;
};
layout (packed) uniform size_data
{ 
  mydata size["""+str(int(size_data.shape[0]/2))+"""];
};
layout (points)  in;
layout (triangle_strip)   out;
layout (max_vertices = 4) out;

in int geom_quad_size[1];

float xwidth;
float ywidth;
void main(void)
{

    if (geom_quad_size[0] == 0) {
        xwidth = .4;
        ywidth = .4;
    }

    if (geom_quad_size[0] == 1) {
        xwidth = .25;
        ywidth = .25;
    }

    if (geom_quad_size[0] == 77) {
        xwidth = .1;
        ywidth = .1;
    }

    xwidth = size[0].size.x;
    ywidth = size[0].size.y;
    gl_Position = gl_in[0].gl_Position + vec4(-xwidth, ywidth,0,0);
    EmitVertex();

    gl_Position = gl_in[0].gl_Position + vec4(xwidth, ywidth,0,0);
    EmitVertex();

    gl_Position = gl_in[0].gl_Position + vec4(-xwidth, -ywidth,0,0);
    EmitVertex();

    gl_Position = gl_in[0].gl_Position + vec4(xwidth, -ywidth,0,0);
    EmitVertex();

    EndPrimitive();
}
"""
print(GEOM_SHADER)
if not glfwInit(): 
    raise RuntimeError('glfw.Init() error')

glfwWindowHint(GLFW_CONTEXT_VERSION_MAJOR, 4);
glfwWindowHint(GLFW_CONTEXT_VERSION_MINOR, 1);
glfwWindowHint(GLFW_OPENGL_FORWARD_COMPAT, GL_TRUE);
glfwWindowHint(GLFW_OPENGL_PROFILE, GLFW_OPENGL_CORE_PROFILE);

window = glfwCreateWindow(500, 500)
if not window: raise RuntimeError('glfw.CreateWindow() error')
glfwMakeContextCurrent(window)

# SHADER
glfwMakeContextCurrent(window)
program = glCreateProgram()

vertex_shader = glCreateShader(GL_VERTEX_SHADER)
glShaderSource(vertex_shader, VERT_SHADER)
glCompileShader(vertex_shader)
glAttachShader(program, vertex_shader)
log = glGetShaderInfoLog(vertex_shader)
if log: raise Exception(log)

fragment_shader = glCreateShader(GL_FRAGMENT_SHADER)
glShaderSource(fragment_shader, FRAG_SHADER)
glCompileShader(fragment_shader)
glAttachShader(program, fragment_shader)
log = glGetShaderInfoLog(fragment_shader)
if log: raise Exception(log)
glLinkProgram(program)

geometry_shader_shader = glCreateShader(GL_GEOMETRY_SHADER)
glShaderSource(geometry_shader_shader, GEOM_SHADER)
glCompileShader(geometry_shader_shader)
glAttachShader(program, geometry_shader_shader)
log = glGetShaderInfoLog(geometry_shader_shader)
if log: raise Exception(log)

glLinkProgram(program)
log = glGetProgramInfoLog(program)
if log: raise Exception(log)
locaction_vertex_position = glGetAttribLocation(program, 'vertex_position')
location_quad_size = glGetAttribLocation(program, 'quad_size')
location_ubo = glGetUniformBlockIndex(program, "size_data");


quad_data = np.array([
    ((0, 0),0),
    ((0.4, 0.4),1),
    ((0.6, 0.6),77),
], dtype=np.dtype([
    ('position', np.float32, (2, )),
    ('size', np.int32)
]))

quad_vbo = glGenBuffers(1)
glBindBuffer(GL_ARRAY_BUFFER, quad_vbo)
glBufferData(GL_ARRAY_BUFFER, quad_data.nbytes, quad_data, GL_STATIC_DRAW)
glBindBuffer(GL_ARRAY_BUFFER, 0)

quad_vao = glGenVertexArrays(1)
glBindVertexArray(quad_vao)
glBindBuffer(GL_ARRAY_BUFFER, quad_vbo)

glVertexAttribPointer(locaction_vertex_position, 2, GL_FLOAT, GL_FALSE, 3*4, c_void_p(0))
glEnableVertexAttribArray(0)

glVertexAttribPointer(location_quad_size, 4, GL_FLOAT, GL_FALSE, 3*4, c_void_p(2*4))
glEnableVertexAttribArray(1)

glBindBuffer(GL_ARRAY_BUFFER, 0)
glBindVertexArray(0)

ubo = glGenBuffers(1)

glBindBuffer(GL_UNIFORM_BUFFER, ubo)
glBufferData(GL_UNIFORM_BUFFER, size_data.nbytes, size_data, GL_STATIC_DRAW)
glBindBufferBase(GL_UNIFORM_BUFFER, 0, ubo);
glBindBuffer(GL_UNIFORM_BUFFER, 0)

glUniformBlockBinding(program, location_ubo, 0);

## plane 
#vertex_position = np.array([-1, 1, -1, -1, 1, -1, 1, -1, 1, 1, -1, 1], dtype=np.float32)
#tex_position = np.array([0, 0, 0, 1, 1, 1, 1, 1, 1, 0, 0, 0], dtype=np.float32)
#
#vao = glGenVertexArrays(1)
#vbo = glGenBuffers(2)
#
#glBindVertexArray(vao)
#glBindBuffer(GL_ARRAY_BUFFER, vbo[0])
#glBufferData(GL_ARRAY_BUFFER, ArrayDatatype.arrayByteCount(vertex_position), vertex_position, GL_STATIC_DRAW)
#glVertexAttribPointer(glGetAttribLocation(program, 'vertex_position'), 2, GL_FLOAT, GL_FALSE, 0, None)
#glEnableVertexAttribArray(0)
#
#glBindBuffer(GL_ARRAY_BUFFER, vbo[1])
#glBufferData(GL_ARRAY_BUFFER, ArrayDatatype.arrayByteCount(tex_position), tex_position, GL_STATIC_DRAW)
#glVertexAttribPointer(glGetAttribLocation(program, 'text_coord'), 2, GL_FLOAT, GL_FALSE, 0, None)
#glEnableVertexAttribArray(1)
#
#glBindBuffer(GL_ARRAY_BUFFER, 0)
#glBindVertexArray(0)


# render
while not glfwWindowShouldClose(window):
    glfwPollEvents()

    glClear(GL_COLOR_BUFFER_BIT)
    glUseProgram(program)
    glBindVertexArray(quad_vao)

    glDrawArrays(GL_POINTS, 0, quad_data.shape[0])

    glBindVertexArray(0)
    glUseProgram(0)

    glfwSwapBuffers(window)
