vertex_shader_axes = """
# version 330 core

layout(location = 0) in vec3 a_position; 
layout(location = 1) in vec3 a_color;

uniform mat4 model;
uniform mat4 project;
uniform mat4 view;
uniform float scale;

out vec3 v_color;
void main()
{   
    // Scale when the cs is in the origin position.
    vec4 scale_pos = vec4(a_position * scale, 1.0);

    // Move to world origin
    vec4 world_pos = model * scale_pos;
    
    gl_Position = project * view * world_pos;

    v_color = a_color;
}
"""

# Fragment shader for mesh also works for the mesh edges

fragment_shader_axes = """
# version 330 core
in vec3 v_color;
out vec4 out_color;
void main()
{
    out_color = vec4(v_color, 1.0);
}
"""
