#-*- coding: utf-8 -*-
"""
some usefull numpy utilities

:author: keksnicoh
"""

import numpy as np 

def cplane(x0=-1, x1=1, i0=-1, i1=1, steps=500):
    """
    creates a complex plane from [x0, x1] x [i0, i1]

    """
    axis_r = np.linspace(x0, x1, steps)
    axis_i = np.linspace(i0, i1, steps)
    r, i = np.meshgrid(axis_r, axis_i)
    return r + i*1j