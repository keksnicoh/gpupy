from PyQt5.QtGui import (
        QOpenGLBuffer,
        QOpenGLShader,
        QOpenGLShaderProgram,
        QOpenGLVersionProfile,
        QOpenGLVertexArrayObject,
        QSurfaceFormat,
    )
from OpenGL.GL import * 
from PyQt5.QtWidgets import QApplication, QMainWindow, QOpenGLWidget, QWidget, QGridLayout
from gpupy.gl.common import Event
from gpupy.plot.plotter2d import Plotter2d
from gpupy.gl.components.camera import Camera2D
from gpupy.gl import GPUPY_GL
from gpupy.gl.context import Context

class Window(QWidget):
    """Main window."""

    def __init__(self, versionprofile=None, *args, **kwargs):
        """Initialize with an OpenGL Widget."""
        super().__init__(*args, **kwargs)
        widget = Qt5GlWidget(versionprofile=versionprofile)
        widget2 = Qt5GlWidget(versionprofile=versionprofile)
        layout = QGridLayout()
        layout.addWidget(widget, 0, 0)
        layout.addWidget(widget2, 0, 1)
        self.setLayout(layout)


        #self.show()

class EventController:
    def __init__(self):
        self.on_ready = Event()
        self.on_init = Event()
        self.on_cycle = Event()
        self.on_close = Event()

class Qt5GlWidget(QOpenGLWidget):
    def __init__(self, versionprofile=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.versionprofile = versionprofile
        self.setAutoFillBackground(True)
        self.context = Context()
       #self.size = None
    def initializeGL(self):
        GPUPY_GL.CONTEXT = self.context
        size = self.size()
        size = (size.width(), size.height())
        self.camera = Camera2D(screensize=size, position=(0,0,1))

        self.plotter = Plotter2d(size, configuration_space=(0, 1, -1, 1))

        def dd(*e):
            print(e)
        self.plotter.size.on_change.append(dd)
        self.plotter._plot_container.border = (2,2,2,2)
        self.plotter._plot_container.margin = (10, 10, 10, 10)
        #self.border = 3 

    def glDraw(self):
        GPUPY_GL.CONTEXT = self.context
        self.plotter.tick()
        glClearColor(1, 0, 1, 1)
        #glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        self.camera.enable()
        self.plotter.draw()

    def resizeGL(self, w, h):
        glViewport(0, 0, w, h)
        self.plotter.size = (w, h)
        self.camera.screensize = (w, h)
       # self.size = (w, h)
        self.glDraw()

if __name__ == '__main__':
    import sys

    fmt = QSurfaceFormat()
    fmt.setVersion(4, 1)
    fmt.setProfile(QSurfaceFormat.CoreProfile)
    fmt.setSamples(4)
    QSurfaceFormat.setDefaultFormat(fmt)

    vp = QOpenGLVersionProfile()
    vp.setVersion(4, 1)
    vp.setProfile(QSurfaceFormat.CoreProfile)

    app = QApplication(sys.argv)
    window = Window(versionprofile=vp)
    window.show()
    sys.exit(app.exec_())