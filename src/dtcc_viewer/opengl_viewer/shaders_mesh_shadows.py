vertex_shader_shadows = """
# version 330 core

layout(location = 0) in vec3 a_position; 
layout(location = 1) in vec3 a_color;
layout(location = 2) in vec3 a_normal;

out vec3 v_frag_pos;
out vec3 v_color;
out vec3 v_normal;
out vec4 v_frag_pos_light_space;

uniform mat4 model;
uniform mat4 view;
uniform mat4 project;
uniform int color_by;
uniform mat4 light_space_matrix;

uniform float clip_x;
uniform float clip_y;
uniform float clip_z;

void main()
{   

    vec4 clippingPlane1 = vec4(-1, 0, 0, clip_x);
	vec4 clippingPlane2 = vec4(0, -1, 0, clip_y);
	vec4 clippingPlane3 = vec4(0, 0, -1, clip_z);
    
    vec4 world_pos = model * vec4(a_position, 1.0);
    
    gl_ClipDistance[0] = dot(world_pos, clippingPlane1);
    gl_ClipDistance[1] = dot(world_pos, clippingPlane2);
    gl_ClipDistance[2] = dot(world_pos, clippingPlane3);

    v_frag_pos = vec3(world_pos);

    //v_frag_pos = vec3(model * vec4(a_position, 1.0));
    v_normal = transpose(inverse(mat3(model))) * a_normal;
    v_frag_pos_light_space = light_space_matrix * vec4(v_frag_pos, 1.0);

    if(color_by == 1)
    {
        v_color = a_color;
    }
    else if(color_by == 2)
    {
        v_color = vec3(1.0, 1.0, 1.0);
    }

    gl_Position = project * view * vec4(v_frag_pos, 1.0);
}
"""

fragment_shader_shadows = """ 
# version 330 core

in vec3 v_frag_pos;
in vec3 v_color;
in vec3 v_normal;
in vec4 v_frag_pos_light_space;

out vec4 out_frag_color;

uniform sampler2D shadow_map;

uniform vec3 light_color;
uniform vec3 light_position;
uniform vec3 view_position;


float shadow_calc(float dot_light_normal)
{
    //transform from [-1, 1] to [0, 1]
    vec3 pos = v_frag_pos_light_space.xyz * 0.5 + 0.5;
    if(pos.z > 1.0)
    {
        pos.z = 1.0;
    }
    //Sample from the shadow map using xy as uv coordinates
    float depth = texture(shadow_map, pos.xy).r;

    //Surfaces with normal perpendicular to the ligth source (i.e. dot_light_normal = 0) gives a larger bias. 
    //Surfaces looking at the light source get a smaller bias of minimum 0.005. 
    float bias = max(0.0011 * (1.0 - dot_light_normal), 0.00005);   
    
    float shadow = 0.0;
    vec2 texel_size = 1.0 / textureSize(shadow_map, 0);

    //PCF for smoother shadow edges
    for(int x = -1; x <= 1; ++x)
    {
        for(int y = -1; y <= 1; ++y)
        {   
            float depth = texture(shadow_map, pos.xy + vec2(x,y) * texel_size).r;
            shadow += (depth + bias) < pos.z ? 0.0 : 1.0;
        }
    }

    return shadow / 9.0;
}

void main()
{   
	float ambient_strength = 0.4;
	vec3 ambient = ambient_strength * light_color;

	vec3 norm = normalize(v_normal);
	vec3 light_dir = normalize(light_position); // - v_frag_pos);

    float dot_light_normal = dot(norm, light_dir);

	float diff = max(dot_light_normal, 0.0);
	vec3 diffuse = diff * light_color;

    float shadow = shadow_calc(dot_light_normal);
    
    vec3 lightning = (shadow * (diffuse) + ambient) * v_color;

    out_frag_color = vec4(lightning, 1.0);

}
"""

vertex_shader_shadow_map = """
#version 330 core
layout (location = 0) in vec3 a_pos;

uniform mat4 light_space_matrix;
uniform mat4 model;

void main()
{
    gl_Position = light_space_matrix * model * vec4(a_pos, 1.0);
} 
"""

fragment_shader_shadow_map = """
#version 330 core

void main()
{             
    // gl_FragDepth = gl_FragCoord.z;
} 
"""

vertex_shader_debug = """
#version 330 core
layout (location = 0) in vec3 a_pos;
layout (location = 1) in vec2 a_tex_coords;

out vec2 tex_coords;

void main()
{
    tex_coords = a_tex_coords;
    gl_Position = vec4(a_pos, 1.0);
} 
"""

fragment_shader_debug = """
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
