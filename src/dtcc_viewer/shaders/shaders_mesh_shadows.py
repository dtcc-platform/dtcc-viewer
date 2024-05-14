vertex_shader_shadows = """
# version 330 core

layout(location = 0) in vec3 a_position; 
layout(location = 1) in vec2 a_texel;
layout(location = 2) in vec3 a_normal;
layout(location = 3) in float a_id;

out vec3 v_frag_pos;
out vec3 v_color;
out vec3 v_normal;
out vec4 v_frag_pos_light_space;

uniform mat4 model;
uniform mat4 view;
uniform mat4 project;
uniform int color_by;
uniform int color_inv;
uniform mat4 lsm;       // light space matrix

uniform float data_min; 
uniform float data_max;
uniform int cmap_idx;
uniform int data_idx;
uniform int picked_id;

uniform float clip_x;
uniform float clip_y;
uniform float clip_z;

uniform sampler2D data_tex;

$color_map_0
$color_map_1
$color_map_2
$color_map_3
$color_map_4

void main()
{   
    ivec2 texel_coords = ivec2(a_texel);
    vec4 data_from_texture = texelFetch(data_tex, texel_coords, 0);
    float data = data_from_texture.r;    

    vec4 clippingPlane1 = vec4(-1, 0, 0, clip_x);
	vec4 clippingPlane2 = vec4(0, -1, 0, clip_y);
	vec4 clippingPlane3 = vec4(0, 0, -1, clip_z);
    
    vec4 world_pos = model * vec4(a_position, 1.0);
    
    gl_ClipDistance[0] = dot(world_pos, clippingPlane1);
    gl_ClipDistance[1] = dot(world_pos, clippingPlane2);
    gl_ClipDistance[2] = dot(world_pos, clippingPlane3);

    v_frag_pos = vec3(world_pos);

    v_normal = transpose(inverse(mat3(model))) * a_normal;
    v_frag_pos_light_space = lsm * vec4(v_frag_pos, 1.0);

    highp int id_int = int(a_id);
    if(picked_id == id_int)
    {
        v_color = vec3(1.0, 0.0, 1.0);
    }
    else if(color_by == 1)
    {
        // Calculate the colors using the shader colormaps
        if(cmap_idx == 0)
        {
            v_color = turbo(data);
        }
        else if(cmap_idx == 1)
        {
            v_color = inferno(data);
        }
        else if(cmap_idx == 2)
        {
            v_color = black_body(data);
        }
        else if(cmap_idx == 3)
        {
            v_color = rainbow(data);
        }
        else if(cmap_idx == 4)
        {
            v_color = viridis(data);
        }

        if(color_inv == 1)
        {
            v_color = vec3(1.0) - v_color;
        }
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
uniform vec3 light_pos;
uniform vec3 view_pos;


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
	vec3 light_dir = normalize(light_pos); // - v_frag_pos);

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

uniform mat4 lsm; // light space matrix
uniform mat4 model;

void main()
{
    gl_Position = lsm * model * vec4(a_pos, 1.0);
} 
"""

fragment_shader_shadow_map = """
#version 330 core

void main()
{             
    // gl_FragDepth = gl_FragCoord.z;
} 
"""
