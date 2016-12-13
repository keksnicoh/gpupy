class Frame():


    def __init__(self, camera, mat_model=None, inner_camera=None, viewport=None):

        self._mat_model = None
        self.set_mat_model(mat_model or ModelMatrix())
        
        pass

    @classmethod 
    def create_frame(self, camera, size, position, inner_camera=None, viewport=None):
        pass

    def set_size(self, size):
        pass 

    def set_rotation(self, rotation):
        pass 

    def set_position(self, position):
        pass 

    def upload_mat_model(self):
        pass

    def set_mat_model(self, mat_model):
        self._mat_model = mat_model
        if hasattr(self.mat_model, 'on_change'):
            self._mat_model.on_change.append(self.upload_mat_model)

    def draw(self):
        self.use()
        self.draw_inner()

        self.unuse()

    def draw_inner(self):
        pass

