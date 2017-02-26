{% version %}
{% uniform_block camera %}
{% uniform_block plot %}

in vec4 vertex;
in vec2 tex;

out vec2 frag_pos;

void main() {
    gl_Position = camera.mat_projection * camera.mat_view * plot.mat_cs * vec4(
        plot.cs.x + plot.cs_size.x * vertex.x, 
        plot.cs.z + plot.cs_size.y * vertex.y, 0, 1);
    frag_pos = vec2(tex.x, 1-tex.y);
}