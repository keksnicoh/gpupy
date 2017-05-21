#-*- coding: utf-8 -*-
"""
simple glprimitives graph

:author: keksnicoh
"""
from . import DomainGraph, DomainProgram
from gpupy.plot import domain, plotter2d

from gpupy.gl.common import attributes
from gpupy.gl import GPUPY_GL as G_, Shader, components
from OpenGL.GL import (
    GL_VERTEX_SHADER, GL_FRAGMENT_SHADER, glEnable, glBindVertexArray,
    GL_PROGRAM_POINT_SIZE, glBindVertexArray, glDrawArrays,
    glGenVertexArrays, GL_POINTS, GL_LINES, GL_LINE_STRIP)
from gpupy.gl.glsl import Template

import os 
from time import time

class GlPrimitivesGraph(DomainGraph):
    DEFAULT_KERNEL = """
        vec2 kernel() { 
            return  ${D.domain}; 
        }
    """

    def __init__(self, domain=None, kernel=None, mode="points", offset=0, length=None):
        super().__init__(domain)
        self.kernel = kernel or self.DEFAULT_KERNEL

        self.resolution.on_change.append(self._properties_changed)
        self.viewport.on_change.append(self._properties_changed)
        self.viewport.on_change.append(self._properties_changed)

        self._kernel_template = None
        self._fragment_kernel_template = None 

        self.offset = offset
        self.length = length

        valid_modes = {'points': GL_POINTS,
                       'lines': GL_LINE_STRIP,
                       'segments': GL_LINES}
        if not mode in valid_modes:
            raise ValueError('invalid mode "{}". Must be "points", "lines" or "segments"'.format(mode))
        self.gl_mode = valid_modes[mode]


    def _properties_changed(self, *e):
        self.on_tick.once(self.sync_gpu)


    def init(self): 
        self._build_kernel()
        self.program = self._create_program()
        self._init_vao()

        # if no custom length detect the length
        # once on the first tick.
        if self.length is None:
            self.on_tick.once(self.set_range)


    def set_range(self, offset=0, length=None):
        if length is None:
            for dname, _d in self.domains.items():
                if hasattr(_d.domain, 'attrib_pointers'):
                    length = len(_d.domain)
        self.offset = offset
        self.length = length


    def _build_kernel(self):
        context = self.get_domain_glsl_substitutions()
        kernel = Template(self.kernel, context)
        kernel.context.update({
            'size': 'gl_PointSize',
            'color': 'v_col'})
        self._kernel_template = kernel


    def _create_program(self):
        prg = DomainProgram(vrt_file='glprimitives.vrt.glsl', 
                            frg_file='glprimitives.frg.glsl') 

        prg.declare_uniform('camera', components.camera.Camera2D.DTYPE, variable='camera')
        prg.declare_uniform('plot',   plotter2d.Plotter2d.UBO_DTYPE,    variable='plot')

        prg.get_shader(GL_VERTEX_SHADER).substitutions.update({
            'vrt_kernl': self._kernel_template.render()})
        prg.prepare_domains(self.domains)
        prg.link()
        
        prg.uniform_block_binding('plot',   G_.CONTEXT.buffer_base('gpupy.plot.plotter2d'))
        prg.uniform_block_binding('camera', G_.CONTEXT.buffer_base('gpupy.gl.camera'))

        return prg 


    def _init_vao(self):
        self.vao = glGenVertexArrays(1)
        glBindVertexArray(self.vao)
        self._enable_domain_attrib_pointers()
        glBindVertexArray(0)


    def sync_gpu(self):
        self.program.uniform('u_resolution', self.resolution.xy)
        self.program.uniform('u_viewport',   self.viewport.xy)


    def render(self):
        domain.enable_domains(self.program, self.domains.items())

        glEnable(GL_PROGRAM_POINT_SIZE)
        self.program.use()
        glBindVertexArray(self.vao)
        glDrawArrays(self.gl_mode, self.offset, self.length)
        glBindVertexArray(0)
        self.program.unuse()
