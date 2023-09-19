# Vertex shader for lines

vertex_shader_lines = """
# version 330 core

layout(location = 0) in vec3 a_position; 
layout(location = 1) in vec3 a_color;

uniform mat4 model;
uniform mat4 view;
uniform mat4 project;
uniform int color_by;

uniform float clip_x;
uniform float clip_y;
uniform float clip_z;

out vec3 v_color;
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
    
    //gl_Position = project * view * model * vec4(a_position, 1.0);
    v_color = a_color;

    if(color_by == 1)
    {
        v_color = a_color;
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
