{% version %}

in vec2 frag_pos;
out vec4 frag_color;

{% uniform_block plot %}
uniform vec2 u_x_space;
uniform vec4 cs;
uniform vec2 cs_size;

${glsl_declr}
${clr_kernel}

void main() {

    // frg x coord
    float x = -u_x_space.x + (frag_pos.x * cs_size.x + cs.x);

    if (x > 1 || x < 0) {
        // signal is not periodic
    //    discard;
    }

    // frg y coord
    float y = frag_pos.y * cs_size.y + cs.z;

    // function value at x
    float ty = ${domain.${MAIN_DOMAIN}}(x);

    // signed distance from the graph y-value to x-axis.
    // positive if outside otherwise negative.
    float sd = abs(y) - sign(y) * ty;
    
    // relative signed distance. 
    // from x-axis to y-value: [-1,0]
    float xsd = sd;// / ty * sign(ty) : 0;

    // color kernel here
    frag_color = color(vec2(x, y), sd, xsd);
   
}
