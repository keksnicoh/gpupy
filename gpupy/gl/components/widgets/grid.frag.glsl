{% version %}
{% uniform_block camera %}
const float M_PI = 3.14159265358979323846;
const float M_SQRT2 = 1.41421356237309504880;

uniform float u_antialias;
uniform vec4 u_limits1;
uniform vec4 u_limits2;
uniform vec2 u_major_grid_step;
uniform vec2  u_minor_grid_step;
uniform float u_major_grid_width;
uniform float u_minor_grid_width;
uniform vec4 u_major_grid_color;
uniform vec4 u_minor_grid_color;
uniform mat4 mat_model;
uniform vec2 iResolution;
uniform vec4 c_bg;
in vec2 v_texcoord;
out vec4 f_out;

vec2 transform_forward(vec2 P) { 
    return P;
}
vec2 transform_inverse(vec2 P) {
    return P;
}

// [-0.5,-0.5]x[0.5,0.5] -> [xmin,xmax]x[ymin,ymax]
// limits = xmin,xmax,ymin,ymax
// ------------------------------------------------
vec2 scale_forward(vec2 P, vec4 limits)
{
    P += vec2(.5,.5);
    P *= vec2(limits[1] - limits[0], limits[3] - limits[2]);
    P += vec2(limits[0], limits[2]);
    return P;
}

// [xmin,xmax]x[ymin,ymax] -> [-0.5,-0.5]x[0.5,0.5]
// limits = xmin,xmax,ymin,ymax
// ------------------------------------------------
vec2 scale_inverse(vec2 P, vec4 limits)
{
    P -= vec2(limits[0], limits[2]);
    P /= vec2(limits[1] - limits[0], limits[3] - limits[2]);
    return P - vec2(.5,.5);
}

// Antialias stroke alpha coeff
float stroke_alpha(float distance, float linewidth, float antialias)
{
    float t = linewidth/2.0 - antialias;
    float signed_distance = distance;
    float border_distance = abs(signed_distance) - t;
    float alpha = border_distance/antialias;
    alpha = exp(-alpha*alpha);
    if( border_distance > (linewidth/2.0 + antialias) )
        return 0.0;
    else if( border_distance < 0.0 )
        return 1.0;
    else
        return alpha;
}

// Compute the nearest tick from a (normalized) t value
float get_tick(float t, float vmin, float vmax, float step)
{
    float first_tick = floor((vmin + step/2.0)/step) * step;
    float last_tick = floor((vmax + step/2.0)/step) * step;
    float tick = vmin + t*(vmax-vmin);
    if (tick < (vmin + (first_tick-vmin)/2.0))
        return vmin;
    if (tick > (last_tick + (vmax-last_tick)/2.0))
        return vmax;
    tick += step/2.0;
    tick = floor(tick/step)*step;
    return min(max(vmin,tick),vmax);
}

// Screen distance (pixels) between A and B
float screen_distance(vec4 A, vec4 B)
{

    vec4 pA = camera.mat_projection* camera.mat_view* mat_model *A;
    pA /= pA.w;
    pA.xy = pA.xy * iResolution/2.0;

    vec4 pB = camera.mat_projection* camera.mat_view* mat_model *B;
    pB /= pB.w;
    pB.xy = pB.xy * iResolution/2.0;

    return length(pA.xy - pB.xy);
}

// Screen distance (pixels) between A and B
// (and A screen position is known)
float screen_distance(vec2 A, vec4 B)
{
    vec4 pB = camera.mat_projection* camera.mat_view* mat_model*B;
    pB /= pB.w;
    pB.xy = pB.xy * iResolution/2.0;

    return length(A.xy - pB.xy);
}

void main()
{
    vec2 NP1 = v_texcoord;
    vec2 P1 = scale_forward(NP1, u_limits1);
    vec2 P2 = transform_inverse(P1);

    // Test if we are within limits but we do not discard yet because we want
    // to draw border. Discarding would mean half of the exterior not drawn.
    bvec2 outside = bvec2(false);
    if( P2.x < u_limits2[0] ) outside.x = true;
    if( P2.x > u_limits2[1] ) outside.x = true;
    if( P2.y < u_limits2[2] ) outside.y = true;
    if( P2.y > u_limits2[3] ) outside.y = true;

    vec2 NP2 = scale_inverse(P2,u_limits2);

    vec2 P;
    float tick;

    vec4 pNP1 = camera.mat_projection* camera.mat_view* mat_model*vec4(NP1,0,1);
    pNP1 /= pNP1.w;
    pNP1.xy = pNP1.xy * iResolution/2.0;

    tick = get_tick(NP2.x+0.5, u_limits2[0], u_limits2[1], u_major_grid_step[0]);
    P = transform_forward(vec2(tick,P2.y));
    P = scale_inverse(P, u_limits1);
    float Mx = screen_distance(pNP1.xy, vec4(P,0,1));

    tick = get_tick(NP2.x+0.5, u_limits2[0], u_limits2[1], u_minor_grid_step[0]);
    P = transform_forward(vec2(tick,P2.y));
    P = scale_inverse(P, u_limits1);
    float mx = screen_distance(pNP1.xy, vec4(P,0,1));

    tick = get_tick(NP2.y+0.5, u_limits2[2], u_limits2[3], u_major_grid_step[1]);
    P = transform_forward(vec2(P2.x,tick));
    P = scale_inverse(P, u_limits1);
    float My = screen_distance(pNP1.xy, vec4(P,0,1));

    tick = get_tick(NP2.y+0.5, u_limits2[2], u_limits2[3], u_minor_grid_step[1]);
    P = transform_forward(vec2(P2.x,tick));
    P = scale_inverse(P, u_limits1);
    float my = screen_distance(pNP1.xy, vec4(P,0,1));

    float M = min(Mx,My);
    float m = min(mx,my);

    // Here we take care of "finishing" the border lines
    if(outside.x && outside.y) {
        if (Mx > 0.5*(u_major_grid_width + u_antialias)) {
            discard;
        } else if (My > 0.5*(u_major_grid_width + u_antialias)) {
            discard;
        } else {
            M = max(Mx,My);
        }
    } 
    else if(outside.x) {
        if (Mx > 0.5*(u_major_grid_width + u_antialias)) {
            discard;
        } else {
            M = m = Mx;
        }
    } 
    else if(outside.y) {
        if (My > 0.5*(u_major_grid_width + u_antialias)) {
            discard;
        } else {
            M = m = My;
        }
    }

    // Mix major/minor colors to get dominant color
    vec4 color = u_major_grid_color;
    float alpha1 = stroke_alpha( M, u_major_grid_width, u_antialias);
    float alpha2 = stroke_alpha( m, u_minor_grid_width, u_antialias);
    float alpha  = alpha1;
    if( alpha2 > alpha1*1.5 )
    {
        alpha = alpha2;
        color = u_minor_grid_color;
    }

    // final mixing
    if( outside.x || outside.y ) {
        f_out = vec4(color.rgb, color.a*alpha);
    } else {
        vec4 texcolor = c_bg;
        f_out = mix(texcolor, color, color.a*alpha);
    }
}
