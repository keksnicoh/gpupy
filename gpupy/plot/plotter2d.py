from gpupy.plot.style import *

from gpupy.gl.layout.boxes import BoxLayout
from gpupy.gl.components.camera import Camera2D
from gpupy.gl.components.frame import Frame
from gpupy.gl.util import Event
from gpupy.gl.vector import *
from gpupy.gl.mesh import StridedVertexMesh
from gpupy.gl import *

from OpenGL.GL import * 
import numpy as np 

DEFAULT_STYLE = {
    'border': '1 #000000ff',
    'background-color': '#ffffffff',
    'plot-background-color': '#aaaaaaff',
    'min-size': '100 100',
}
"""

plot graph[] {
    color: xyz
    bla: foo bar
} 

"""

class LayerWidget():
    # BASIC LAYER WIDGET CLASS

    """
    CONCECPT:

    SIZE - POSITION - PADDING - MARGIN - BORDER
    """
    pass

class FrameLayerWidget(LayerWidget):
    pass

class ViewportLayerWidget(LayerWidget):
    pass

class Plotter2d():
    FLAG_SIZE = 1
    FLAG_BORDER = 2

    configuration_space = Vec4Field((0, 0, 0, 0))
    size = Vec2Field()
    position = Vec2Field((0, 0))
    content_size = Vec2Field(listen_to=size)

    def flag(self, name):
        self._flagged.add(name)
        def _listener(*v):
            self._flagged.add(name)
        return _listener

    def __init__(self, size, 
                       position=(0, 0), 
                       configuration_space=(0, 1, 0, 1), 
                       style=DEFAULT_STYLE):
        # state
        self.configuration_space = configuration_space
        self.size = size 
        self.position = position
        self._flagged = set()

        self.style = Style({
            'border': (parse_4f1_1c4, self.flag(self.FLAG_BORDER)),
            'background-color': parse_1c4,
            'plot-background-color': parse_1c4,
            'min-size': (parse_2f1, self.flag(self.FLAG_SIZE)),
        }, style)

        # event hooks
        self.on_pre_plot = Event()
        self.on_post_plot = Event()
        self.on_pre_graph = Event()
        self.on_post_graph = Event()

        # configure layout - connect the layout 
        # size and position directly to the plot size
        # and plot position.
        self._layout = BoxLayout(self.content_size, self.position)

        bw, bc = self.style['border']

        self._layout.scope = {
            # the margin will be a function of the
            # axis labels. It must rescale in such
            # a way that the labels fit into.
            'margin': vec4((10, 10, 10, 10)),
            # inner capture size scaling. 
            'capture_scaling': 1,
            'border': vec4(bw),
            'border_color': vec4(bc),
        }

        self._layout.scope['border'].on_change.append(self.flag(self.FLAG_BORDER))
        self._layout.scope['border_color'].on_change.append(self.flag(self.FLAG_BORDER))

        self.init()

        self.borders(*self._layout.scope['border'], color=self._layout.scope['border_color'])

        self._test_grid = TestGrid()
    def init(self):
        self._init_plot_camera()
        self._init_plot_frame()
        self._init_borders()
        self._init_borders()

    def borders(self, top=2, right=2, bottom=2, left=2, color=(1, 1, 0, 1)):
        """
        set *top*, *right*, *bottom* and *left* border
        width and bordercolor *color*.
        """
        self._layout.scope['border'].xyzw = (top, right, bottom, left)
        self._layout.scope['border_color'].xyzw = color

        if self.FLAG_BORDER in self._flagged:
            # create buffer
            b = self._layout.scope['border'].xyzw
            vertex_count = sum(6*(int(l > 0) + int(l > 0 and b[(i + 1) % 4] > 0)) for i, l in enumerate(b))
            self._border_vertex = np.zeros(vertex_count, self.border_mesh.buffer.dtype)
            
            self.content_size = self.size
            self._layout.calculate()
            self._update_border_mesh()

            self._flagged.remove(self.FLAG_BORDER)

    @content_size.transformation
    def content_size_minimum(self, plot_size):
        """
        calculates the size of the plotframe from 
        given *plot_size*
        """
        m = self._layout.scope['margin']
        b = self._layout.scope['border']

        return (max(plot_size[0], m[1] + b[1] + m[3] + b[3] + self.style['min-size'][0]), 
                max(plot_size[1], m[0] + b[0] + m[2] + b[2] + self.style['min-size'][0]))

    # -- event handlers

    @content_size.on_change
    def size_changed(self, *e):
        self._layout.calculate()
        self._update_border_mesh()

    def _update_border_mesh(self):

        b, c = self._layout.scope['border'], self._layout.scope['border_color']
        p, s = self._layout.boxes['plot'].position, self._layout.boxes['plot'].size 
        # coordinates of plot frame corners
        pf = (p[1], p[0] + s[0], p[1] + s[1], p[0])
        i, v = 0, self._border_vertex
        if b[3] and b[0]:
            # left upper corner
            v[i:i+6] = [
                ((pf[3]-b[3],   pf[0]-b[0], 0, 1), c),
                ((pf[3],        pf[0]-b[0], 0, 1), c),
                ((pf[3],        pf[0],      0, 1), c),
                ((pf[3],        pf[0],      0, 1), c),
                ((pf[3]-b[3],   pf[0],      0, 1), c),
                ((pf[3]-b[3],   pf[0]-b[0], 0, 1), c),
            ]; i+=6
        if b[0]:
            # top
            v[i:i+6] = [
                ((pf[3]-b[3],   pf[0]-b[0], 0, 1), c),
                ((pf[1],        pf[0]-b[0], 0, 1), c),
                ((pf[1],        pf[0],      0, 1), c),
                ((pf[1],        pf[0],      0, 1), c),
                ((pf[3]-b[3],   pf[0]-b[0], 0, 1), c),
                ((pf[3]-b[3],   pf[0],      0, 1), c),
            ]; i+=6
        if b[0] and b[1]:
            # right upper corner
            v[i:i+6] = [
                ((pf[1]+b[1],   pf[0]-b[0], 0, 1), c),
                ((pf[1],        pf[0]-b[0], 0, 1), c),
                ((pf[1],        pf[0],      0, 1), c),
                ((pf[1],        pf[0],      0, 1), c),
                ((pf[1]+b[1],   pf[0],      0, 1), c),
                ((pf[1]+b[1],   pf[0]-b[0], 0, 1), c),
            ]; i+=6
        if b[1]:
            # right
            v[i:i+6] = [
                ((pf[1]+b[1],   pf[0], 0, 1), c),
                ((pf[1],        pf[0], 0, 1), c),
                ((pf[1],        pf[2], 0, 1), c),
                ((pf[1],        pf[2], 0, 1), c),
                ((pf[1]+b[1],   pf[2], 0, 1), c),
                ((pf[1]+b[1],   pf[0], 0, 1), c),
            ]; i+=6
        if b[1] and b[2]:
            # right lower corner
            v[i:i+6] = [
                ((pf[1]+b[1],   pf[2]+b[2], 0, 1), c),
                ((pf[1],        pf[2]+b[2], 0, 1), c),
                ((pf[1],        pf[2],      0, 1), c),
                ((pf[1],        pf[2],      0, 1), c),
                ((pf[1]+b[1],   pf[2],      0, 1), c),
                ((pf[1]+b[1],   pf[2]+b[2], 0, 1), c),
            ]; i+=6
        if b[2]:
            # bottom
            v[i:i+6] = [
                ((pf[3]-b[3],   pf[2]+b[2], 0, 1), c),
                ((pf[1],        pf[2]+b[2], 0, 1), c),
                ((pf[1],        pf[2],      0, 1), c),
                ((pf[1],        pf[2],      0, 1), c),
                ((pf[3]-b[3],   pf[2]+b[2], 0, 1), c),
                ((pf[3]-b[3],   pf[2],      0, 1), c),
            ]; i+=6
        if b[2] and b[3]:
            # left lower corner
            v[i:i+6] = [
                ((pf[3]-b[3],   pf[2]+b[2], 0, 1), c),
                ((pf[3],        pf[2]+b[2], 0, 1), c),
                ((pf[3],        pf[2],      0, 1), c),
                ((pf[3],        pf[2],      0, 1), c),
                ((pf[3]-b[3],   pf[2],      0, 1), c),
                ((pf[3]-b[3],   pf[2]+b[2], 0, 1), c),
            ]; i+=6
        if b[3]:
            # left
            v[i:i+6] = [
                ((pf[3]-b[3],   pf[0], 0, 1), c),
                ((pf[3],        pf[0], 0, 1), c),
                ((pf[3],        pf[2], 0, 1), c),
                ((pf[3],        pf[2], 0, 1), c),
                ((pf[3]-b[3],   pf[2], 0, 1), c),
                ((pf[3]-b[3],   pf[0], 0, 1), c),
            ]; i+=6

        self.border_mesh.buffer.set(v)

        if 'border' in self._flagged:
            self._flagged.remove(self.FLAG_BORDER)

    def _init_borders(self):
        self.border_program = BorderProgram()
        self.border_mesh = StridedVertexMesh(np.empty(0, dtype=np.dtype([
            ('vertex', np.float32, 4),
            ('color', np.float32, 4)
        ])), GL_TRIANGLES, attribute_locations=self.border_program.attributes)

    def _init_plot_camera(self):
        """
        creates a plot camera which is connected to
        the configuration space
        """
        cam_position = self.configuration_space.observe_as_vec3(
            lambda v: (v[0]+np.abs(v[1]-v[0])*0.5, v[2]+np.abs(v[3]-v[2])*0.5, 0))
        cam_screensize = self.configuration_space.observe_as_vec2(
            lambda v: (np.abs(v[1]-v[0]), np.abs(v[3]-v[2])))

        self._plot_camera = Camera2D(cam_screensize, cam_position)

    def _init_plot_frame(self):
        """
        creates main plot frame 
        """
        self._layout.create_box('plot', lambda l: (
            l.scope['margin'][0]            + l.scope['border'][0],               #top
            l.size.x - l.scope['margin'][1] - l.scope['border'][1],               #right
            l.size.y - l.scope['margin'][2] - l.scope['border'][2],               #bottom
            l.scope['margin'][3]            + l.scope['border'][3]                #left
        ), scope=('margin'))
        self._layout.calculate() #XXX

        # connect vectors and setup the frame itself.
        cap_size = self._layout.boxes['plot'].size.observe(
            lambda v: self._layout.scope['capture_scaling'] * v)

        self._plotframe = Frame(size=self._layout.boxes['plot'].size,
                                position=self._layout.boxes['plot'].position,
                                capture_size=cap_size)

    def tick(self, redraw=True):
        pre_plot_event = PrePlotEvent(redraw=redraw)
        self.on_pre_plot(pre_plot_event)

        if pre_plot_event.redraw:
            self._plotframe.use()
            self._plot_camera.enable()

            glClearColor(*self.style['plot-background-color'])
            glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

            self._test_grid.draw()
            self._plotframe.unuse()

        self.on_post_plot()

    def draw(self):
        glClearColor(*self.style['background-color'])
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        self._plotframe.draw() 
        self.border_program.use()
        self.border_mesh.draw()
        self.border_program.unuse()

class PrePlotEvent():
    def __init__(self, redraw=False):
        self.redraw = redraw 

class TestGrid():
    def __init__(self):
        self._program = Program()
        self._program.shaders.append(Shader(GL_VERTEX_SHADER, """
            {% version %}
            {% uniform_block camera %}

            in vec2 vertex;

            void main() {
                gl_Position = camera.mat_projection * camera.mat_view * vec4(vertex, 0, 1);
            }
        """))
        self._program.shaders.append(Shader(GL_FRAGMENT_SHADER, """
            {% version %}

            out vec4 color;
            void main() {
                color = vec4(0, 0, 0, 1);
            }
        """))
        self._program.declare_uniform('camera', Camera2D.DTYPE, variable='camera')
        self._program.link()
        self._program.uniform_block_binding('camera', GlConfig.STATE.RESERVED_BUFFER_BASE['gpupy.gl.camera'])


        self._mesh = StridedVertexMesh(np.array([
            ((0.25, 0),),
            ((0.25, 1),),
            ((0.5, 0),),
            ((0.5, 1),),
            ((0.75, 0),),
            ((0.75, 1),),

            ((0, 0.25),),
            ((1, 0.25),),
            ((0, 0.5),),
            ((1, 0.5),),
            ((0, 0.75),),
            ((1, 0.75),),       
        ], dtype=np.dtype([('vertex', np.float32, 2)])), GL_LINES, attribute_locations=self._program.attributes) 


    def draw(self):
        self._program.use()
        self._mesh.draw()
        self._program.unuse()


class AbstractDomain():
    def set_attribute_locations(self):
        pass
    def get_domain_attributes(self):

        return (
            'x', dtype_of_x,
            'xyz', dtype_of_xyz,
        )

        pass 

    def get_vao(self):
        pass

class TestGraph():
    def __init__(self, domain):
        self.domain = domain

    def prepare(self):
        self.domain.prepare()
        attributes = self.domain.get_domain_attributes()

        glsl = attributes_to_glsl(attributes)
        self.program.subsitute('domain_attributes', glsl)

        self.program.link()
        self.domain.set_attribute_locations(self.program.attributes)

        self.gl_vao_id = self.domain.create_vao()

    def draw(self):
        vao = self.domain.gl_vao_id
        glBindVertexArrays(vao)
        self.program.use()
        glDrawArrays(GL_LINES, len(self.domain))
        self.program.unuse()  
        glBindVertexArrays(0)


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
