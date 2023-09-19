# Vertex shader for mesh also works for the mesh edges

vertex_shader_ambient = """
# version 330 core

layout(location = 0) in vec3 a_position; 
layout(location = 1) in vec3 a_color;
layout(location = 2) in vec3 a_normal;

uniform mat4 model;
uniform mat4 project;
uniform mat4 view;
uniform int color_by;
uniform float clip_x;
uniform float clip_y;
uniform float clip_z;

out vec4 v_color;
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

    //gl_Position = project * view * vec4(a_position, 1.0);
    
    if(color_by == 1)
    {
        v_color = vec4(a_color, 1.0);
    }
    else if(color_by == 2)
    {
        v_color = vec4(1.0, 1.0, 1.0, 1.0);   
    }
}
"""

# Fragment shader for mesh also works for the mesh edges

fragment_shader_ambient = """
# version 330 core
in vec4 v_color;
out vec4 out_color;
void main()
{
    out_color = v_color;
}
"""
