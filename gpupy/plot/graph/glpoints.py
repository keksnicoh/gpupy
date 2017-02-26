#-*- coding: utf-8 -*-
"""
simple glpoints graph

:author: keksnicoh
"""
from . import DomainGraph, DomainProgram
from gpupy.plot import domain, plotter2d

from gpupy.gl.common import attributes
from gpupy.gl import GPUPY_GL as G_, Shader, components
from OpenGL.GL import (
    GL_VERTEX_SHADER, GL_FRAGMENT_SHADER, glEnable, glBindVertexArray,
    GL_PROGRAM_POINT_SIZE, glBindVertexArray, glDrawArrays,
    glGenVertexArrays, GL_POINTS)

import os 

class GlPointsGraph(DomainGraph):

    def __init__(self, domain=None):
        super().__init__(domain)
        self.kernel = None

    def init(self): 
        self._init_program()
        self._init_vao()

    def _init_program(self):
        self.program = _p = DomainProgram() 

        vert_path = os.path.join(os.path.dirname(__file__), 'glpoints.vrt.glsl')
        _p.shaders.append(Shader(GL_VERTEX_SHADER, open(vert_path).read()))

        vert_path = os.path.join(os.path.dirname(__file__), 'glpoints.frg.glsl')
        _p.shaders.append(Shader(GL_FRAGMENT_SHADER, open(vert_path).read()))

        _p.declare_uniform('camera', components.camera.Camera2D.DTYPE, variable='camera')
        _p.declare_uniform('plot', plotter2d.Plotter2d.UBO_DTYPE, variable='plot')

        _p.get_shader(GL_VERTEX_SHADER).substitutions.update({
            'vrt_kernl': self.kernel,
            'DOMAIN': self.domains[self.main_domain][1]
        })

        _p.prepare_domains(self.domains)
        _p.link()
        
        _p.uniform_block_binding('plot', G_.CONTEXT.buffer_base('gpupy.plot.plotter2d'))
        _p.uniform_block_binding('camera', G_.CONTEXT.buffer_base('gpupy.gl.camera'))

    def _init_vao(self):
        self.vao = glGenVertexArrays(1)
        glBindVertexArray(self.vao)

        for domain in self.domains.values():
            if hasattr(domain[0], 'attrib_pointers'):
                domain[0].attrib_pointers(domain[1], self.program.attributes)

        glBindVertexArray(0)

    def draw(self):
        glEnable(GL_PROGRAM_POINT_SIZE)
        self.program.use()
        glBindVertexArray(self.vao)
        glDrawArrays(GL_POINTS, 0, len(self[self.main_domain]))
        glBindVertexArray(0)
        self.program.unuse()