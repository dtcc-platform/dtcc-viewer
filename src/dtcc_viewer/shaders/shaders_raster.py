vertex_shader_raster = """
#version 330 core
layout (location = 0) in vec3 a_position;
layout (location = 1) in vec2 a_tex_coords;

uniform mat4 model;
uniform mat4 project;
uniform mat4 view;
uniform float clip_x;
uniform float clip_y;
uniform float clip_z;
uniform float asp_rat;      // Aspect ratio of the raster


out vec3 v_color;
out vec2 tex_coords;

void main()
{
    vec4 clippingPlane1 = vec4(-1, 0, 0, clip_x);
	vec4 clippingPlane2 = vec4(0, -1, 0, clip_y);
	vec4 clippingPlane3 = vec4(0, 0, -1, clip_z);

    vec4 world_pos = model * vec4(a_position, 1.0);
    
    gl_ClipDistance[0] = dot(world_pos, clippingPlane1);
    gl_ClipDistance[1] = dot(world_pos, clippingPlane2);
    gl_ClipDistance[2] = dot(world_pos, clippingPlane3);

    gl_Position = project * view * world_pos;

    v_color = vec3(1.0, 0.0, 1.0);  
    tex_coords = a_tex_coords;
} 
"""


fragment_shader_raster_data = """
#version 330 core

in vec3 v_color;
in vec2 tex_coords;
out vec4 frag_color;

uniform int color_by;
uniform int color_inv;
uniform int cmap_idx;

uniform sampler2D data_texture;
uniform float data_min;
uniform float data_max;

$color_map_0
$color_map_1
$color_map_2
$color_map_3
$color_map_4

void main()
{
    // Sample the data texture at the current texture coordinates
    vec4 value = texture(data_texture, tex_coords);

    // Magenta as default color
    vec3 color = vec3(1.0, 0.0, 1.0); 

    if (color_by == 1) {
    
        if (cmap_idx == 0) {
            color = turbo(value.r);
        } 
        else if (cmap_idx == 1) 
        {
            color = inferno(value.r);
        } 
        else if (cmap_idx == 2) 
        {
            color = black_body(value.r);
        } 
        else if (cmap_idx == 3) 
        {
            color = rainbow(value.r);
        } 
        else if (cmap_idx == 4) 
        {
            color = viridis(value.r);
        }
        if(color_inv == 1)
        {
            color = vec3(1.0) - color;
        }
    }
    else
    {
        color = vec3(1.0, 1.0, 1.0);
    }
    frag_color = vec4(color, 1.0);
}

"""


fragment_shader_raster_rgb = """
#version 330 core

in vec3 v_color;
in vec2 tex_coords;
out vec4 frag_color;

uniform sampler2D data_texture;
uniform int color_inv;
uniform int r_channel;
uniform int g_channel;
uniform int b_channel;

void main()
{
    // Sample the data texture at the current texture coordinates
    vec4 value = texture(data_texture, tex_coords);
    
    float r = 0.0;
    float g = 0.0;
    float b = 0.0;
    float a = 1.0; 

    if(r_channel == 1)
    {
        r = value.r;
    }
    if(g_channel == 1)
    {
        g = value.g;
    }
    if(b_channel == 1)
    {
        b = value.b;
    }
    
    vec3 color = vec3(r, g, b);

    if(color_inv == 1)
    {
        color = vec3(1.0) - color;
    }

    frag_color = vec4(color, a);
}

"""

fragment_shader_raster_rgba = """
#version 330 core

in vec3 v_color;
in vec2 tex_coords;
out vec4 frag_color;

uniform sampler2D data_texture;
uniform int color_inv;
uniform int r_channel;
uniform int g_channel;
uniform int b_channel;


void main()
{
    // Sample the data texture at the current texture coordinates
    vec4 value = texture(data_texture, tex_coords);

    float r = 0.0;
    float g = 0.0;
    float b = 0.0;
    float a = value.a; 

    if(r_channel == 1)
    {
        r = value.r;
    }
    if(g_channel == 1)
    {
        g = value.g;
    }
    if(b_channel == 1)
    {
        b = value.b;
    }
    
    vec3 color = vec3(r, g, b);

    if(color_inv == 1)
    {
        color = vec3(1.0) - color;
    }

    frag_color = vec4(color, a);
}

"""
