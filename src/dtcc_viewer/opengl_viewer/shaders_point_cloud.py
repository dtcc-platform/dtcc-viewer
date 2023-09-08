# Vertex shader for the particles

vertex_shader_pc = """
# version 330 core

layout(location = 0) in vec3 a_position; 
layout(location = 1) in vec3 a_color;
layout(location = 2) in vec3 a_offset;
layout(location = 3) in vec3 a_icolor;

uniform mat4 model;
uniform mat4 project;
uniform mat4 view;
uniform int color_by;
uniform mat4 scale;

uniform float clip_x;
uniform float clip_y;
uniform float clip_z;

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
        v_color = a_icolor * a_color;
    }
    else
    {
        v_color = a_color;
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
