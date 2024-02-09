vertex_shader_picking = """
# version 330 core

// Input vertex data, different for all executions of this shader.
layout(location = 0) in vec3 a_position;

// Values that stay constant for the whole mesh.
uniform mat4 model;
uniform mat4 view;
uniform mat4 project;

void main()
{
    // Output position of the vertex, in clip space : MVP * position
    gl_Position = project * view * model * vec4(a_position, 1.0);
}
"""

fragment_shader_picking = """ 
# version 330 core

// Ouput data
out vec4 color;

// Values that stay constant for the whole mesh.
uniform vec4 picking_color;

void main()
{
    color = picking_color;
}
"""
