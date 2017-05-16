{% version %}
layout(location=0) out vec4 color;
layout(location=1) out vec4 rs_clr;
in vec4 v_col;
void main() { 
    color = v_col; 
    rs_clr = vec4(1,1,1,1); 
}