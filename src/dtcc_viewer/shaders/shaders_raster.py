vertex_shader_raster = """
#version 330 core
layout (location = 0) in vec3 a_position;
layout (location = 1) in vec2 a_tex_coords;

uniform mat4 model;
uniform mat4 project;
uniform mat4 view;
uniform int color_by;
uniform int color_inv;
uniform float clip_x;
uniform float clip_y;
uniform float clip_z;

uniform int cmap_idx;
uniform int data_idx;
uniform float data_min;
uniform float data_max;

$color_map_0
$color_map_1
$color_map_2
$color_map_3
$color_map_4

out vec3 v_color;
out vec2 tex_coords;

void main()
{
    vec4 clippingPlane1 = vec4(-1, 0, 0, clip_x);
	vec4 clippingPlane2 = vec4(0, -1, 0, clip_y);
	vec4 clippingPlane3 = vec4(0, 0, -1, clip_z);

    vec4 world_pos = model * vec4(a_position, 1.0);
    
    gl_ClipDistance[0] = dot(world_pos, clippingPlane1);
    gl_ClipDistance[1] = dot(world_pos, clippingPlane2);
    gl_ClipDistance[2] = dot(world_pos, clippingPlane3);

    gl_Position = project * view * world_pos;

    v_color = vec3(1.0, 0.0, 1.0);  
    tex_coords = a_tex_coords;
} 
"""


fragment_shader_raster = """
#version 330 core

in vec3 v_color;
in vec2 tex_coords;
out vec4 out_color;

//uniform sampler2D depth_map;

void main()
{
    out_color = vec4(v_color, 1.0);
} 
"""


fragment_shader_test = """
#version 330 core

in vec3 v_color;
in vec2 tex_coords;
out vec4 out_color;

void main()
{
    // Calculate the UV coordinates of the fragment
    vec2 uv = gl_FragCoord.xy / 256.0;

    // Calculate the checkerboard pattern based on UV coordinates
    int x = int(uv.x * 8.0);
    int y = int(uv.y * 8.0);
    bool isBlack = (x + y) % 2 == 0;

    // Set the fragment color based on the checkerboard pattern
    out_color = isBlack ? vec4(0.0, 0.0, 0.0, 1.0) : vec4(1.0, 1.0, 1.0, 1.0);
}
"""


fragment_shader_checker = """
#version 330 core

in vec3 v_color;
in vec2 tex_coords;
out vec4 frag_color;

uniform sampler2D data_texture;
uniform float data_min; 
uniform float data_max;

void main()
{
    // Define the size of the checkerboard squares
    float square_size = 0.01;

    // Calculate the checkerboard pattern based on the texture coordinates
    int x_square = int(tex_coords.x / square_size);
    int y_square = int(tex_coords.y / square_size);
    int sum = x_square + y_square;

    // Alternate between black and white squares based on the sum of the square indices
    if (mod(sum, 2) == 0) {
        // Even sum: white
        frag_color = vec4(1.0, 1.0, 1.0, 1.0);
    } else {
        // Odd sum: black
        frag_color = vec4(0.0, 0.0, 0.0, 1.0);
    }
}
"""

fragment_shader_color_checker = """
#version 330 core

in vec3 v_color;
in vec2 tex_coords;
out vec4 frag_color;

uniform sampler2D data_texture;
uniform float data_min;
uniform float data_max;

void main()
{
    // Sample the data texture at the current texture coordinates
    vec4 data_sample = texture(data_texture, tex_coords);

    // Normalize the sampled value between 0 and 1
    float normalized_value = (data_sample.r - data_min) / (data_max - data_min);

    // Use the normalized value to determine the color of the square
    vec3 color = vec3(normalized_value);

    frag_color = vec4(color, 1.0);
}

"""
