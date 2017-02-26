#http://python.6.x6.nabble.com/Programs-that-need-opengl-won-t-run-td5049035.html

from OpenGL import GL
from PyQt5 import Qt

class GlQWindow(Qt.QWindow):
    def __init__(self):
        super().__init__()
        format = Qt.QSurfaceFormat()
        format.setVersion(2, 0)
        format.setProfile(Qt.QSurfaceFormat.CompatibilityProfile)
        format.setStereo(False)
        format.setSwapBehavior(Qt.QSurfaceFormat.DoubleBuffer)
        self.setSurfaceType(Qt.QWindow.OpenGLSurface)
        self.context = Qt.QOpenGLContext()
        self.context.setFormat(format)
        if not self.context.create():
            raise Exception('self.context.create() failed')
        self.create()

    def exposeEvent(self, ev):
        ev.accept()
        if self.isExposed() and self.isVisible():
            self.update()

    def makeCurrent(self):
        self.context.makeCurrent(self)

    def swapBuffers(self):
        self.context.swapBuffers(self)

    def update(self):
        self.makeCurrent()
        GL.glClearColor(0,0,0,0)
        GL.glClearDepth(1)
        GL.glClear(GL.GL_COLOR_BUFFER_BIT | GL.GL_DEPTH_BUFFER_BIT)
        GL.glBegin(GL.GL_TRIANGLES)
        GL.glVertex2f(0.5, 1)
        GL.glVertex2f(1, 0)
        GL.glVertex2f(0, 0)
        GL.glEnd()
        GL.glFlush()
        self.swapBuffers()


app = Qt.QApplication([])
glQWindow = GlQWindow()
glQWindowWidget = Qt.QWidget.createWindowContainer(glQWindow, None, Qt.Qt.Widget)
glQWindowWidget.show()
app.exec_()