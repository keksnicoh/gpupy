#-*- coding: utf-8 -*-

from gpupy.gl.common.vector import * 

import unittest
from unittest_data_provider import data_provider



class TestVectors(unittest.TestCase):

    def test_vector_basics(self):
        vec = vec3((1,2,3))

        self.assertListEqual([1,2,3], list(vec.xyz))
        self.assertListEqual([1,2,3], list(vec.values))
        self.assertEqual((1,2,3), vec) # test __eq__ impl
        self.assertNotEqual((2,2,3), vec) # test __neq__ impl

        self.assertEqual(1, vec.x)
        self.assertEqual(2, vec.y)
        self.assertEqual(3, vec.z)

        vec.x = 12
        vec.z = 14
        self.assertEqual((12,2,14), vec)
    
    def test_vec4(self):
        c = (1,2,3,4)
        vec = vec4(c)
        self.assertEqual(c, vec)
        self.assertListEqual(list(c), list(vec.xyzw))
        self.assertEqual(c[0], vec.x)
        self.assertEqual(c[1], vec.y)
        self.assertEqual(c[2], vec.z)
        self.assertEqual(c[3], vec.w)

    def test_vec3(self):
        c = (1,2,3)
        vec = vec3(c)
        self.assertEqual(c, vec)
        self.assertListEqual(list(c), list(vec.xyz))
        self.assertEqual(c[0], vec.x)
        self.assertEqual(c[1], vec.y)
        self.assertEqual(c[2], vec.z)

    def test_vec2(self):
        c = (1,2)
        vec = vec2(c)
        self.assertEqual(c, vec)
        self.assertListEqual(list(c), list(vec.xy))
        self.assertEqual(c[0], vec.x)
        self.assertEqual(c[1], vec.y)

    def test_transformation(self):
        # non linear self depending transformation
        t = lambda v: (2*v[0], 3*v[1]*v[0], 4*v[2]*v[0])
        vec = vec3((0, 0, 0))
        vec.transformation = t

        vec.xyz = (1, 2, 3)
        self.assertEqual((2,6,12), vec)

        vec.x = 4
        self.assertEqual((8, 3*6*4, 4*4*12), vec)

        vec.y = 4
        self.assertEqual((2*8, 4*3*8, 4*8*4*4*12), vec)

        vec.z = 2
        self.assertEqual((2*2*8, 3*2*8*4*3*8, 4*2*2*8), vec)

    def test_on_change(self):
        pass


