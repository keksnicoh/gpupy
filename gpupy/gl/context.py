"""
basic context api for integrating different context managers
like QT, GLFW, SDL, ...
:author: keksnicoh
"""

from gpupy.gl.common import attributes, Event
from gpupy.gl import GPUPY_GL

class ContextException(Exception): pass 
class CloseContextException(ContextException): pass

class Context():
    """
    context API:

    __gl_init_context__         initialized the OpenGL context
    __gl_context_enable__       enables the OpenGL context
    __gl_cycle__                one full cycle (tick, draw, ...)
    __del__                     must be implemented to provide
                                destruction of the context

    events:
    -------
    on_ready        when the context is ready to let 
                    the OpenGL.GL functions do their job.

    on_cycle        when the cycle logic should be executed

    on_resize       when the context was resized. It is allowed
                    to perform the tick and rendering logic
                    like on_cycle to provide fluid window resizing.

    """
    size       = attributes.VectorAttribute(2)
    resolution = attributes.VectorAttribute(2)
    position   = attributes.VectorAttribute(2)
    title      = attributes.CastedAttribute(str, 'window')
    visible    = attributes.CastedAttribute(bool)

    def __init__(self):
        self.gl_buffer_base_register = {}
        self._next_free_gl_buffer_base_index = 0

        self.on_ready  = Event()
        self.on_cycle  = Event()
        self.on_resize = Event()

        self.active_keys = set()

    def buffer_base(self, name, index=None):
        """ reserves a buffer base with a **name** at **index**.
            if no **index** was given, the next free buffer base
            will be reserved. 

            The reserved buffer index is then returned. 

            Usage:
            ```python
            from gpupy.gl import VertexBuffer, GPUPY_GL

            ubo = VertexBuffer.to_device(ndarray, target=UNIFORM_BUFFER)
            ubo.bind_buffer_base(GPUPY_GL.CONTEXT.buffer_base('some_name'))
            ```
            """
        if not name in self.gl_buffer_base_register:
            if index is not None and index in self.gl_buffer_base_register:
                raise RuntimeError('allready registred')
            self.gl_buffer_base_register[name] = index or self._next_free_gl_buffer_base_index
            self._next_free_gl_buffer_base_index += 1
        return self.gl_buffer_base_register[name]

    def __gl_init_context__(self):
        """ initializes OpenGL context """
        raise NotImplementedError('abstract method')

    def __gl_context_enable__(self):
        """ activates OpenGL context """
        GPUPY_GL.CONTEXT = self

    def __gl_cycle__(self):
        """
        during a cycle all calculations and renderings of a 
        frame are done. A cycle should be stopped by raising a 
        CloseContextException.
        """
        pass

    def __del__(self):
        """ remove the OpenGL context """
        raise NotImplementedError('abstract method')

# keyboard shortcuts
KEY_SPACE            = 32
KEY_APOSTROPHE       = 39
KEY_COMMA            = 44
KEY_MINUS            = 45
KEY_PERIOD           = 46
KEY_SLASH            = 47
KEY_0                = 48
KEY_1                = 49
KEY_2                = 50
KEY_3                = 51
KEY_4                = 52
KEY_5                = 53
KEY_6                = 54
KEY_7                = 55
KEY_8                = 56
KEY_9                = 57
KEY_SEMICOLON        = 59
KEY_EQUAL            = 61
KEY_A                = 65
KEY_B                = 66
KEY_C                = 67
KEY_D                = 68
KEY_E                = 69
KEY_F                = 70
KEY_G                = 71
KEY_H                = 72
KEY_I                = 73
KEY_J                = 74
KEY_K                = 75
KEY_L                = 76
KEY_M                = 77
KEY_N                = 78
KEY_O                = 79
KEY_P                = 80
KEY_Q                = 81
KEY_R                = 82
KEY_S                = 83
KEY_T                = 84
KEY_U                = 85
KEY_V                = 86
KEY_W                = 87
KEY_X                = 88
KEY_Y                = 89
KEY_Z                = 90
KEY_LEFT_BRACKET     = 91
KEY_BACKSLASH        = 92
KEY_RIGHT_BRACKET    = 93
KEY_GRAVE_ACCENT     = 96
KEY_WORLD_1          = 161
KEY_WORLD_2          = 162
KEY_ESCAPE           = 256
KEY_ENTER            = 257
KEY_TAB              = 258
KEY_BACKSPACE        = 259
KEY_INSERT           = 260
KEY_DELETE           = 261
KEY_RIGHT            = 262
KEY_LEFT             = 263
KEY_DOWN             = 264
KEY_UP               = 265
KEY_PAGE_UP          = 266
KEY_PAGE_DOWN        = 267
KEY_HOME             = 268
KEY_END              = 269
KEY_CAPS_LOCK        = 280
KEY_SCROLL_LOCK      = 281
KEY_NUM_LOCK         = 282
KEY_PRINT_SCREEN     = 283
KEY_PAUSE            = 284
KEY_F1               = 290
KEY_F2               = 291
KEY_F3               = 292
KEY_F4               = 293
KEY_F5               = 294
KEY_F6               = 295
KEY_F7               = 296
KEY_F8               = 297
KEY_F9               = 298
KEY_F10              = 299
KEY_F11              = 300
KEY_F12              = 301
KEY_F13              = 302
KEY_F14              = 303
KEY_F15              = 304
KEY_F16              = 305
KEY_F17              = 306
KEY_F18              = 307
KEY_F19              = 308
KEY_F20              = 309
KEY_F21              = 310
KEY_F22              = 311
KEY_F23              = 312
KEY_F24              = 313
KEY_F25              = 314
KEY_KP_0             = 320
KEY_KP_1             = 321
KEY_KP_2             = 322
KEY_KP_3             = 323
KEY_KP_4             = 324
KEY_KP_5             = 325
KEY_KP_6             = 326
KEY_KP_7             = 327
KEY_KP_8             = 328
KEY_KP_9             = 329
KEY_KP_DECIMAL       = 330
KEY_KP_DIVIDE        = 331
KEY_KP_MULTIPLY      = 332
KEY_KP_SUBTRACT      = 333
KEY_KP_ADD           = 334
KEY_KP_ENTER         = 335
KEY_KP_EQUAL         = 336
KEY_LEFT_SHIFT       = 340
KEY_LEFT_CONTROL     = 341
KEY_LEFT_ALT         = 342
KEY_LEFT_SUPER       = 343
KEY_RIGHT_SHIFT      = 344
KEY_RIGHT_CONTROL    = 345
KEY_RIGHT_ALT        = 346
KEY_RIGHT_SUPER      = 347
KEY_MENU             = 348
KEY_LAST             = KEY_MENU

KEY_EVENT_RELEASE = 0
KEY_EVENT_PRESS  = 1
KEY_EVENT_REPEAT = 2
