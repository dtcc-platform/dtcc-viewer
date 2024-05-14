# Vertex shader for lines

vertex_shader_lines = """
# version 330 core

layout(location = 0) in vec3 a_position; 
layout(location = 1) in vec2 a_texel;
layout(location = 2) in float a_id;

uniform mat4 model;
uniform mat4 view;
uniform mat4 project;
uniform int color_by;
uniform int color_inv;

uniform float clip_x;
uniform float clip_y;
uniform float clip_z;

uniform float data_min; 
uniform float data_max;
uniform int cmap_idx;
uniform int data_idx;

uniform sampler2D data_tex;

$color_map_0
$color_map_1
$color_map_2
$color_map_3
$color_map_4

out vec3 v_color;
void main()
{
    ivec2 texel_coords = ivec2(a_texel);
    vec4 data_from_texture = texelFetch(data_tex, texel_coords, 0);
    float data = data_from_texture.r;

    vec4 clippingPlane1 = vec4(-1, 0, 0, clip_x);
	vec4 clippingPlane2 = vec4(0, -1, 0, clip_y);
	vec4 clippingPlane3 = vec4(0, 0, -1, clip_z);
    
    vec4 world_pos = model * vec4(a_position, 1.0);
    
    gl_ClipDistance[0] = dot(world_pos, clippingPlane1);
    gl_ClipDistance[1] = dot(world_pos, clippingPlane2);
    gl_ClipDistance[2] = dot(world_pos, clippingPlane3);

    gl_Position = project * view * world_pos;
    
    if(color_by == 1)
    {
        //v_color = a_color;
        
        // Calculate the colors using the shader colormaps
        if(cmap_idx == 0)
        {
            v_color = turbo(data);
        }
        else if(cmap_idx == 1)
        {
            v_color = inferno(data);
        }
        else if(cmap_idx == 2)
        {
            v_color = black_body(data);
        }
        else if(cmap_idx == 3)
        {
            v_color = rainbow(data);
        }
        else if(cmap_idx == 4)
        {
            v_color = viridis(data);
        }

        if(color_inv == 1)
        {
            v_color = vec3(1.0) - v_color;
        }
    }
    else if(color_by == 0)
    {
        v_color = vec3(1.0, 1.0, 1.0);
    }
}
"""

# Fragment shader for lines

fragment_shader_lines = """
# version 330 core
in vec3 v_color;
out vec4 out_color;
void main()
{
    out_color = vec4(v_color, 1.0);
}
"""
