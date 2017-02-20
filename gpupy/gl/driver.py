CONCEPT ... ... ... class Driver():

    def __init__(self, version): 
        self.contexts = []
        self.version = version

    def run():
        """
        runs the application
        """
        if not self._initialized:
            self.init()

        for window in self.windows:
            window.__gl_context_enable__()
            window.on_ready(window)

        # main cycle
        while self.active():
            glfwPollEvents()
            for window in self.windows:
                try:
                    window.__gl_cycle__()
                except CloseContextException as e:
                    GLFW_Application._dbg('close window', '...')
                    self.windows.remove(window)
                    del window
                    GLFW_Application._dbg('window closed', 'OK')
            else:
                self.terminate()
                yield False
                return
            yield True
        self.terminate()

    def __gl_driver_init__(self): pass 

    def __del__(self): pass 