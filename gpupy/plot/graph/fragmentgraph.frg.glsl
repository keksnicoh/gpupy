{% version %}
in  vec2 frag_pos;
out vec4 frag_color;
{% uniform_block plot %}
${glsl_declr}

vec4 tovec4(float x) { return vec4(x, 0, 0, 1); }
vec4 tovec4(vec2 x) { return vec4(x.x, x.y, 0, 1); }
vec4 tovec4(vec3 x) { return vec4(x.x, x.y, x.z, 1); }
vec4 tovec4(vec4 x) { return x; }
${fragment_kernel}
void main() 
{
    // color kernel here
    vec2 x = vec2(frag_pos.x, 1.0-frag_pos.y);
    frag_color = fragment_kernel(x);
}
