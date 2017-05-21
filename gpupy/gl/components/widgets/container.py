from gpupy.gl.components.widgets import Widget 

from gpupy.gl.common.vector import *
from gpupy.gl import * 
from gpupy.gl.components.camera import Camera2D
from gpupy.gl.common import attributes
from gpupy.gl.mesh import * 
from gpupy.gl.common import Event 

import numpy as np 
from OpenGL.GL import *

def border_size(s, b, m):
    x = s.x - b.y - b.w - m.y - m.w
    y = s.y - b.x - b.z - m.x - m.z
    return (x, y)

def content_size(s, b, m, p):
    x = s.x - b.y - b.w - p.y - p.w - m.y - m.w
    y = s.y - b.x - b.z - p.y - p.z - m.x - m.z
    return (x, y)

def content_position(p, b, m, pd):
    x = p.x + b.w + pd.w + m.w
    y = p.y + b.x + pd.x + m.x
    return (x, y, p.z, p.w)

class Container(Widget):
    """
    like a div container, the Container widget has a position, size, margin, border and padding. 

     position
       \        size x
        +---------------------------- ... +
        |     margin
      s | 
      i |     +---------   
      z |     |    border
      e |     |   +----------
        |     |   |    padding
      y |     |   |   +-----------
        |     |   |   |    content box
        |
        ...  
        +---------------------------- ... +

    ```python
        container = Container((100, 100), margin=(10, 10), padding=(10, 10), border=(10, 10, 10, 10), border_color=(1, 0, 0, 1))
        container.widget = SomeWidget(size=container.content_size, position=container_position)
        container.tick()
        container.render()
    ```
    """
    size = attributes.VectorAttribute(2)

    position         = attributes.VectorAttribute(4)
    padding          = attributes.VectorAttribute(4)
    margin           = attributes.VectorAttribute(4)
    border           = attributes.VectorAttribute(4)
    border_color     = attributes.VectorAttribute(4)

    # transformed properties
    content_position = attributes.ComputedAttribute(
        position, border, margin, padding, 
        transformation=content_position,
        descriptor=attributes.VectorAttribute(4))

    content_size = attributes.ComputedAttribute(
        size, border, margin, padding,    
        transformation=content_size, 
        descriptor=attributes.VectorAttribute(2))

    border_size = attributes.ComputedAttribute(
        size, border, margin,             
        transformation=border_size,
        descriptor=attributes.VectorAttribute(2))

    def __init__(self, 
                 widget=None, 
                 size=(0, 0), 
                 position=(0, 0, 0, 0), 
                 margin=(0, 0, 0, 0), 
                 padding=(0, 0, 0, 0), 
                 border=(1, 1, 1, 1), 
                 border_color=(0, 0, 0, 1)):

        super().__init__()

        self.size         = size 
        self.position     = position 
        self.padding      = padding 
        self.border       = border 
        self.border_color = border_color
        self.margin       = margin

        self._widget = None
        self.set_widget(widget)

        self.to_gpu = True
        self._init_borders()


    def set_widget(self, widget):
        self._widget = widget 

    @border_color.on_change 
    @content_size.on_change 
    @border_size.on_change
    def _flag_create_mesh(self, *a):
        self.on_tick.once(self.sync_gpu)


    def sync_gpu(self):
        self._create_mesh()


    def _init_borders(self):
        self.border_program = BorderProgram()
        self.border_mesh = StridedVertexMesh(np.empty(0, dtype=np.dtype([
            ('vertex', np.float32, 4),
            ('color', np.float32, 4)
        ])), GL_TRIANGLES, attribute_locations=self.border_program.attributes)



    def _create_mesh(self):
        b, c, s = self.border, self.border_color, self.border_size
        p = self.position + (b[3] + self.margin[3], b[0] + self.margin[0], 0, 0)
        crn = (p[1], p[0] + s[0], p[1] + s[1], p[0]) # corner coords
        vcnt = sum(6*(int(l > 0) + int(l > 0 and b[(i + 1) % 4] > 0)) for i, l in enumerate(b))
        v = np.zeros(vcnt, self.border_mesh.buffer.dtype)
        i = 0
        if b[3] and b[0]: # left upper corner
            v[i:i+6] = [((crn[3]-b[3], crn[0]-b[0], 0, 1), c), 
                        ((crn[3], crn[0]-b[0], 0, 1), c), 
                        ((crn[3], crn[0], 0, 1), c),
                        ((crn[3], crn[0], 0, 1), c), 
                        ((crn[3]-b[3], crn[0], 0, 1), c), 
                        ((crn[3]-b[3], crn[0]-b[0], 0, 1), c)]; i+=6
        if b[0]: # top
            v[i:i+6] = [((crn[3]-b[3], crn[0]-b[0], 0, 1), c),
                        ((crn[1], crn[0]-b[0], 0, 1), c),
                        ((crn[1], crn[0], 0, 1), c),
                        ((crn[1], crn[0], 0, 1), c),
                        ((crn[3]-b[3], crn[0]-b[0], 0, 1), c),
                        ((crn[3]-b[3], crn[0], 0, 1), c)]; i+=6
        if b[0] and b[1]: # right upper corner
            v[i:i+6] = [((crn[1]+b[1], crn[0]-b[0], 0, 1), c),
                        ((crn[1], crn[0]-b[0], 0, 1), c),
                        ((crn[1], crn[0], 0, 1), c),
                        ((crn[1], crn[0], 0, 1), c),
                        ((crn[1]+b[1], crn[0],  0, 1), c),
                        ((crn[1]+b[1], crn[0]-b[0], 0, 1), c)]; i+=6
        if b[1]: # right
            v[i:i+6] = [((crn[1]+b[1], crn[0], 0, 1), c),
                        ((crn[1], crn[0], 0, 1), c),
                        ((crn[1], crn[2], 0, 1), c),
                        ((crn[1], crn[2], 0, 1), c),
                        ((crn[1]+b[1], crn[2], 0, 1), c),
                        ((crn[1]+b[1], crn[0], 0, 1), c)]; i+=6
        if b[1] and b[2]: # right lower corner
            v[i:i+6] = [((crn[1]+b[1], crn[2]+b[2], 0, 1), c),
                        ((crn[1], crn[2]+b[2], 0, 1), c),
                        ((crn[1], crn[2], 0, 1), c),
                        ((crn[1], crn[2], 0, 1), c),
                        ((crn[1]+b[1], crn[2], 0, 1), c),
                        ((crn[1]+b[1], crn[2]+b[2], 0, 1), c)]; i+=6
        if b[2]: # bottom
            v[i:i+6] = [((crn[3]-b[3], crn[2]+b[2], 0, 1), c),
                        ((crn[1], crn[2]+b[2], 0, 1), c),
                        ((crn[1], crn[2], 0, 1), c),
                        ((crn[1], crn[2], 0, 1), c),
                        ((crn[3]-b[3], crn[2]+b[2], 0, 1), c),
                        ((crn[3]-b[3], crn[2], 0, 1), c)]; i+=6
        if b[2] and b[3]: # left lower corner
            v[i:i+6] = [((crn[3]-b[3], crn[2]+b[2], 0, 1), c),
                        ((crn[3], crn[2]+b[2], 0, 1), c),
                        ((crn[3], crn[2], 0, 1), c),
                        ((crn[3], crn[2], 0, 1), c),
                        ((crn[3]-b[3], crn[2], 0, 1), c),
                        ((crn[3]-b[3], crn[2]+b[2], 0, 1), c)]; i+=6
        if b[3]: # left
            v[i:i+6] = [((crn[3]-b[3], crn[0], 0, 1), c),
                        ((crn[3], crn[0], 0, 1), c),
                        ((crn[3], crn[2], 0, 1), c),
                        ((crn[3], crn[2], 0, 1), c),
                        ((crn[3]-b[3], crn[2], 0, 1), c),
                        ((crn[3]-b[3], crn[0], 0, 1), c)]; i+=6

        self.border_mesh.buffer.set(v)

    def _render(self):
        self.border_program.use()
        self.border_mesh.draw()
        self.border_program.unuse()


class BorderProgram(Program):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.shaders.append(Shader(GL_VERTEX_SHADER, """
            {% version %}
            {% uniform_block camera %}
            in vec4 vertex;
            in vec4 color;
            out vec4 frg_color;
            void main() {
                gl_Position = camera.mat_projection * camera.mat_view * vertex;
                frg_color = color;
            }
        """))
        self.shaders.append(Shader(GL_FRAGMENT_SHADER, """
            {% version %}
            in vec4 frg_color;
            out vec4 out_color;
            void main() {
                out_color = frg_color;
            }
        """))
        self.declare_uniform('camera', Camera2D.DTYPE, variable='camera')
        self.link()
        self.uniform_block_binding('camera', GPUPY_GL.CONTEXT.buffer_base('gpupy.gl.camera'))


