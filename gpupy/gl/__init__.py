from pkgutil import extend_path
__path__ = extend_path(__path__, __name__)

# allow to import all accepted basic components
# to be imported by 
# from gpupy.gl import *

from gpupy.gl.config import GlConfig 
from gpupy.gl.buffer import BufferObject 
from gpupy.gl.texture import Texture2D, Texture1D, Texture3D 
from gpupy.gl.shader import Shader, Program 
from gpupy.gl.camera import Camera 
from gpupy.gl.framebuffer import Framebuffer 
from gpupy.gl.viewport import ViewPort

__all__ = ['GlConfig', 'BufferObject', 'Texture2D', 'Texture1D', 
           'Texture3D', 'Shader', 'Program', 'Camera', 'Framebuffer', 'ViewPort']