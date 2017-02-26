{% version %}
{% uniform_block camera %}
{% uniform_block plot %}

${vrt_declr}
${glsl_header}
out vec4 v_col;

vec4 _cs(vec4 p) { return camera.mat_projection * camera.mat_view * plot.mat_cs * p; }
vec4 cs(float p) { return _cs(vec4(p, 0, 0, 1)); }
vec4 cs(vec2 p)  { return _cs(vec4(p, 0, 1)); }
vec4 cs(vec3 p)  { return _cs(vec4(p,  1)); }
vec4 cs(vec4 p)  { return _cs(p); }

${glsl_declr}
${vrt_kernl}

void main() {
    v_col = vec4(1, 0, 0, 1);
    gl_PointSize = 1;
    gl_Position = cs(kernel());
}