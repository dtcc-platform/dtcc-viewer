
vertex_shader_fancy = """
# version 330 core

layout(location = 0) in vec3 a_position; 
layout(location = 1) in vec3 a_color;
layout(location = 2) in vec3 a_normal;

uniform mat4 model;
uniform mat4 view;
uniform mat4 project;
uniform int color_by;

out vec3 v_frag_pos;
out vec3 v_color;
out vec3 v_normal;

void main()
{
    gl_Position = project * view * model * vec4(a_position, 1.0);
    v_frag_pos = vec3(model * vec4(a_position, 1.0));
    v_normal = a_normal;

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

fragment_shader_fancy = """ 
# version 330 core

in vec3 v_frag_pos;
in vec3 v_color;
in vec3 v_normal;

uniform vec3 object_color;
uniform vec3 light_color;
uniform vec3 light_position;
uniform vec3 view_position;

out vec4 out_frag_color;

void main()
{
	float ambient_strength = 0.3;
	vec3 ambient = ambient_strength * light_color;

	vec3 norm = normalize(v_normal);
	vec3 light_dir = normalize(light_position); // - v_frag_pos);

	float diff = max(dot(norm, light_dir), 0.0);
	vec3 diffuse = diff * light_color;

	//float specular_strength = 0.7;
	//vec3 view_dir = normalize(view_position - v_frag_pos);
	//vec3 reflect_dir = reflect(-light_dir, norm);

	//float spec = pow(max(dot(view_dir, reflect_dir), 0.0), 16);
	//vec3 specular = specular_strength * spec * light_color;

	//vec3 result = (ambient + diffuse + specular) * vec3(v_color); // objectColor;
	
    vec3 result = (ambient + diffuse) * vec3(v_color); // objectColor;
	out_frag_color = vec4(result, 1.0);
}
"""
