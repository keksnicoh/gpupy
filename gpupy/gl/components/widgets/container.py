from gpupy.gl.components.widgets import Widget 

from gpupy.gl.vector import *
from gpupy.gl import * 
from gpupy.gl.components.camera import Camera2D
from gpupy.gl.common import attributes
from gpupy.gl.mesh import * 
import numpy as np 
from OpenGL.GL import *
from gpupy.gl.common import Event 

class Container(Widget):

    size = attributes.VectorAttribute(2)

    position         = attributes.VectorAttribute(4)
    padding          = attributes.VectorAttribute(4)
    margin           = attributes.VectorAttribute(4)
    border           = attributes.VectorAttribute(4)
    border_color     = attributes.VectorAttribute(4)
    content_position = attributes.ComputedAttribute(position, border, margin, padding, descriptor=attributes.VectorAttribute(4), some_test='TOO')
    content_size     = attributes.ComputedAttribute(size, border, margin, padding,     descriptor=attributes.VectorAttribute(2))
    border_size      = attributes.ComputedAttribute(size, border, margin,              descriptor=attributes.VectorAttribute(2))

    def __init__(self, widget=None, 
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

        self.widget = widget

        self._require_create_mesh = True
        self._init_borders()

    @content_size.transformation
    def set_contentsize(self, size, border, margin, padding):
        x = size.x - border.y - border.w - padding.y - padding.w - margin.y - margin.w
        y = size.y - border.x - border.z - padding.y - padding.z - margin.x - margin.z
        return (x, y)


    @border_size.transformation
    def weewewwe(self, size, border, margin):
        x = size.x - border.y - border.w - margin.y - margin.w
        y = size.y - border.x - border.z - margin.x - margin.z
        return (x, y)


    @content_position.transformation
    def swtwef(self, position, border, margin, padding):
        x = position.x + border.w + padding.w + margin.w
        y = position.y + border.x + padding.x + margin.x
        return (x, y, position.z, position.w)


    @border_color.on_change 
    @content_size.on_change 
    def _flag_create_mesh(self, *a):
        self._require_create_mesh = True


    def _init_borders(self):
        self.border_program = BorderProgram()
        self.border_mesh = StridedVertexMesh(np.empty(0, dtype=np.dtype([
            ('vertex', np.float32, 4),
            ('color', np.float32, 4)
        ])), GL_TRIANGLES, attribute_locations=self.border_program.attributes)


    def _create_mesh(self):
        b = self.border
        c = self.border_color
        s =  self.border_size
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


    def _tick(self):
        if self._require_create_mesh:
            self._create_mesh()
            self._require_create_mesh = False
        self.widget.tick()

    def _render(self):
        self.widget.draw()
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
        self.uniform_block_binding('camera', GlConfig.STATE.RESERVED_BUFFER_BASE['gpupy.gl.camera'])


