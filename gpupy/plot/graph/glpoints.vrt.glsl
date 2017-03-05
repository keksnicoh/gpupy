{% version %}
{% uniform_block camera %}
{% uniform_block plot %}

uniform vec2 u_resolution;
uniform vec2 u_viewport;
uniform vec4 u_col = vec4(1, 0, 0, 1);

${glsl_attr}
${glsl_declr}
out vec4 v_col;

vec4 _cs(vec4 p) { return camera.mat_projection * camera.mat_view * plot.mat_cs * p; }
vec4 cs(float p) { return _cs(vec4(p, 0, 0, 1)); }
vec4 cs(vec2 p)  { return _cs(vec4(p, 0, 1)); }
vec4 cs(vec3 p)  { return _cs(vec4(p,  1)); }
vec4 cs(vec4 p)  { return _cs(p); }

float cartesian_x(float x) { return plot.cs.x + plot.cs_size.x * x; }
float cartesian_x(vec2 x) { return cartesian_x(x.x); }

${vrt_kernl}

void main() {
    v_col = u_col;
    gl_PointSize = 1;
    gl_Position = cs(kernel());

    // adjust pointsize to resolution
    float f = u_resolution.x/u_viewport.x;
    if (gl_PointSize*f > 1) {
        gl_PointSize *= f;
    }
}