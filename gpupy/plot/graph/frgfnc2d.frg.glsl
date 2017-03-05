{% version %}

in vec2 frag_pos;
out vec4 frag_color;

{% uniform_block plot %}

${glsl_declr}
${clr_kernel}

void main() {
    // color kernel here
    vec2 x = vec2(frag_pos.x, 1.0-frag_pos.y);
    frag_color = color(${DOMAIN:${MAIN_DOMAIN}}(x));
}
