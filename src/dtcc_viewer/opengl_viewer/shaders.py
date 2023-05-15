
# Vertex shader for the particles

vertex_shader_particle = """
# version 330 core

layout(location = 0) in vec3 a_position; 
layout(location = 1) in vec3 a_color;
layout(location = 2) in vec3 a_offset;
layout(location = 3) in vec3 a_icolor;

uniform mat4 model;
uniform mat4 project;
uniform mat4 view;
uniform int color_by;

out vec3 v_color;
void main()
{   
    vec4 final_pos = (model * vec4(a_position, 1.0)) + vec4(a_offset, 0.0);
    gl_Position = project * view * final_pos;
    if(color_by == 1)
    {
        v_color = a_icolor * a_color;
    }
    else
    {
        v_color = a_color;
    }
}
"""

# Fragement shader for the particles

fragment_shader_particle = """
# version 330 core
in vec3 v_color;
out vec4 out_color;
void main()
{
    out_color = vec4(v_color, 1.0);
}
"""

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

vertex_shader_triangels_fancy = """
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

fragment_shader_triangels_fancy = """
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



# -------- Shader from previous implementation ---------

vertex_shader_triangels_fancy_2 = """
# version 330 core

layout(location = 0) in vec3 a_position; 
layout(location = 1) in vec3 a_color;
layout(location = 2) in vec3 a_normal;

uniform mat4 model;
uniform mat4 view;
uniform mat4 project;

out vec3 v_frag_pos;
out vec3 v_color;
out vec3 v_normal;

void main()
{
    gl_Position = project * view * model * vec4(a_position, 1.0);
    v_frag_pos = vec3(model * vec4(a_position, 1.0));
    v_color = a_color;
    v_normal = a_normal;
}
"""

fragment_shader_triangels_fancy_2 = """ 
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
	float ambient_strength = 0.2;
	vec3 ambient = ambient_strength * light_color;

	vec3 norm = normalize(v_normal);
	vec3 light_dir = normalize(light_position - v_frag_pos);

	float diff = max(dot(norm, light_dir), 0.0);
	vec3 diffuse = diff * light_color;

	float specular_strength = 0.7;
	vec3 view_dir = normalize(view_position - v_frag_pos);
	vec3 reflect_dir = reflect(-light_dir, norm);

	float spec = pow(max(dot(view_dir, reflect_dir), 0.0), 16);
	vec3 specular = specular_strength * spec * light_color;

	vec3 result = (ambient + diffuse + specular) * vec3(v_color); // objectColor;
	out_frag_color = vec4(result, 1.0);

}

"""
