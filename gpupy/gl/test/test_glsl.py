#-*- coding: utf-8 -*-

import unittest
from unittest_data_provider import data_provider

from gpupy.gl.glsl import render_struct_items_from_dtype, struct_fields_to_dtype

import numpy as np 

class TestGlslUtilities(unittest.TestCase):
    fields_data = lambda: (
        (np.float32,'float a;'),
        (np.int32,'int a;'),
        (np.float64, 'double a;'),
        ((np.float32, 2), 'vec2 a;'),
        ((np.int32, 2),'ivec2 a;'),
        ((np.float64, 2),'dvec2 a;'),
        ((np.float32, 3),'vec3 a;'),
        ((np.int32, 3),'ivec3 a;'),
        ((np.float64, 3),'dvec3 a;'),
        ((np.float32, 4),'vec4 a;'),
        ((np.int32, 4),'ivec4 a;'),
        ((np.float64, 4),'dvec4 a;'),
        ((np.float32, (2, 2)),'mat2 a;'),
        ((np.float64, (2, 2)),'dmat2 a;'),
        ((np.float32, (3, 3)),'mat3 a;'),
        ((np.float64, (3, 3)),'dmat3 a;'),
        ((np.float32, (4, 4)),'mat4 a;'),
        ((np.float64, (4, 4)),'dmat4 a;'),
    )

    @data_provider(fields_data)
    def test_fields(self, field_type, expected_glsl_declr):
        if not isinstance(field_type, tuple):
            dtype = np.dtype([('a', field_type)])
        else:
            dtype = np.dtype([('a', *field_type)])

        self.assertEqual(
            render_struct_items_from_dtype(dtype).strip(), 
            expected_glsl_declr)

    def test_struct_to_dtype(self):
        test_struct = """
            float a;
            float b;
            int i1;
            ivec4 i4;
            vec3 f3;
            mat4 m4;
            dmat4 dm4;
        """

        rendered_dtype = struct_fields_to_dtype(test_struct)
        expected_dtype = np.dtype([
            ('a', np.float32),
            ('b', np.float32),
            ('i1', np.int32),
            ('i4', np.int32, 4),
            ('f3', np.float32, 3),
            ('m4', np.float32, (4, 4)),
            ('dm4', np.float64, (4, 4))
        ])

        self.assertTrue(
            rendered_dtype == expected_dtype
        )

    def test_id(self):
        dtype = np.dtype([
            ('a', np.float32),
            ('b', np.float32),
            ('i1', np.int32),
            ('i4', np.int32, 4),
            ('f3', np.float32, 3),
            ('m4', np.float32, (4, 4)),
            ('dm4', np.float64, (4, 4))
        ])
        self.assertTrue(dtype == struct_fields_to_dtype(render_struct_items_from_dtype(dtype)))


if __name__ == '__main__':
    unittest.main()