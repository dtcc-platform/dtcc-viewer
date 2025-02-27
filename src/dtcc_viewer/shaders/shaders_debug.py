vertex_shader_debug_shadows = """
#version 330 core
layout (location = 0) in vec2 a_pos;
layout (location = 1) in vec2 a_tex_coords;

out vec2 tex_coords;

void main()
{
    tex_coords = a_tex_coords;
    gl_Position = vec4(a_pos, 0.0, 1.0);
} 
"""

fragment_shader_debug_shadows = """
#version 330 core

out vec4 frag_color;
in vec2 tex_coords;

uniform sampler2D depth_map;

void main()
{   
    float depth_value = texture(depth_map, tex_coords).r;          
    frag_color = vec4(vec3(depth_value), 1.0); 
} 
"""

vertex_shader_debug_picking = """
#version 330 core

layout (location = 0) in vec2 aPos;
layout (location = 1) in vec2 aTexCoords;

out vec2 TexCoords;

void main()
{
    gl_Position = vec4(aPos.x, aPos.y, 0.0, 1.0); 
    TexCoords = aTexCoords;
}
"""

fragment_shader_debug_picking = """ 
#version 330 core
out vec4 FragColor;
  
in vec2 TexCoords;

uniform sampler2D screenTex;

void main()
{ 
    FragColor = texture(screenTex, TexCoords);
}
"""
