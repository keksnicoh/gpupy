Buffers
=======

the `gpupy.gl.buffer` module provides some numpy friendly api to OpenGl buffers.
```python
from gpupy.gl.buffer import BufferObject 
from OpenGL.GL import GL_UNIFORM_BUFFER

BufferObject.empty(500, (np.float32, 4))
BufferObject.zeros(500, (np.float32, 4))
BufferObject.ones(500, (np.float32, 4))

BufferObject.empty_like(ndarray)
BufferObject.zeros_like(ndarray)
BufferObject.ones_like(ndarray)

# push a numpy ndarray 
BufferObject.to_device(ndarray)

# push a numpy ndarray and use it as an uniform buffer object
buffer = BufferObject.to_device(ndarray, target=GL_UNIFORM_BUFFER)
buffer.bind_buffer_base(0)
```

The buffer can be overwritten by
```python
buffer.set(ndarray)
```

and read by 
```python
ndarray = buffer.set()
```

TODO: partial write / read.

OpenCL interoperatibility 
-------------------------
One can create an `pyopencl.array.Array` from a buffer
```python 
opencl_buf = buffer.get_cl_array()
```
