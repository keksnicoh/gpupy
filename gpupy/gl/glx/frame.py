
class FrameWidget():
    """
    Frame component uses framebuffer to render a scene on 
    a plane. 

    the state of a Frame is described by the following properties:

    Properties:

    - size: the size of the frame
    - resulution: the size of the texture which captures the scene.
                    e.g. the capture size might be higher than the size
                         of the plane to enable anti aliasing like down
                         sampling.

    - viewport: gpupy.gl.ViewPort
                if not defined the viewport is set to 
                    ViewPort((0, 0), resulution)
    - camera: camera which will be enabled when the Framebuffer 
              starts cawhichpturing
    - camera: camera for rendering the screen


         +----------------------------------------+
         |
         |             capture.x 
         |  c #####################################
         |  a #
      s  |  p #         
      i  |  t #       vp.pos          vp.w
      z  |  u #            x ---------------------
      e  |  r #            |          
      .  |  e #       vp.h | 
      y  |  . #            + ---------------------
         |  y ####################################
         |
         +----------------------------------------+

    """


    size         = attributes.VectorAttribute(2)
    position     = attributes.VectorAttribute(4)
    resulution   = attributes.VectorAttribute(2)
    plane_size   = attributes.ComputedAttribute(size, descriptor=attributes.VectorAttribute(2))
    clear_color  = attributes.VectorAttribute(4)

    def __init__(self, 
                 size, 
                 resulution=None, 
                 position=(0,0,0,1), 
                 multisampling=None, 
                 post_effects=None, 
                 blit=None, 
                 clear_color=(0, 0, 0, 1), 
                 preload_factor=2):
        """
        creates a framebuffer of *size* and *resulution* 
        at *position*.

        if *resulution* is None, the resulution is linked
        to *size*.
        """
        # XXX
        # - multisampling 
        # - post effects
        # - blit/record mode

        super().__init__()
        self._res = None
        self.size         = size
        self.position     = position
        self.resulution = resulution if resulution is not None else self.size
        self.viewport     = Viewport((0, 0), self.resulution)
        self.texture      = None
        self.clear_color  = clear_color
        self.preload_factor = preload_factor
        self._init_capturing()
        self._init_plane()

        

        self._require_resize = False 

    # -- initialization --

    def _init_capturing(self):
        self._res = self.preload_factor*self.resulution.values
        self.texture = Texture2D.empty((*self._res, 4), np.float32)
        self.texture.interpolation_linear()
        self.framebuffer = Framebuffer()
        self.framebuffer.color_attachment(self.texture)
        self.texture.parameter(GL_TEXTURE_WRAP_S, GL_CLAMP_TO_EDGE)
        self.texture.parameter(GL_TEXTURE_WRAP_T, GL_CLAMP_TO_EDGE)

    @resulution.on_change
    def resulution_changed(self, value):
        print('WFWEFWEFFF§§33')
        self._require_resize = True 

    def _init_plane(self):
    	self.texture.activate()

        self.program = create_program(vertex=_GLSL_VRT, fragment=_GLSL_FRG, link=False)
        self.program.declare_uniform('camera', camera.Cartesian2D.DTYPE, variable='camera')
        self.program.link()

        self.program.uniform_blocks['camera'] = GPUPY_GL.CONTEXT.buffer_base('gpupy.gl.camera')
        self.program.uniforms.update({
        	'frame_texture': self.texture
        	'size': self.plane_size.xy,
        	'mat_model': np.identity(4, dtype=np.float32),
        	'position': self.position.xyzw,
        	'rf': (self.resulution[0]/self._res[0], self.resulution[1]/self._res[1]),
        }) 
        self.position.on_change.append(partial(self.program.uniform, 'position'))
        self.size.on_change.append(partial(self.program.uniform, 'size'))

        self.mesh = StridedVertexMesh(mesh3d_rectangle(), 
                                      GL_TRIANGLES, 
                                      attribute_locations=self.program.attributes)

    @plane_size.transformation
    @resulution.transformation
    def normalize(self, v):
        """ to avoid pixel rounding errors """
        # XXX 
        # - is this the best solution?
        v = np.ceil(v)
        return (max(1, v[0]), max(1, v[1]))

    def tick(self):
        if self._require_resize:
            
            if self._res[0] < self.resulution[0] \
            or self._res[1] < self.resulution[1]:
                self._res = self.resulution.values * self.preload_factor
                self.texture.resize(self._res) 
            self.program.uniform('rf', (self.resulution[0]/self._res[0], self.resulution[1]/self._res[1]))
            self._require_resize = False

    def render(self):
        self.draw()

    def draw(self, shader=None):
        shader = shader or self.program
        self.texture.activate()
        shader.use()
        self.mesh.draw()
        shader.unuse()

    def use(self): 
        self.framebuffer.use()
        self.viewport.use((0, 0), np.array(self.resulution, dtype=np.int32))
        glClearColor(*self.clear_color)
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

    def unuse(self): 
        self.viewport.unuse(restore=True)
        self.framebuffer.unuse()

class _CameraProgram(Program):
    def __init__(self, vrt, frg, *args, **kwargs):
        super().__init__(*args, **kwargs)

# ---- GLSL ---------------



_GLSL_VRT = """
{% version %}
{% uniform_block camera %}
in vec4 vertex;
uniform vec4 position;
in vec2 tex;
out vec2 frag_pos;
uniform mat4 mat_model;
uniform vec2 rf;
uniform vec2 size;
void main() {
    gl_Position = camera.mat_projection 
                * camera.mat_view * mat_model 
                * vec4(position.x + size.x*vertex.x, 
                       position.y + size.y*vertex.y, 
                       position.z + vertex.z, 
                       vertex.w);
    frag_pos = tex*rf;
}
"""


_GLSL_FRG = """
{% version %}
uniform sampler2D frame_texture;
in vec2 frag_pos;
out vec4 frag_color;
void main() {
    frag_color = texture(frame_texture, frag_pos);
    //frag_color = vec4(0, frag_pos.y, 0, 1);
}
"""