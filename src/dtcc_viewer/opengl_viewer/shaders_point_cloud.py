# Vertex shader for the particles

vertex_shader_pc = """
# version 330 core

layout(location = 0) in vec3 a_position; 
layout(location = 1) in vec3 a_base_color;      //White in center, grey at border
layout(location = 2) in vec3 a_offset;
layout(location = 3) in vec3 a_idata;           //Data per instance

uniform mat4 model;
uniform mat4 project;
uniform mat4 view;
uniform int color_by;
uniform mat4 scale;
uniform int invert_color;

uniform float clip_x;
uniform float clip_y;
uniform float clip_z;

uniform float data_min; 
uniform float data_max;
uniform int cmap_idx;
uniform int data_idx;

$color_map_0
$color_map_1
$color_map_2
$color_map_3
$color_map_4

out vec3 v_color;
void main()
{   
    vec4 clippingPlane1 = vec4(-1, 0, 0, clip_x);
	vec4 clippingPlane2 = vec4(0, -1, 0, clip_y);
	vec4 clippingPlane3 = vec4(0, 0, -1, clip_z);
    
    //vec4 world_pos = model * vec4(a_position, 1.0);
    
    vec4 final_pos = (model * scale * vec4(a_position, 1.0)) + vec4(a_offset, 0.0);
    
    gl_ClipDistance[0] = dot(final_pos, clippingPlane1);
    gl_ClipDistance[1] = dot(final_pos, clippingPlane2);
    gl_ClipDistance[2] = dot(final_pos, clippingPlane3);

    gl_Position = project * view * final_pos;


    if(color_by == 1)
    {   
        // Calculate the colors using the shader colormaps

        vec3 color_per_instance = vec3(1,0,1);

        if(cmap_idx == 0)
        {
            color_per_instance = rainbow(a_idata[data_idx]);
        }
        else if(cmap_idx == 1)
        {
            color_per_instance = inferno(a_idata[data_idx]);
        }
        else if(cmap_idx == 2)
        {
            color_per_instance = black_body(a_idata[data_idx]);
        }
        else if(cmap_idx == 3)
        {
            color_per_instance = turbo(a_idata[data_idx]);
        }
        else if(cmap_idx == 4)
        {
            color_per_instance = viridis(a_idata[data_idx]);
        }

        if(invert_color == 1)
        {
            color_per_instance = vec3(1.0) - color_per_instance;
        }

        v_color = color_per_instance * a_base_color;
    }
    else
    {
        v_color = a_base_color;
    }

}
"""

# Fragement shader for the particles

fragment_shader_pc = """
# version 330 core
in vec3 v_color;
out vec4 out_color;
void main()
{
    out_color = vec4(v_color, 1.0);
}
"""
