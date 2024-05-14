vertex_shader_diffuse = """
# version 330 core

layout(location = 0) in vec3 a_position; 
layout(location = 1) in vec2 a_texel;
layout(location = 2) in vec3 a_normal;
layout(location = 3) in float a_id;

uniform mat4 model;
uniform mat4 view;
uniform mat4 project;
uniform int color_by;
uniform int color_inv;
uniform float clip_x;
uniform float clip_y;
uniform float clip_z;

uniform float data_min; 
uniform float data_max;
uniform int cmap_idx;
uniform int data_idx;
uniform int picked_id;

uniform sampler2D data_tex;

out vec3 v_frag_pos;
out vec3 v_color;
out vec3 v_normal;

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

    gl_Position = project * view * world_pos;

    v_frag_pos = vec3(model * vec4(a_position, 1.0));
    v_normal = a_normal;

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


}
"""

fragment_shader_diffuse = """ 
# version 330 core

in vec3 v_frag_pos;
in vec3 v_color;
in vec3 v_normal;

uniform vec3 light_color;
uniform vec3 light_pos;
uniform vec3 view_pos;

out vec4 out_frag_color;

void main()
{
	float ambient_strength = 0.5;
	vec3 ambient = ambient_strength * light_color;

	vec3 norm = normalize(v_normal);
	vec3 light_dir = normalize(light_pos); // - v_frag_pos);

	float diff = max(dot(norm, light_dir), 0.0);
	vec3 diffuse = diff * light_color;

	//float specular_strength = 0.7;
	//vec3 view_dir = normalize(view_pos - v_frag_pos);
	//vec3 reflect_dir = reflect(-light_dir, norm);

	//float spec = pow(max(dot(view_dir, reflect_dir), 0.0), 16);
	//vec3 specular = specular_strength * spec * light_color;

	//vec3 result = (ambient + diffuse + specular) * vec3(v_color); // objectColor;
	
    vec3 result = (ambient + diffuse) * vec3(v_color); // objectColor;
	out_frag_color = vec4(result, 1.0);
}
"""
