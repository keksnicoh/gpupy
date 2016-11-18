"""
this code demosntrates problems with glGetBufferSubData.
if one invokes

    glGetBufferSubData(GL_ARRAY_BUFFER, 0, 6*4, data)

with non-empty data, the application ends in segfault 
about 50% of the time.

if you invoke it with empty data, pyopengl seems to ignore
the argument. nothing will be written to data. 
if you let opengl yield an invalid operation (bad length)
one can see, that the argument may not be handled proper:

    OpenGL.error.GLError: GLError(
        err = 1281,
        description = 'invalid value',
        baseOperation = glGetBufferSubData,
        pyArgs = (
            GL_ARRAY_BUFFER,
            0,
            48,
            array([ 0.,  0.,  0.,  0.,  0.,  0.], dtype=float32),
        ),
        cArgs = (
            GL_ARRAY_BUFFER,
            0,
            48,
            array([0, 0, 0, 0, 0, 0], dtype=uint8),  < DATA IS unit8 instead of float32
        ),
        cArguments = (
            GL_ARRAY_BUFFER,
            0,
            48,
            array([0, 0, 0, 0, 0, 0], dtype=uint8),  
        )
    )

But: the function seems to return the data as a raw uint8 numpy.ndarray. 
if you convert this raw binary data to float32, one can finally read
the float32 values from the vbo:

    raw_unit8_data = glGetBufferSubData(GL_ARRAY_BUFFER, 0, 6*4)
    print(np.fromstring(raw_unit8_data.tostring(), dtype='<f4'))

@author Nicolas 'keksnicoh' Heimann
"""
from gpupy.gl.vendor.glfw import * 
from OpenGL.GL import * 
import numpy as np 

# spawn glfw stuff
if not glfwInit(): raise RuntimeError('glfw.Init() error')
glfwWindowHint(GLFW_CONTEXT_VERSION_MAJOR, 4);
glfwWindowHint(GLFW_CONTEXT_VERSION_MINOR, 1);
glfwWindowHint(GLFW_OPENGL_FORWARD_COMPAT, GL_TRUE);
glfwWindowHint(GLFW_OPENGL_PROFILE, GLFW_OPENGL_CORE_PROFILE);
window = glfwCreateWindow(500, 500)
glfwMakeContextCurrent(window)

# push data to vbo
data = np.array([1,1,1,2,2,100], dtype=np.float32)
vbo = glGenBuffers(1)
glBindBuffer(GL_ARRAY_BUFFER, vbo)
glBufferData(GL_ARRAY_BUFFER, 6*4, data, GL_STATIC_DRAW)
glBindBuffer(GL_ARRAY_BUFFER, 0)

# pullback
glBindBuffer(GL_ARRAY_BUFFER, vbo)
raw_unit8_data = glGetBufferSubData(GL_ARRAY_BUFFER, 0, 6*4)
glBindBuffer(GL_ARRAY_BUFFER, 0)
print(raw_unit8_data.view('<f4'))

