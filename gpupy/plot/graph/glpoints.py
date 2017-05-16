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
from time import time

class GlPointsGraph(DomainGraph):

    def __init__(self, domain=None, kernel=None):
        super().__init__(domain)
        self.kernel = kernel or """vec2 kernel() { return ${DOMAIN}; } """
        self.resolution.on_change.append(self._changes)
        self.viewport.on_change.append(self._changes)
        self.viewport.on_change.append(self._changes)
        self._dynamic_test = False
        self._require_render = True
        self.ticker = time()
    def _changes(self, *e):
        self._require_render = True
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
            'vrt_kernl': self.kernel.replace('${COLOR}', 'v_col').replace('${SIZE}', 'gl_PointSize'),
            'DOMAIN': self.domains[self.main_domain].glsl_identifier[0][1]
        })

        _p.prepare_domains(self.domains)
        _p.link()
        
        _p.uniform_block_binding('plot', G_.CONTEXT.buffer_base('gpupy.plot.plotter2d'))
        _p.uniform_block_binding('camera', G_.CONTEXT.buffer_base('gpupy.gl.camera'))

        txunits = []
        for dname, _d in self.domains.items():
            _d.domain.enable(txunits, self.program, _d.prefix)

    def _init_vao(self):
        self.vao = glGenVertexArrays(1)
        glBindVertexArray(self.vao)

        for _d in self.domains.values():
            if hasattr(_d.domain, 'attrib_pointers'):
                _d.domain.attrib_pointers(_d.prefix, self.program.attributes)

        glBindVertexArray(0)


    def gtick(self, gtick):
        gtick.require_render = self._require_render or self._dynamic_test
        self.program.uniform('u_resolution', self.resolution.xy)
        self.program.uniform('u_viewport', self.viewport.xy)
        self.program.uniform('ticker_test', time() - self.ticker)

    def render(self):


        length = None
        txunits = []
        for dname, _d in self.domains.items():
            _d.domain.enable(txunits, self.program, _d.prefix)
            if hasattr(_d.domain, 'attrib_pointers'):
                length = len(_d.domain)

        glEnable(GL_PROGRAM_POINT_SIZE)
        self.program.use()
        glBindVertexArray(self.vao)
        glDrawArrays(GL_POINTS, 0, length)
        glBindVertexArray(0)
        self.program.unuse()

        self._require_render = False