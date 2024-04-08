# Vertex shader for lines

vertex_shader_grid = """
# version 330 core

layout(location = 0) in vec3 a_position; 

uniform mat4 model;
uniform mat4 view;
uniform mat4 project;

uniform float scale;
uniform vec3 color;

out vec3 v_color;
void main()
{    
    
    vec4 world_pos = model * vec4(a_position * scale, 1.0);
    gl_Position = project * view * world_pos;    
    v_color = color;
}
"""

# Fragment shader for lines

fragment_shader_grid = """
# version 330 core
in vec3 v_color;
out vec4 out_color;
void main()
{
    out_color = vec4(v_color, 1.0);
}
"""

vertex_shader_axes = """
# version 330 core

layout(location = 0) in vec3 a_position;
layout(location = 1) in vec3 a_color; 

uniform mat4 model;
uniform mat4 view;
uniform mat4 project;

out vec3 v_color;
void main()
{
    vec4 world_pos = model * vec4(a_position, 1.0);
    gl_Position = project * view * world_pos;
    v_color = a_color;
}
"""

fragment_shader_axes = """
# version 330 core
in vec3 v_color;
out vec4 out_color;
void main()
{
    out_color = vec4(v_color, 1.0);
}
"""
