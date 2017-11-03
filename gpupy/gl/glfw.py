"""
provides a gpupy integration of the GLFW 
window context OpenGL library.

:author: keksnicoh
"""
from functools import partial
from gpupy.gl.context import *
from gpupy.gl.vendor.glfw import * 
from gpupy.gl.lib import attributes, Event
from gpupy.gl.lib import *
from gpupy.gl import GPUPY_GL

def_version = GlVersion('4.1', core_profile=True, forward_compat=True)

def bootstrap_gl(version=def_version):
    """ 
    bootstrap GL with a given **def_version** 
    """
    if not glfwInit():
        raise RuntimeError('glfw.Init() error')

    glfwWindowHint(GLFW_CONTEXT_VERSION_MAJOR, version.version[0]);
    glfwWindowHint(GLFW_CONTEXT_VERSION_MINOR, version.version[1]);

    if version.forward_compat != True:
        raise RuntimeError('version.forward_compat=False not supported in GLFW_Application at the moment')
    if version.core_profile != True:
        raise RuntimeError('version.core_profile=False not supported in GLFW_Application at the moment')
    
    glfwWindowHint(GLFW_OPENGL_FORWARD_COMPAT, glbool(True));
    glfwWindowHint(GLFW_OPENGL_PROFILE, GLFW_OPENGL_CORE_PROFILE);

def run(*windows):
    windows = windows[:]
    for window in create_runner(windows):
        if not window():
            windows.remove(window)
def create_runner(windows):
    """
    creates a simple runner 
    """
    while len(windows):
        glfwPollEvents()
        for window in windows:
            try:
                yield window
            except CloseContextException as e:
                windows.remove(window)
                del window
            except Exception as e:
                del windows[:]
                glfwTerminate()
                raise e
    glfwTerminate()        

class GLFW_Window(Context):
    size       = attributes.VectorAttribute(2)
    resolution = attributes.VectorAttribute(2)
    position   = attributes.VectorAttribute(2)
    title      = attributes.CastedAttribute(str, 'window')
    visible    = attributes.CastedAttribute(bool)

    def __init__(self, size=(400, 400), title='gpupy glfw window', bootstrap=True, widget=None):
        super().__init__()
        self._glfw_initialized = False
        self.size = size 
        self.title = title
        self.visible = True 
        self._active = False

        self.on_ready  = Event()
        self.on_cycle  = Event()
        self.on_resize = Event()
        self.on_close = Event()

        
        self.active_keys = set()

        if bootstrap:
            self.bootstrap()

        self.make_context()
        self.widget = widget or (lambda *a: True)

    @visible.on_change
    def set_visible(self, visible):
        if visible:
            glfwShowWindow(self._handle)
        else:
            glfwHideWindow(self._handle)


    @size.on_change
    def set_size(self, size):
        glfwSetWindowSize(self._handle, int(size[0]), int(size[1]))


    def bootstrap(self):
        if self._glfw_initialized:
            raise RuntimeError('allready initialized.')
        self._handle = glfwCreateWindow(int(self.size[0]), int(self.size[1]), self.title)
        if not self._handle:
            raise RuntimeError('glfw.CreateWindow() error')
        glfwWindowHint(GLFW_VISIBLE, int(self.visible))  
        def _v2_callback(attr, window, width, height):
            setattr(self, attr, (width, height))    
        glfwSetWindowSizeCallback(self._handle,      self.resize_callback)
        glfwSetFramebufferSizeCallback(self._handle, partial(_v2_callback, 'resolution'))
        glfwSetWindowCloseCallback(self._handle,     self._close_callback)
        glfwSetKeyCallback(self._handle,             self.key_callback)
        glfwSetWindowTitle(self._handle, 'wewf')
        self.resolution = glfwGetFramebufferSize(self._handle)

        self._glfw_initialized = True

    def resize_callback(self, window, width, height):
        """ triggers on_resize event queue and swaps GLFW buffers. """
        self.size = (width, height)

        if len(self.on_resize):
            # at this point we only make a new context if we are not just
            # within GLFW_Application.cycle method. E.g. if GLFW_Window.set_size()
            # was performed within the GLFW_Window.cycle() method.
            if not self._in_cycle:
                self.__gl_context_enable__()
            self.on_resize(self)
            if not self._in_cycle:
                glfwSwapBuffers(self._handle)

    def key_callback(self, window, keycode, scancode, action, option):
        """ put glfw keyboard event data into active and
            pressed keyboard buffer """
        if action == GLFW_PRESS:
            self.active_keys.add(GLFW_Context.KEYBOARD_MAP[keycode])
        elif action == GLFW_RELEASE:
            self.active_keys.remove(GLFW_Context.KEYBOARD_MAP[keycode])

    def _close_callback(self, *e):
        self.on_close(self)

    def make_context(self):

        if not self._active:
            glfwMakeContextCurrent(self._handle)
            self._active = True

        GPUPY_GL.CONTEXT = self

    def __call__(self):
        self.make_context()

        # GLFW close state
        if glfwWindowShouldClose(self._handle):
            self._active = False 
            return False

        # run widget and close if return value is False
        success = self.widget()
        glfwSwapBuffers(self._handle)
        if not success:
            self._active = False 
            return False

        self._active = False 
        return True

class GLFW_Context(Context):
    KEYBOARD_MAP = {
        GLFW_KEY_SPACE: KEY_SPACE, GLFW_KEY_APOSTROPHE: KEY_APOSTROPHE, GLFW_KEY_COMMA: KEY_COMMA, GLFW_KEY_MINUS: KEY_MINUS, GLFW_KEY_PERIOD: KEY_PERIOD, GLFW_KEY_SLASH: KEY_SLASH,
        GLFW_KEY_0: KEY_0, GLFW_KEY_1: KEY_1, GLFW_KEY_2: KEY_2, GLFW_KEY_3: KEY_3, GLFW_KEY_4: KEY_4, GLFW_KEY_5: KEY_5,
        GLFW_KEY_6: KEY_6, GLFW_KEY_7: KEY_7, GLFW_KEY_8: KEY_8, GLFW_KEY_9: KEY_9, GLFW_KEY_SEMICOLON: KEY_SEMICOLON, GLFW_KEY_EQUAL: KEY_EQUAL, GLFW_KEY_A: KEY_A, GLFW_KEY_B: KEY_B,
        GLFW_KEY_C: KEY_C, GLFW_KEY_D: KEY_D, GLFW_KEY_E: KEY_E, GLFW_KEY_F: KEY_F, GLFW_KEY_G: KEY_G, GLFW_KEY_H: KEY_H, GLFW_KEY_I: KEY_I, GLFW_KEY_J: KEY_J,
        GLFW_KEY_K: KEY_K, GLFW_KEY_L: KEY_L, GLFW_KEY_M: KEY_M, GLFW_KEY_N: KEY_N, GLFW_KEY_O: KEY_O, GLFW_KEY_P: KEY_P, GLFW_KEY_Q: KEY_Q, GLFW_KEY_R: KEY_R,
        GLFW_KEY_S: KEY_S, GLFW_KEY_T: KEY_T, GLFW_KEY_U: KEY_U, GLFW_KEY_V: KEY_V, GLFW_KEY_W: KEY_W, GLFW_KEY_X: KEY_X, GLFW_KEY_Y: KEY_Y, GLFW_KEY_Z: KEY_Z,
        GLFW_KEY_LEFT_BRACKET: KEY_LEFT_BRACKET, GLFW_KEY_BACKSLASH: KEY_BACKSLASH, GLFW_KEY_RIGHT_BRACKET: KEY_RIGHT_BRACKET, GLFW_KEY_GRAVE_ACCENT: KEY_GRAVE_ACCENT, 
        GLFW_KEY_WORLD_1: KEY_WORLD_1, GLFW_KEY_WORLD_2: KEY_WORLD_2, GLFW_KEY_ESCAPE: KEY_ESCAPE, GLFW_KEY_ENTER: KEY_ENTER, GLFW_KEY_TAB: KEY_TAB, GLFW_KEY_BACKSPACE: KEY_BACKSPACE, 
        GLFW_KEY_INSERT: KEY_INSERT, GLFW_KEY_DELETE: KEY_DELETE, GLFW_KEY_RIGHT: KEY_RIGHT, GLFW_KEY_LEFT: KEY_LEFT, GLFW_KEY_DOWN: KEY_DOWN, GLFW_KEY_UP: KEY_UP, 
        GLFW_KEY_PAGE_UP: KEY_PAGE_UP, GLFW_KEY_PAGE_DOWN: KEY_PAGE_DOWN, GLFW_KEY_HOME: KEY_HOME,
        GLFW_KEY_END: KEY_END, GLFW_KEY_CAPS_LOCK: KEY_CAPS_LOCK, GLFW_KEY_SCROLL_LOCK: KEY_SCROLL_LOCK, GLFW_KEY_NUM_LOCK: KEY_NUM_LOCK, GLFW_KEY_PRINT_SCREEN: KEY_PRINT_SCREEN, GLFW_KEY_PAUSE: KEY_PAUSE,
        GLFW_KEY_F1: KEY_F1, GLFW_KEY_F2: KEY_F2, GLFW_KEY_F3: KEY_F3, GLFW_KEY_F4: KEY_F4, GLFW_KEY_F5: KEY_F5, GLFW_KEY_F6: KEY_F6, GLFW_KEY_F7: KEY_F7, GLFW_KEY_F8: KEY_F8,
        GLFW_KEY_F9: KEY_F9, GLFW_KEY_F10: KEY_F10, GLFW_KEY_F11: KEY_F11, GLFW_KEY_F12: KEY_F12, GLFW_KEY_F13: KEY_F13, GLFW_KEY_F14: KEY_F14, GLFW_KEY_F15: KEY_F15, GLFW_KEY_F16: KEY_F16,
        GLFW_KEY_F17: KEY_F17, GLFW_KEY_F18: KEY_F18, GLFW_KEY_F19: KEY_F19, GLFW_KEY_F20: KEY_F20, GLFW_KEY_F21: KEY_F21, GLFW_KEY_F22: KEY_F22, GLFW_KEY_F23: KEY_F23, GLFW_KEY_F24: KEY_F24, GLFW_KEY_F25: KEY_F25,
        GLFW_KEY_KP_0: KEY_KP_0, GLFW_KEY_KP_1: KEY_KP_1, GLFW_KEY_KP_2: KEY_KP_2, GLFW_KEY_KP_3: KEY_KP_3, GLFW_KEY_KP_4: KEY_KP_4, GLFW_KEY_KP_5: KEY_KP_5, GLFW_KEY_KP_6: KEY_KP_6, GLFW_KEY_KP_7: KEY_KP_7,
        GLFW_KEY_KP_8: KEY_KP_8, GLFW_KEY_KP_9: KEY_KP_9, GLFW_KEY_KP_DECIMAL: KEY_KP_DECIMAL, GLFW_KEY_KP_DIVIDE: KEY_KP_DIVIDE, GLFW_KEY_KP_MULTIPLY: KEY_KP_MULTIPLY, GLFW_KEY_KP_SUBTRACT: KEY_KP_SUBTRACT,
        GLFW_KEY_KP_ADD: KEY_KP_ADD, GLFW_KEY_KP_ENTER: KEY_KP_ENTER, GLFW_KEY_KP_EQUAL: KEY_KP_EQUAL, GLFW_KEY_LEFT_SHIFT: KEY_LEFT_SHIFT, GLFW_KEY_LEFT_CONTROL: KEY_LEFT_CONTROL,
        GLFW_KEY_LEFT_ALT: KEY_LEFT_ALT, GLFW_KEY_LEFT_SUPER: KEY_LEFT_SUPER, GLFW_KEY_RIGHT_SHIFT: KEY_RIGHT_SHIFT, GLFW_KEY_RIGHT_CONTROL: KEY_RIGHT_CONTROL, GLFW_KEY_RIGHT_ALT: KEY_RIGHT_ALT,
        GLFW_KEY_RIGHT_SUPER: KEY_RIGHT_SUPER, GLFW_KEY_MENU: KEY_MENU, GLFW_KEY_LAST: KEY_LAST,
    }
    size       = attributes.VectorAttribute(2)
    resolution = attributes.VectorAttribute(2)
    position   = attributes.VectorAttribute(2)
    title      = attributes.CastedAttribute(str, 'window')
    visible    = attributes.CastedAttribute(bool)

    """ 
    a glfw context manages the window created by glfwCreateWindow.
    """
    def __init__(self, size, title='no title'):
        super().__init__()
        self.size = size 
        self.title = title
        self.visible = True
        self._handle = None
        self._glfw_initialized = False
        self._active = False

    def _close_callback(self, *e):
        self.on_close(self)

    @visible.on_change
    def set_visible(self, visible):
        if visible:
            glfwShowWindow(self._handle)
        else:
            glfwHideWindow(self._handle)

    @size.on_change
    def set_size(self, size):
        glfwSetWindowSize(self._handle, int(size[0]), int(size[1]))

    def bootstrap(self):
        if self._glfw_initialized:
            raise RuntimeError('allready initialized.')

        self._handle = glfwCreateWindow(int(self.size[0]), int(self.size[1]), self.title)
        if not self._handle:
            raise RuntimeError('glfw.CreateWindow() error')

        glfwWindowHint(GLFW_VISIBLE, int(self.visible))  

        def _v2_callback(attr, window, width, height):
            setattr(self, attr, (width, height))    
        glfwSetWindowSizeCallback(self._handle,      self.resize_callback)
        glfwSetFramebufferSizeCallback(self._handle, partial(_v2_callback, 'resolution'))
        glfwSetWindowCloseCallback(self._handle,     self._close_callback)
        glfwSetKeyCallback(self._handle,             self.key_callback)
        glfwSetWindowTitle(self._handle, 'wewf')
        self.resolution = glfwGetFramebufferSize(self._handle)

        self._glfw_initialized = True

    def context(self):
        if glfwWindowShouldClose(self._handle):
            self.on_close(self)

        if not self._active:
            glfwMakeContextCurrent(self._handle)
            self._active = True

        super().__gl_context_enable__()

    def resize_callback(self, window, width, height):
        """ triggers on_resize event queue and swaps GLFW buffers. """
        self.size = (width, height)

        if len(self.on_resize):
            # at this point we only make a new context if we are not just
            # within GLFW_Application.cycle method. E.g. if GLFW_Window.set_size()
            # was performed within the GLFW_Window.cycle() method.
            if not self._in_cycle:
                self.__gl_context_enable__()
            self.on_resize(self)
            if not self._in_cycle:
                glfwSwapBuffers(self._handle)

    def key_callback(self, window, keycode, scancode, action, option):
        """ put glfw keyboard event data into active and
            pressed keyboard buffer """
        if action == GLFW_PRESS:
            self.active_keys.add(GLFW_Context.KEYBOARD_MAP[keycode])
        elif action == GLFW_RELEASE:
            self.active_keys.remove(GLFW_Context.KEYBOARD_MAP[keycode])

    def cycle(self):
        if glfwWindowShouldClose(self._handle):
            raise CloseContextException()

        self._in_cycle = True
        self.__gl_context_enable__()
        self.on_cycle(self)
        glfwSwapBuffers(self._handle)
        self._in_cycle = False


    def __del__(self):
        glfwDestroyWindow(self._handle)

def GLFW_run(*windows, version=def_version):
    """ 
    executes a list of GLFW *windows* with a specific
    OpenGL **version** profile. 

    This is a generator which yields the window
    which cycle will be executed next.
    """
    if not glfwInit():
        raise RuntimeError('glfw.Init() error')

    glfwWindowHint(GLFW_CONTEXT_VERSION_MAJOR, version.version[0]);
    glfwWindowHint(GLFW_CONTEXT_VERSION_MINOR, version.version[1]);
    if version.forward_compat != True:
        raise RuntimeError('version.forward_compat=False not supported in GLFW_Application at the moment')
    if version.core_profile != True:
        raise RuntimeError('version.core_profile=False not supported in GLFW_Application at the moment')
    glfwWindowHint(GLFW_OPENGL_FORWARD_COMPAT, glbool(True));
    glfwWindowHint(GLFW_OPENGL_PROFILE, GLFW_OPENGL_CORE_PROFILE);
    #glfwWindowHint(GLFW_DECORATED, False);
    for window in windows:
        window.bootstrap()
        window.context()
        window.on_ready(window)

    while len(windows):
        glfwPollEvents()
        for window in windows:
            try:
                yield window
                window.cycle()

            except CloseContextException as e:
                windows.remove(window)
                del window
            except Exception as e:
                del windows[:]
                glfwTerminate()
                raise e

    glfwTerminate()


class GLFW_window:
    """ decorator which creates a single window OpenGL GLFW
        application. Decorated function recieves the window instance
        as well as *args, **kwargs."""
    def __init__(self, f):
        self.f = f

    def __call__(self, width=400, height=400, title="OpenGL GLFW Window"):
        window = GLFW_Context(size=(width, height), title=title)
        window.on_ready.append(self.f)
        for window in GLFW_run(window):
            pass

