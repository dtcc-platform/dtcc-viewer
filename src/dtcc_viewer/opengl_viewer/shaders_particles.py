
# Vertex shader for the particles

vertex_shader_particle = """
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

out vec3 v_color;
void main()
{   

    vec4 final_pos = (model * scale * vec4(a_position, 1.0)) + vec4(a_offset, 0.0);
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

fragment_shader_particle = """
# version 330 core
in vec3 v_color;
out vec4 out_color;
void main()
{
    out_color = vec4(v_color, 1.0);
}
"""
