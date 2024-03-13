vertex_shader_picking = """
# version 330 core

// Input vertex data, different for all executions of this shader.
layout(location = 0) in vec3 a_position; 
layout(location = 1) in vec2 a_texel;
layout(location = 2) in vec3 a_normal;
layout(location = 3) in float a_id;

// Values that stay constant for the whole mesh.
uniform mat4 model;
uniform mat4 view;
uniform mat4 project;

out vec3 v_color;

//Convert id to color
vec3 id_to_color(int id) {
    float r = float((id & 0x000000FF) >> 0) / 255.0;
    float g = float((id & 0x0000FF00) >> 8) / 255.0;
    float b = float((id & 0x00FF0000) >> 16) / 255.0;
    return vec3(r, g, b);
}

void main()
{
    // Output position of the vertex, in clip space : MVP * position
    gl_Position = project * view * model * vec4(a_position, 1.0);
    highp int id_int = int(a_id);
    v_color = id_to_color(id_int);
}
"""

fragment_shader_picking = """ 
# version 330 core

// Input from vertex shader
in vec3 v_color;

// Ouput data
out vec4 color;

void main()
{
    color =  vec4(v_color, 1.0);
}
"""
