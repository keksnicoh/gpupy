"""
gpupy.gl 

OpenGL context manager wrapper, OpenGL core functions wrapper and 
python integration as well as helpers and common widgets and components to 
deal with OpenGL.

:author: keksnicoh
"""
from pkgutil import extend_path
__path__ = extend_path(__path__, __name__)

# allow to import all __accepted__ basic components
# to be imported by 
#    from gpupy.gl import *

from gpupy.gl.gpupygl import GPUPY_GL
from gpupy.gl.buffer import BufferObject 
from gpupy.gl.texture import Texture2D, Texture1D, Texture3D 
from gpupy.gl.shader import Shader, Program, create_program
from gpupy.gl.framebuffer import Framebuffer 
from gpupy.gl.viewport import Viewport

from OpenGL import GL as _GL
GL = _GL

__all__ = ['BufferObject', 'Texture2D', 'Texture1D', 
           'Texture3D', 'Shader', 'Program', 'Framebuffer', 'Viewport', 'GPUPY_GL', 'GL', 'create_program']

