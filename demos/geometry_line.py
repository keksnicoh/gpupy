"""
use geometry shader to plot a thick line

notes:
- sometimes there are artefacts in rendering. maybe the calculation
  of m or t in geometry shader leads to infinity? 

@author Nicolas 'keksnicoh' Heimann <nicolas.heimann@gmail.com>
"""
from gpupy.gl.vendor.glfw import * 
from OpenGL.GL import * 
import numpy 
from time import time

# data domain
LENGTH = 10000
UNIT = 2.0/LENGTH
SHIFT = 1.0;
vertex_position = numpy.zeros(LENGTH*2, dtype=numpy.float32)
for i in range(0, LENGTH):
    vertex_position[i*2] = UNIT*i - SHIFT
    vertex_position[i*2+1] = .0

VERT_SHADER_ID = """
#version 410
in vec2 vertex_position;
out vec4 fragment_color;
uniform float time;
void main() {
    fragment_color = vec4(0.5+0.5*cos(70*vertex_position.x),0.5+0.5*sin(70*vertex_position.x),0,1);
    float r = exp(-1*(vertex_position.x+1))*(0.5+sin(time)*0.5+0.5);
    gl_Position = vec4(vertex_position.x, r*sin(20*vertex_position.x+5*time), 0, 1);
}
"""
FRAG_SHADER_ID = """
#version 410
out vec4 output_color;
uniform float smooth_width = 0.08;
uniform float border = 0.15;
uniform vec4 border_color = vec4(1,1,1,1);
in vec4 color;
in vec2 coord;
void main() {
    float mix_factor = 0.0;
    float y = abs(coord.y-0.5);
    if (y > (0.5-border)+smooth_width/2) {
        mix_factor = 1.0;
    }
    else if (y > (0.5-border)-smooth_width/2) {
        float yb = y-((0.5-border)-smooth_width/2);
        mix_factor = yb/smooth_width;

    }
    else {
        mix_factor = 0.0;
    }
    output_color = mix(color, border_color, mix_factor);

    // pseudo antialiasing outside
    if (coord.y < smooth_width) {
        output_color.w = coord.y/smooth_width;
    }
    else if (coord.y > 1-smooth_width) {
        output_color.w = (1-coord.y)/smooth_width;
    }
    output_color = output_color;
}
"""
GEOMETRY_SHADER = """
#version 410
layout (lines_adjacency) in;
layout (triangle_strip) out;
layout (max_vertices = 4) out;
out vec4 color;
out vec2 coord;
in vec4 fragment_color[4];

uniform float width = 0.002;
vec2 n(vec2 x0, vec2 x1) {
    return normalize(vec2(x0.y-x1.y, x1.x-x0.x));
}

vec2 p[4]; // verticies
vec2 t[2]; // tangents between 0-1, 2-3
vec2 m[2];
float l[2]; 

void main(void)
{
    p[0] = gl_in[0].gl_Position.xy;
    p[1] = gl_in[1].gl_Position.xy;
    p[2] = gl_in[2].gl_Position.xy;
    p[3] = gl_in[3].gl_Position.xy;

    t[0] = normalize(normalize(p[2]-p[1]) + normalize(p[1]-p[0]));
    t[1] = normalize(normalize(p[3]-p[2]) + normalize(p[2]-p[1]));

    m[0] = vec2(-t[0].y, t[0].x);
    m[1] = vec2(-t[1].y, t[1].x);

    l[0] = width/dot(m[0], n(p[0], p[1]));
    l[1] = width/dot(m[1], n(p[1], p[2]));

    color = fragment_color[0];
    coord = vec2(0,1);
    gl_Position = gl_in[1].gl_Position + vec4(-m[0]*l[0], 0, 0) ;
    EmitVertex();

    color = fragment_color[1];
    coord = vec2(0,0);
    gl_Position = gl_in[1].gl_Position + vec4(m[0]*l[0], 0,0) ;
    EmitVertex();

    color = fragment_color[2];
    coord = vec2(1,1);
    gl_Position = gl_in[2].gl_Position + vec4(-m[1]*l[1], 0,0) ;
    EmitVertex();

    color = fragment_color[3];
    coord = vec2(1,0);
    gl_Position = gl_in[2].gl_Position + vec4(m[1]*l[1], 0,0) ;
    EmitVertex();

    EndPrimitive();
}
"""

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
glShaderSource(vertex_shader, VERT_SHADER_ID)
glCompileShader(vertex_shader)
glAttachShader(program, vertex_shader)
log = glGetShaderInfoLog(vertex_shader)
if log: raise Exception(log)

fragment_shader = glCreateShader(GL_FRAGMENT_SHADER)
glShaderSource(fragment_shader, FRAG_SHADER_ID)
glCompileShader(fragment_shader)
glAttachShader(program, fragment_shader)
log = glGetShaderInfoLog(fragment_shader)
if log: raise Exception(log)

geometry_shader = glCreateShader(GL_GEOMETRY_SHADER)
glShaderSource(geometry_shader, GEOMETRY_SHADER)
glCompileShader(geometry_shader)
glAttachShader(program, geometry_shader)
log = glGetShaderInfoLog(geometry_shader)
if log: raise Exception(log)
glLinkProgram(program)


# DATA
vao1 = glGenVertexArrays(1)
vbo1 = glGenBuffers(1)

glBindBuffer(GL_ARRAY_BUFFER, vbo1)
glBufferData(GL_ARRAY_BUFFER, ArrayDatatype.arrayByteCount(vertex_position), vertex_position, GL_STATIC_DRAW)
glBindBuffer(GL_ARRAY_BUFFER, 0)
glBindVertexArray(vao1)
glBindBuffer(GL_ARRAY_BUFFER, vbo1)
glVertexAttribPointer(glGetAttribLocation(program, 'vertex_position'), 2, GL_FLOAT, GL_FALSE, 0, None)
glEnableVertexAttribArray(0)
glBindBuffer(GL_ARRAY_BUFFER, 0)
glBindVertexArray(0)

# init main loop
gl_time = glGetUniformLocation(program, 'time')
gl_width = glGetUniformLocation(program, 'width')
start_time = time()
glClearColor(.01, .01, .1, 1)
glEnable(GL_BLEND);
glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA);

while not glfwWindowShouldClose(window):
    timer = time() - start_time
    glfwPollEvents()

    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    glUseProgram(program)
    glUniform1f(gl_time, timer)
    glUniform1f(gl_width, 0.002+0.02*(numpy.sin(timer)+1))
    glBindVertexArray(vao1)
    glDrawArrays(GL_LINE_STRIP_ADJACENCY, 0, int(float(len(vertex_position))/2))
    glBindVertexArray(0)
    glUseProgram(0)

    glfwSwapBuffers(window)
