Shaders
=======

gpupy.gl.shader brings utilities to work with OpenGL shaders.

```python
from gpupy.gl.shaders import Shader, Program
from OpenGL.GL import VERTEX_SHADER, FRAGMENT_SHADER

vertex_shader = Shader(GL_VERTEX_SHADER, """
  {% version %}
  in vec4 vertex;

  void main() {
    gl_Position = vertex;
  }
""")
fragment_shader = Shader(GL_FRAGMENT_SHADER, """
  {% version %}
  
  uniform vec4 color;
  out vec4 fragment_color;
  void main() {
    fragment_color = color;
  }
""")
program = Program()
program.shaders.append(vertex_shader)
program.shaders.append(fragment_shader)
program.link()
```

The `{% version %}` tag injects the shader version which is required for OpenGL Core profile. The Shader instance precompiles the source code to reflect attributes, uniforms, structures, uniform blocks. For example the attribute location of `vertex` can be accessed by
```python 
program.attributes['vertex']
# equivalent to
glGetAttribLocation(program.gl_shader_id, 'vertex')
```

uniforms can be defined by 
```python
program.uniform('color', (1, 0, 0, 1))
``` 
To avoid memory transfer from the host to gpu, the shader keeps all changes of uniforms within a buffer until the program is used. 

structures
----------
The `{% struct <name> %}` tag allows to define structures within the shader via python. 
```python
vertex_shader = Shader(GL_VERTEX_SHADER, """
  {% version %}
  {% struct some_structure %}
  //...
""")
#...
program.declare_struct('some_structure', """some_structure {
  float3 a;
  float b;
}""")
```
It is possible to use numpy dtype to declare a structure.
```python 
# this is equivalent to the latter code snippet
program.declare_struct('some_structure', np.dtype([
  ('a', np.float32, 3),
  ('b', np,float32)
])
```
