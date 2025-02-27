# Vertex shader for lines

vertex_shader_grid = """
# version 330 core

layout(location = 0) in vec3 a_position; 

uniform mat4 model;
uniform mat4 view;
uniform mat4 project;
uniform vec3 color;
uniform float scale;
uniform float clip_xy;

out vec3 v_color;
out vec3 frag_position;

void main()
{    
    vec4 world_pos = model * vec4(a_position[0] * scale, a_position[1] * scale, a_position[2], 1.0);
    
    float xdir = 1.0;
    float ydir = 1.0;
    
    vec4 clippingPlane1 = vec4(1.0, 0, 0, clip_xy);
	vec4 clippingPlane2 = vec4(0, 1.0, 0, clip_xy);    
    vec4 clippingPlane3 = vec4(-1.0, 0, 0, clip_xy);
    vec4 clippingPlane4 = vec4(0, -1.0, 0, clip_xy);    
    
    gl_ClipDistance[3] = dot(world_pos, clippingPlane1);
    gl_ClipDistance[4] = dot(world_pos, clippingPlane2);
    gl_ClipDistance[5] = dot(world_pos, clippingPlane3);
    gl_ClipDistance[6] = dot(world_pos, clippingPlane4);

    frag_position = vec3(world_pos[0], world_pos[1], world_pos[2]);

    gl_Position = project * view * world_pos;    
    v_color = color;
}
"""

# Fragment shader for lines

fragment_shader_grid = """
# version 330 core
in vec3 v_color;
in vec3 frag_position;
out vec4 out_color;

uniform float fog_start;
uniform float fog_end;
uniform vec3 fog_color;

void main()
{   
    float distance = length(frag_position); // Distance from the fragment to the origin
    float fog_factor = (distance - fog_start) / (fog_end - fog_start); // Calculate fog factor
    fog_factor = clamp(fog_factor, 0.0, 1.0);

    vec4 finalColor = mix(vec4(v_color, 1.0), vec4(fog_color, 1.0), fog_factor); // Interpolate between fragment color and fog color

    out_color = finalColor;
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
