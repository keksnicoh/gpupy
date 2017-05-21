{% version %}
layout(location=0) out vec4 color;
in vec4 v_col;
vec4 fragment_kernel(vec4 color) {
    return color;
}
void main() { 
    color = fragment_kernel(v_col); 
}