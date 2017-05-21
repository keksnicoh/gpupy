#-*- coding: utf-8 -*-
"""
matrix utilities..

:author: Nicolas 'keksnicoh' Heimann
"""
from gpupy.gl.common.vector import *
import numpy as np



def mat4_rot_x(angle):
    """ creates 4x4 rotation matrix around x axis """
    return np.array([
        1, 0, 0, 0,
        0, np.cos(angle), -np.sin(angle), 0,
        0, np.sin(angle), np.cos(angle), 0,
        0, 0, 0, 1
    ], np.float32).reshape((4, 4)).T

def mat4_rot_y(angle):
    """ creates 4x4 rotation matrix around y axis """
    return np.array([
        np.cos(angle), 0, np.sin(angle), 0,
        0, 1, 0, 0,
        - np.sin(angle), 0, np.cos(angle), 0,
        0, 0, 0, 1
    ], np.float32).reshape((4, 4)).T

def mat4_rot_z(angle):
    """ creates 4x4 rotation matrix around y axis """
    return np.array([
        np.cos(angle), -np.sin(angle), 0, 0,
        np.sin(angle), np.cos(angle), 0, 0,
        0, 0, 1, 0,
        0, 0, 0, 1,
    ], np.float32).reshape((4, 4)).T

def mat4_translation(x=0, y=0, z=0):
    return np.array([
        1, 0, 0, -x,
        0, 1, 0, -y,
        0, 0, 1, z,
        0, 0, 0, 1,
    ], np.float32).reshape((4, 4))

def mat4_reflection_xy():
    return np.array([
        1, 0, 0, 0,
        0, 1, 0, 0,
        0, 0, -1, 0,
        0, 0, 0, 1,
    ], np.float32).reshape((4, 4))

def MatModel2d():
    def __init__(self, position=(0, 0), scaling=(0, 0), rotation=0):
        self.position = vec2(position)
        self.scaling = vec2(scaling)
        self.rotation = vec2(rotation)

        self.has_changes = changes

