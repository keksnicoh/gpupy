{% version %}

in vec2 frag_pos;
out vec4 frag_color;

{% uniform_block plot %}
uniform vec2 u_x_space;

${glsl_header}
${glsl_declr}
${clr_kernel}

void main() {
    // frg x coord
    float x = -u_x_space.x + (frag_pos.x * plot.cs_size.x + plot.cs.x);

    if (x > 1 || x < 0) {
        // signal is not periodic
    //    discard;
    }

    // frg y coord
    float y = frag_pos.y * plot.cs_size.y + plot.cs.z;

    // function value at x
    float ty = ${DOMAIN:${MAIN_DOMAIN}}(x);

    // signed distance from the graph y-value to x-axis.
    // positive if outside otherwise negative.
    float sd = abs(y) - sign(y) * ty;
    
    // relative signed distance. 
    // from x-axis to y-value: [-1,0]
    float xsd = sd / ty * sign(ty);

    // color kernel here
    frag_color = color(vec2(x, y), sd, xsd);
   //frag_color = vec4(1, 0,0,1);
}
