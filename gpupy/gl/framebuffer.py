#-*- coding: utf-8 -*-
"""
framebuffer utilities

:author: Nicolas 'keksnicoh' Heimann
"""

from OpenGL.GL import * 
from gpupy.gl.texture import gl_texture_id
from gpupy.gl.errors import GlError

def create_framebuffer(color=None, depth=None, stencil=None):
    pass

class Framebuffer():

    def __init__(self):
        self.gl_framebuffer_id = None
        self.on_use = None 
        self.on_unuse = None
        
        self.attachments = {
            'color': [],
            'depth': [],
            'stencil': [],
        }

    def color_attachment(self, texture, n=0, target=None):
        self.use()

        if hasattr(texture, 'gl_target'):
            if target is not None and texture.gl_target != target:
                raise ValueError('explicit declaration of arg target(%s) differs from texture.gl_target(%s)', target, texture.gl_target)
            target = texture.gl_target
        elif target is None:
            target = GL_TEXTURE_2D

        # XXX
        # validate target 
        assert_framebuffer_target(target)

        attachment = globals()['GL_COLOR_ATTACHMENT%d' % n]
        glDrawBuffer(attachment)
        glFramebufferTexture2D(GL_FRAMEBUFFER, attachment, target, gl_texture_id(texture), 0);
        glBindFramebuffer(GL_DRAW_FRAMEBUFFER, 0)
        
        self.unuse()

    def use(self):
        if self.gl_framebuffer_id is None:
            self.gl_framebuffer_id = glGenFramebuffers(1)

        glBindFramebuffer(GL_DRAW_FRAMEBUFFER, self.gl_framebuffer_id)
        if not glCheckFramebufferStatus(GL_FRAMEBUFFER):
            raise GlError('framebuffer is not configured properly.')

    def unuse(self):
        glBindFramebuffer(GL_DRAW_FRAMEBUFFER, 0)

    def blit(): pass


def assert_framebuffer_target(target):
    # XXX
    pass