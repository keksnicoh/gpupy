"""
@author Nicolas 'keksnicoh' Heimann <nicolas.heimann@gmail.com>
"""
from gpupy.gl.util import CommandQueue, Event
from gpupy.gl import Gl
from gpupy.gl.common import *

from OpenGL.GL import *
from gpupy.gl.vendor.glfw import *
from termcolor import colored

default_driver = GlDriver('4.1', core_profile=True, forward_compat=True)

KEYBOARD_MAP = {
    GLFW_KEY_SPACE: KEY_SPACE,
    GLFW_KEY_APOSTROPHE: KEY_APOSTROPHE,
    GLFW_KEY_COMMA: KEY_COMMA,
    GLFW_KEY_MINUS: KEY_MINUS,
    GLFW_KEY_PERIOD: KEY_PERIOD,
    GLFW_KEY_SLASH: KEY_SLASH,
    GLFW_KEY_0: KEY_0,
    GLFW_KEY_1: KEY_1,
    GLFW_KEY_2: KEY_2,
    GLFW_KEY_3: KEY_3,
    GLFW_KEY_4: KEY_4,
    GLFW_KEY_5: KEY_5,
    GLFW_KEY_6: KEY_6,
    GLFW_KEY_7: KEY_7,
    GLFW_KEY_8: KEY_8,
    GLFW_KEY_9: KEY_9,
    GLFW_KEY_SEMICOLON: KEY_SEMICOLON,
    GLFW_KEY_EQUAL: KEY_EQUAL,
    GLFW_KEY_A: KEY_A,
    GLFW_KEY_B: KEY_B,
    GLFW_KEY_C: KEY_C,
    GLFW_KEY_D: KEY_D,
    GLFW_KEY_E: KEY_E,
    GLFW_KEY_F: KEY_F,
    GLFW_KEY_G: KEY_G,
    GLFW_KEY_H: KEY_H,
    GLFW_KEY_I: KEY_I,
    GLFW_KEY_J: KEY_J,
    GLFW_KEY_K: KEY_K,
    GLFW_KEY_L: KEY_L,
    GLFW_KEY_M: KEY_M,
    GLFW_KEY_N: KEY_N,
    GLFW_KEY_O: KEY_O,
    GLFW_KEY_P: KEY_P,
    GLFW_KEY_Q: KEY_Q,
    GLFW_KEY_R: KEY_R,
    GLFW_KEY_S: KEY_S,
    GLFW_KEY_T: KEY_T,
    GLFW_KEY_U: KEY_U,
    GLFW_KEY_V: KEY_V,
    GLFW_KEY_W: KEY_W,
    GLFW_KEY_X: KEY_X,
    GLFW_KEY_Y: KEY_Y,
    GLFW_KEY_Z: KEY_Z,
    GLFW_KEY_LEFT_BRACKET: KEY_LEFT_BRACKET,
    GLFW_KEY_BACKSLASH: KEY_BACKSLASH,
    GLFW_KEY_RIGHT_BRACKET: KEY_RIGHT_BRACKET,
    GLFW_KEY_GRAVE_ACCENT: KEY_GRAVE_ACCENT,
    GLFW_KEY_WORLD_1: KEY_WORLD_1,
    GLFW_KEY_WORLD_2: KEY_WORLD_2,
    GLFW_KEY_ESCAPE: KEY_ESCAPE,
    GLFW_KEY_ENTER: KEY_ENTER,
    GLFW_KEY_TAB: KEY_TAB,
    GLFW_KEY_BACKSPACE: KEY_BACKSPACE,
    GLFW_KEY_INSERT: KEY_INSERT,
    GLFW_KEY_DELETE: KEY_DELETE,
    GLFW_KEY_RIGHT: KEY_RIGHT,
    GLFW_KEY_LEFT: KEY_LEFT,
    GLFW_KEY_DOWN: KEY_DOWN,
    GLFW_KEY_UP: KEY_UP,
    GLFW_KEY_PAGE_UP: KEY_PAGE_UP,
    GLFW_KEY_PAGE_DOWN: KEY_PAGE_DOWN,
    GLFW_KEY_HOME: KEY_HOME,
    GLFW_KEY_END: KEY_END,
    GLFW_KEY_CAPS_LOCK: KEY_CAPS_LOCK,
    GLFW_KEY_SCROLL_LOCK: KEY_SCROLL_LOCK,
    GLFW_KEY_NUM_LOCK: KEY_NUM_LOCK,
    GLFW_KEY_PRINT_SCREEN: KEY_PRINT_SCREEN,
    GLFW_KEY_PAUSE: KEY_PAUSE,
    GLFW_KEY_F1: KEY_F1,
    GLFW_KEY_F2: KEY_F2,
    GLFW_KEY_F3: KEY_F3,
    GLFW_KEY_F4: KEY_F4,
    GLFW_KEY_F5: KEY_F5,
    GLFW_KEY_F6: KEY_F6,
    GLFW_KEY_F7: KEY_F7,
    GLFW_KEY_F8: KEY_F8,
    GLFW_KEY_F9: KEY_F9,
    GLFW_KEY_F10: KEY_F10,
    GLFW_KEY_F11: KEY_F11,
    GLFW_KEY_F12: KEY_F12,
    GLFW_KEY_F13: KEY_F13,
    GLFW_KEY_F14: KEY_F14,
    GLFW_KEY_F15: KEY_F15,
    GLFW_KEY_F16: KEY_F16,
    GLFW_KEY_F17: KEY_F17,
    GLFW_KEY_F18: KEY_F18,
    GLFW_KEY_F19: KEY_F19,
    GLFW_KEY_F20: KEY_F20,
    GLFW_KEY_F21: KEY_F21,
    GLFW_KEY_F22: KEY_F22,
    GLFW_KEY_F23: KEY_F23,
    GLFW_KEY_F24: KEY_F24,
    GLFW_KEY_F25: KEY_F25,
    GLFW_KEY_KP_0: KEY_KP_0,
    GLFW_KEY_KP_1: KEY_KP_1,
    GLFW_KEY_KP_2: KEY_KP_2,
    GLFW_KEY_KP_3: KEY_KP_3,
    GLFW_KEY_KP_4: KEY_KP_4,
    GLFW_KEY_KP_5: KEY_KP_5,
    GLFW_KEY_KP_6: KEY_KP_6,
    GLFW_KEY_KP_7: KEY_KP_7,
    GLFW_KEY_KP_8: KEY_KP_8,
    GLFW_KEY_KP_9: KEY_KP_9,
    GLFW_KEY_KP_DECIMAL: KEY_KP_DECIMAL,
    GLFW_KEY_KP_DIVIDE: KEY_KP_DIVIDE,
    GLFW_KEY_KP_MULTIPLY: KEY_KP_MULTIPLY,
    GLFW_KEY_KP_SUBTRACT: KEY_KP_SUBTRACT,
    GLFW_KEY_KP_ADD: KEY_KP_ADD,
    GLFW_KEY_KP_ENTER: KEY_KP_ENTER,
    GLFW_KEY_KP_EQUAL: KEY_KP_EQUAL,
    GLFW_KEY_LEFT_SHIFT: KEY_LEFT_SHIFT,
    GLFW_KEY_LEFT_CONTROL: KEY_LEFT_CONTROL,
    GLFW_KEY_LEFT_ALT: KEY_LEFT_ALT,
    GLFW_KEY_LEFT_SUPER: KEY_LEFT_SUPER,
    GLFW_KEY_RIGHT_SHIFT: KEY_RIGHT_SHIFT,
    GLFW_KEY_RIGHT_CONTROL: KEY_RIGHT_CONTROL,
    GLFW_KEY_RIGHT_ALT: KEY_RIGHT_ALT,
    GLFW_KEY_RIGHT_SUPER: KEY_RIGHT_SUPER,
    GLFW_KEY_MENU: KEY_MENU,
    GLFW_KEY_LAST: KEY_LAST,
}

GLFW_KEY_OPTION = {
    GLFW_RELEASE: KEY_EVENT_RELEASE,
    GLFW_PRESS: KEY_EVENT_PRESS,
    GLFW_REPEAT: KEY_EVENT_REPEAT,
}

class GLFW_Application():

    DEBUG = False

    """
    allows to register a framebuffer on binding.
    this enabled to reactivate last active framebuffers.
    """
    GL__ACTIVE_FRAMEBUFFER = []

    """
    initializes opengl & glfw. handles glfw windows
    and route events to windows
    """
    def __init__(self, driver=default_driver):
        """general window configuration"""
        self.exit    = False
        self.windows = []
        self.driver  = driver

        GLFW_Application._dbg("init GLFW", '...')
        self.init_glfw()

        GLFW_Application._dbg("load {}".format(colored('OPENGL_CORE_PROFILE 4.10', 'red')), '...')
        self.init_gl_driver()

        self._initialized = False

    def init_gl_driver(self):
        """setup opengl version"""
        glfwWindowHint(GLFW_CONTEXT_VERSION_MAJOR, self.driver.version[0]);
        glfwWindowHint(GLFW_CONTEXT_VERSION_MINOR, self.driver.version[1]);

        if self.driver.forward_compat != True:
            raise RuntimeError('driver.forward_compat=False not supported in GLFW_Application at the moment')
        if self.driver.core_profile != True:
            raise RuntimeError('driver.core_profile=False not supported in GLFW_Application at the moment')

        glfwWindowHint(GLFW_OPENGL_FORWARD_COMPAT, glbool(True));
        glfwWindowHint(GLFW_OPENGL_PROFILE, GLFW_OPENGL_CORE_PROFILE);

    def init(self):
        # initialize windows

       # pos_x = 50
       # pos_y = 150
        for window in self.windows:
            GLFW_Application._dbg('initialize glfw window', '...')
            window.init_glfw()
          #  window.set_position(pos_x, pos_y)
           # pos_x += window.width + 10

        GLFW_Application._dbg('  + Vendor             {}'.format(colored(glGetString(GL_VENDOR), 'cyan')))
        GLFW_Application._dbg('  + Opengl version     {}'.format(colored(glGetString(GL_VERSION), 'cyan')))
        GLFW_Application._dbg('  + GLSL Version       {}'.format(colored(glGetString(GL_SHADING_LANGUAGE_VERSION), 'cyan')))
        GLFW_Application._dbg('  + Renderer           {}'.format(colored(glGetString(GL_RENDERER), 'cyan')))
        GLFW_Application._dbg('  + GLFW3              {}'.format(colored(glfwGetVersion(), 'cyan')))
        GLFW_Application._dbg("application is ready to use.", 'OK')

        self._initialized = True

    def run(self):
        """
        runs the application
        """
        if not self._initialized:
            self.init()

        for window in self.windows:
            window.init()

        # main cycle
        while self.active():
            glfwPollEvents()
            for window in self.windows:
                if window.active():
                    window.cycle()
                else:
                    GLFW_Application._dbg('close window', '...')
                    self.windows.remove(window)
                    del window
                    GLFW_Application._dbg('window closed', 'OK')

        self.terminate()

    def init_glfw(self):
        """initialize glfw"""
        if not glfwInit():
            raise RuntimeError('glfw.Init() error')

    def active(self):
        if self.exit:
            return False
        if not len(self.windows):
            return False
        if not self.windows[0].active():
            return False
        return True

    def terminate(self):
        GLFW_Application._dbg("shutdown", '...')
        glfwTerminate()
        GLFW_Application._dbg("goodbye", 'OK')

    @classmethod
    def _dbg(cls, text, state=None):
        if state is not None:
            if state == 'OK':   state = colored(state, 'green')
            if state == 'FAIL': state = colored(state, 'red')
            if state == '...':  state = colored(state, 'yellow')

            text = '[{}] {}'.format(state, text)
        gpupy_gl_debug(text)

class Keyboard():
    def __init__(self):
        self.active = set()
        self.action = set()

class GLFW_Window():
    """
    glfw window wrapper.

    a window must have a controller, all events will be redirected
    into the given controller. a GLFW_Window does not render something,
    it is the adapter between a Controller and Glfw.
    """
    def __init__(self, width, height, title='no title', x=None, y=None, hidden=False):
        """
        basic state initialization.
        """
        self.initial_size = (width, height)
        self.title = title
        self.x = x
        self.y = y

        self.event_queue = CommandQueue()

        self._glfw_window = None
        self._glfw_initialized = False
        self._active = True

        self.keyboard = Keyboard()

        self.on_init = Event()
        self.on_cycle = Event()
        self.on_close = Event()
        self.on_resize = Event()
        self.on_framebuffer_resize = Event()

        self.gl_state = GlState()
        self._hidden = hidden
        self._in_cycle = False

        self._frambuffer_size = None

    def init_glfw(self):
        """
        glfw initialization.
        """
        if self._hidden:
            glfwWindowHint(GLFW_VISIBLE, 0)

        self._glfw_window = glfwCreateWindow(self.initial_size[0], self.initial_size[1], self.title)

        if not self._glfw_window:
            raise RuntimeError('glfw.CreateWindow() error')
        self._glfw_initialized = True


    def init(self):
        """
        initializes controller and events
        """

        glfwMakeContextCurrent(self._glfw_window)
        Gl.STATE = self.gl_state
        
        glfwSetWindowSizeCallback(self._glfw_window, self.resize_callback)
        glfwSetKeyCallback(self._glfw_window, self.key_callback)
        glfwSetFramebufferSizeCallback(self._glfw_window, self.framebuffer_size_callback)

        self._frambuffer_size = glfwGetFramebufferSize(self._glfw_window)

        self.on_init()

    def framebuffer_size_callback(self, window, width, height):
        self._frambuffer_size = (width, height)
        self.on_framebuffer_resize((width, height))

    def key_callback(self, window, keycode, scancode, action, option):
        """ put glfw keyboard event data into active and
            pressed keyboard buffer """
        if action == GLFW_PRESS:
            self.keyboard.active.add(KEYBOARD_MAP[keycode])
            self.keyboard.action.add((KEYBOARD_MAP[keycode], GLFW_KEY_OPTION[option]))
        elif action == GLFW_RELEASE:
            self.keyboard.active.remove(KEYBOARD_MAP[keycode])
        elif action == GLFW_REPEAT:
            self.keyboard.action.add((KEYBOARD_MAP[keycode], GLFW_KEY_OPTION[option]))

    def get_framebuffer_size(self):
        return self._frambuffer_size

    def resize_callback(self, win, width, height):
        """ triggers on_resize event queue and swaps GLFW buffers."""
        if len(self.on_resize):
            # at this point we only make a new context if we are not just
            # within GLFW_Application.cycle method. E.g. if GLFW_Window.set_size()
            # was performed within the GLFW_Window.cycle() method.
            if not self._in_cycle:
                glfwMakeContextCurrent(self._glfw_window)
                Gl.STATE = self.gl_state

            self.on_resize()

            if not self._in_cycle:
                glfwSwapBuffers(self._glfw_window)


    def cycle(self):
        """ performs a window cycle. A window cycle is allowed to
            dispatch business logic and to render to the OpenGL buffers """
        self._in_cycle = True

        glfwMakeContextCurrent(self._glfw_window)
        Gl.STATE = self.gl_state

        self.event_queue.queue(self.resize_callback)
        self.on_cycle()
        glfwSwapBuffers(self._glfw_window)

        self._in_cycle = False


    def active(self):
        """ returns whether the window is active or should be closed
            by the main GLFW_Application instance """
        return self._active and not glfwWindowShouldClose(self._glfw_window)


    # some simple wrappers
    def get_size(self): return glfwGetWindowSize(self._glfw_window)
    def set_size(self, size):glfwSetWindowSize(self._glfw_window, *ensure_vec2(int, size))
    def get_window_position(self): return glfwGetWindowPos(self._glfw_window)
    def set_position(self, position): glfwSetWindowPos(self._glfw_window, *ensure_vec2(int, position))

    def __del__(self):
        """ destroys the window. """
        glfwDestroyWindow(self._glfw_window)


class GLFW_WindowFunction:
    """ decorator which creates a single window OpenGL GLFW
        application. Decorated function recieves the window instance
        as well as *args, **kwargs."""
    def __init__(self, f):
        self.f = f

    def __call__(self, width=400, height=400, title="OpenGL GLFW Window", *args, **kwargs):
        app = GLFW_Application()
        window = GLFW_Window(width, height, title=title)
        app.windows.append(window)
        app.init()
        self.f(window, *args, **kwargs)
        app.run()

