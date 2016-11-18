#-*- coding: utf-8 -*-
"""
Contains several common objects and helper functions
:author: Nicolas 'keksnicoh' Heimann
"""
from OpenGL.GL import *
from gpupy.gl.util import Event
from gpupy.gl import Gl
import numpy as np
class GlState():
    """
    XXX
    implement all wanted features: framebuffers, buffers etc ...
    """

    def __init__(self):
        self.framebuffer_stack = list()

        self.RESERVED_BUFFER_BASE = {}

        self.reserve_buffer_base('gpupy.gl.camera')
        self.reserve_buffer_base('gpupy.gl.font')

    def reserve_buffer_base(self, key):
        """
        reserves a buffer base index for a given key. 
        returns the reserved buffer base index if the key
        allready has one.
        """
        if key in self.RESERVED_BUFFER_BASE:
            return self.RESERVED_BUFFER_BASE[key]

        if len(self.RESERVED_BUFFER_BASE):
            reserved_indices = self.RESERVED_BUFFER_BASE.values()
            sorted_indiced = sorted(reserved_indices)
            index = sorted_indiced[-1] + 1
        else:
            index = 0
            
        self.RESERVED_BUFFER_BASE[key] = index

        return index

class GlDriver():
    """ represents OpenGL driver profile """
    def __init__(self, version, core_profile=True, forward_compat=True):
        """ initialized glDriver
            :argument version: tuple or a string
            :core_profile: whether core profile should be used
            :forward_compat: see specifications."""
        if type(version) is str:
            prt = version.split('.')
            if len(prt) > 2:
                raise ValueError('Argument version must by either tuple or a string. version examples: "4", "4.0", "3.1"')

            version = (int(prt[0]), 0) if len(prt) == 1 else (int(prt[0]), int(prt[1]))

        self.version = version
        self.core_profile = bool(core_profile)
        self.forward_compat = bool(forward_compat)

    def get_gl_information():
        return {
            'GL_MAX_UNIFORM_BUFFER_BINDINGS': glGetIntegerv(GL_MAX_UNIFORM_BUFFER_BINDINGS),
        }

def gpupy_gl_warning(text):
    """ prints warnings what are generated by gpupy library """
    if Gl.WARNINGS:
        print('\033[31mGPUPY WARNING:\033[0m ' + text)

def gpupy_gl_hint(text):
    """ prints some hints to help the developer """
    if Gl.HINTS:
        print('\033[36mGPUPY HINT:\033[0m ' + text)

def gpupy_gl_debug(text):
    """ prints some hints to help the developer """
    if Gl.DEBUG:
        print('\033[34mGPUPY DEBUG:\033[0m ' + text)

def gpupy_debug_wrap(func, *args, **kwargs):
    if Gl.DEBUG:
        gpupy_gl_debug('{}({}{}{})'.format(
            func.__name__,
            ', '.join(str(a) for a in args),
            ', ' if len(kwargs) and len(args) else '',
            ', '.join('{}={}'.format(k, v) for (k, v) in kwargs.items())))
    func(*args, **kwargs)



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




# some short hand type helpers
def glbool(v): return GL_TRUE if v else GL_FALSE
def glfloat(v): return np.float32(v)
def glint(v): return int(v)
def ensure_vec2(cast=(lambda x: x), *args):
    if len(args) == 1:
        return (cast(args[0][0]), cast(args[0][1]))
    elif len(args) == 2:
        return (cast(args[0]), cast(args[1]))
    else:
        raise ValueError()
def ensure_vec3(cast=(lambda x: x), *args):
    if len(args) == 1:
        return (cast(args[0][0]), cast(args[0][1]), cast(args[0][2]))
    elif len(args) == 3:
        return (cast(args[0]), cast(args[1]), cast(args[2]))
    else:
        raise ValueError()
