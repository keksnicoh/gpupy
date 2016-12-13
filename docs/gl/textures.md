Textures
========

The `gpupy.gl.texture` module provides some utilities to create and modify textures. 
All texture objects should have the `gl_texture_id` attribute. 
Optionally the `gl_texture_unit` attribute may define to which texture unit the texture is bound.

Create a texture:
-----------------
There are different Texture classes: `Texture1D`, `Texture2D`, `Texture3D`. A simple two dimensional texture 
is created by
```python 
from gpupy.gl.textures import *
import numpy as np 

ndarray = np.random.random((500, 500, 2), dtype=np.float32)
texture = Texture2D.to_device(ndarray)
```

The `Texture2D` class determines from numpy dtype and shape that the texture has size `500x500`, two color channels (`GL_RG`) and is of type `GL_FLOAT`. 

Using the texture
------------------
To activate a texture at a given texture unit one can write
```python
texture.activate(1)

# the same as
glActiveTexture(GL_TEXTURE1)
glBindTexture(texture.gl_texture_id)
```

The texture object is known by the gpupy.gl.shader module. If one binds a texture to a shader uniform the Shader Program will activate the texture automatically when the Program is used. 

```python
shader_program.uniform('tex', texture)

shader_program.use()
# ...
shader_program.unnuse()
```

Note: The shader program will not restore the texture configuration from before. 
The shader does only automatically activate textures at some unit if texture.gl_texture_unit exists and is None. 
To prevent the shader from doing so, one can use the `texture_activation` flag of use or disable this feature by default:
```python
shader_program.features('texture_activation', false)
# or locally
shader_program.use(texture_activation=false)
```
