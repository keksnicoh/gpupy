#-*- coding: utf-8 -*-

from gpupy.gl.vector import * 

import unittest
from unittest_data_provider import data_provider



class TestVectors(unittest.TestCase):

    def test_listenable_vector(self):
        vec = ListenableVector(Vec2(100, 100))
        
        self.assertEqual(100, vec.x)        
        self.assertEqual(100, vec.y)

        vec.x = 123
        self.assertEqual(123, vec.x)        
        self.assertEqual(100, vec.y)

        vec.y = 124
        self.assertEqual(123, vec.x)        
        self.assertEqual(124, vec.y)

        event_res = {'old': None, 'new': None, 'counter': 0}
        def event_handler(old, new):
            event_res['old'] = old 
            event_res['new'] = new
            event_res['counter'] += 1

        vec.on_change.append(event_handler)

        vec.x = 33
        self.assertEqual(event_res['old'], (123, 124))
        self.assertEqual(event_res['new'], (33, 124))
        self.assertEqual(event_res['counter'], 1)

        vec.xy = (123, 14)
        self.assertEqual(event_res['old'], (33, 124))
        self.assertEqual(event_res['new'], (123, 14))
        self.assertEqual(event_res['counter'], 2)

        self.assertEqual(tuple(vec), (123, 14))

        # test vec3 
        vec3 = ListenableVector(Vec3(100, 100, 100))
        self.assertEqual((100, 100, 100), vec3.xyz)

        event_res = {'old': None, 'new': None, 'counter': 0}

        vec3.on_change.append(event_handler)
        vec3.xyz = (1,2,3)

        self.assertEqual(event_res['old'], (100, 100, 100))
        self.assertEqual(event_res['new'], (1, 2, 3))
        self.assertEqual(event_res['counter'], 1)

