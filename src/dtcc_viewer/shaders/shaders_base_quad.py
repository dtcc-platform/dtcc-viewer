vertex_shader_base_quad = """
#version 330 core

layout (location = 0) in vec3 a_position;
layout (location = 1) in vec2 aTexCoords;

uniform mat4 model;
uniform mat4 view;
uniform mat4 project;

out vec3 v_color;

void main()
{
    vec4 world_pos = model * vec4(a_position, 1.0);
    gl_Position = project * view * world_pos;
    v_color = vec3(1,0,1);
}
"""

fragment_shader_base_quad = """ 
#version 330 core

out vec4 FragColor;
in vec3 v_color;

void main()
{ 
    FragColor = vec4(v_color, 1.0);
}
"""
