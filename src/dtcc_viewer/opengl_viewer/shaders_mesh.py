
# Vertex shader for mesh also works for the mesh edges

vertex_shader_triangels = """
# version 330 core

layout(location = 0) in vec3 a_position; 
layout(location = 1) in vec3 a_color;
layout(location = 2) in vec3 a_normal;

uniform mat4 model;
uniform mat4 project;
uniform mat4 view;
uniform int color_by;

out vec4 v_color;
void main()
{
    gl_Position = project * view * vec4(a_position, 1.0);
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

fragment_shader_triangels = """
# version 330 core
in vec4 v_color;
out vec4 out_color;
void main()
{
    out_color = v_color;
}
"""


# Vertex shader for mesh also works for the mesh edges

vertex_shader_lines = """
# version 330 core

layout(location = 0) in vec3 a_position; 
layout(location = 1) in vec3 a_color;

uniform mat4 model;
uniform mat4 project;
uniform mat4 view;
uniform int color_by;

out vec3 v_color;
void main()
{
    gl_Position = project * view * vec4(a_position, 1.0);
    v_color = a_color;

    if(color_by == 1)
    {
        v_color = a_color;
    }
    else if(color_by == 2)
    {
        v_color = vec3(1.0, 1.0, 1.0);
    }
}
"""

# Fragment shader for mesh also works for the mesh edges

fragment_shader_lines = """
# version 330 core
in vec3 v_color;
out vec4 out_color;
void main()
{
    out_color = vec4(v_color, 1.0);
}
"""


