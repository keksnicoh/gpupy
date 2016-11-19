from pkgutil import extend_path
__path__ = extend_path(__path__, __name__)

class Gl:
    """
    global application state.

    Since OpenGL is a state-machine it is kind of the developers
    mission to implement a state-less library around it. Most of the
    time it is easy to share some of the OpenGL state in some central
    point to simplify the usage of the library. 

    The STATE attribute contains the GlState of the current running
    OpenGL window instance and is set by the drivers. 

    NOTE: It should always be possible to use all features within this
    library without global states. But in daily business it might be 
    a good thing that one does not have to think about the buffer binding
    indices of certain modules like the camera or the font renderer. 

    The STATE does also contain information about current active Shaders,
    Frambuffers and everything else whih can be bound. 
    """

    STATE = None

    DEBUG = False
    HINTS = True
    WARNINGS = True

    INFO = True