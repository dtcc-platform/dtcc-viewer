import glfw
from OpenGL.GL import *
from OpenGL.GLU import *
from OpenGL.GL.shaders import compileProgram, compileShader
from ctypes import *
import numpy as np
import pyrr
from enum import Enum
import math
from dtcc_viewer.opengl_viewer.interaction import Interaction
from picking_interaction import PickingInteraction

window_w = 1200
window_h = 1200


action = PickingInteraction(window_w, window_h)

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


vertex_shader_normal = """
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

fragment_shader_normal = """ 
# version 330 core

in vec3 v_frag_pos;
in vec3 v_color;
in vec3 v_normal;

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


# glfw callback function
def window_resize(window, width, height):
    global window_w
    global window_h
    window_w = width
    window_h = height
    glViewport(0, 0, width, height)
    global action
    action.update_window_size(width, height)
    project = pyrr.matrix44.create_perspective_projection(
        45, window_w / window_h, 0.1, 100
    )
    glUniformMatrix4fv(project_loc, 1, GL_FALSE, project)


if not glfw.init():
    raise Exception("glfw can not be initialised!")

glfw.window_hint(glfw.CONTEXT_VERSION_MAJOR, 3)
glfw.window_hint(glfw.CONTEXT_VERSION_MINOR, 3)
glfw.window_hint(glfw.OPENGL_FORWARD_COMPAT, True)
glfw.window_hint(glfw.OPENGL_PROFILE, glfw.OPENGL_CORE_PROFILE)
window = glfw.create_window(
    window_w, window_h, "OpenGL Window", None, None
)  # Create window

if not window:
    glfw.terminate()
    raise Exception("glfw window can not be created!")

glfw.set_window_pos(window, 400, 200)


glfw.set_cursor_pos_callback(window, action.mouse_look_callback)
glfw.set_key_callback(window, action.key_input_callback)
glfw.set_mouse_button_callback(window, action.mouse_input_callback)
glfw.set_scroll_callback(window, action.scroll_input_callback)

glfw.set_window_size_callback(window, window_resize)

# Calls can be made after the contex is made current
glfw.make_context_current(window)

floor_size = 30
floor_z = -2.0

tex_min = 0
tex_max = 1

debug_vertices = [
    -floor_size,
    -floor_size,
    0,
    tex_min,
    tex_min,
    floor_size,
    -floor_size,
    0,
    tex_max,
    tex_min,
    -floor_size,
    floor_size,
    0,
    tex_min,
    tex_max,
    floor_size,
    -floor_size,
    0,
    tex_max,
    tex_min,
    -floor_size,
    floor_size,
    0,
    tex_min,
    tex_max,
    floor_size,
    floor_size,
    0,
    tex_max,
    tex_max,
]

debug_indices = [
    0,
    1,
    2,
    3,
    4,
    5,
]

floor_vertices = [
    -floor_size,
    -floor_size,
    floor_z,
    1,
    1,
    1,
    0,
    0,
    1,
    floor_size,
    -floor_size,
    floor_z,
    1,
    1,
    1,
    0,
    0,
    1,
    -floor_size,
    floor_size,
    floor_z,
    1,
    1,
    1,
    0,
    0,
    1,
    floor_size,
    -floor_size,
    floor_z,
    1,
    1,
    1,
    0,
    0,
    1,
    -floor_size,
    floor_size,
    floor_z,
    1,
    1,
    1,
    0,
    0,
    1,
    floor_size,
    floor_size,
    floor_z,
    1,
    1,
    1,
    0,
    0,
    1,
]

floor_indices = [
    0,
    1,
    2,
    3,
    4,
    5,
]

cube_vertices = [
    -0.5,
    0.5,
    -0.5,
    0.9960784314,
    0.7764705882,
    0,
    0,
    0,
    -1,
    -0.5,
    -0.5,
    -0.5,
    1,
    0.1490196078,
    0,
    0,
    0,
    -1,
    0.5,
    -0.5,
    -0.5,
    0.9960784314,
    0.7764705882,
    0,
    0,
    0,
    -1,
    -0.5,
    0.5,
    -0.5,
    0.9960784314,
    0.7764705882,
    0,
    0,
    0,
    -1,
    0.5,
    -0.5,
    -0.5,
    0.9960784314,
    0.7764705882,
    0,
    0,
    0,
    -1,
    0.5,
    0.5,
    -0.5,
    0.7450980392,
    0.9882352941,
    0,
    0,
    0,
    -1,
    -0.5,
    0.5,
    0.5,
    0.7450980392,
    0.9882352941,
    0,
    0,
    0,
    1,
    0.5,
    0.5,
    0.5,
    0,
    1,
    0,
    0,
    0,
    1,
    0.5,
    -0.5,
    0.5,
    0.7450980392,
    0.9882352941,
    0,
    0,
    0,
    1,
    -0.5,
    0.5,
    0.5,
    0.7450980392,
    0.9882352941,
    0,
    0,
    0,
    1,
    0.5,
    -0.5,
    0.5,
    0.7450980392,
    0.9882352941,
    0,
    0,
    0,
    1,
    -0.5,
    -0.5,
    0.5,
    0.9960784314,
    0.7764705882,
    0,
    0,
    0,
    1,
    -0.5,
    0.5,
    0.5,
    0.7450980392,
    0.9882352941,
    0,
    -1,
    0,
    0,
    -0.5,
    -0.5,
    0.5,
    0.9960784314,
    0.7764705882,
    0,
    -1,
    0,
    0,
    -0.5,
    -0.5,
    -0.5,
    1,
    0.1490196078,
    0,
    -1,
    0,
    0,
    -0.5,
    0.5,
    0.5,
    0.7450980392,
    0.9882352941,
    0,
    -1,
    0,
    0,
    -0.5,
    -0.5,
    -0.5,
    1,
    0.1490196078,
    0,
    -1,
    0,
    0,
    -0.5,
    0.5,
    -0.5,
    0.9960784314,
    0.7764705882,
    0,
    -1,
    0,
    0,
    0.5,
    0.5,
    0.5,
    0,
    1,
    0,
    0,
    1,
    0,
    -0.5,
    0.5,
    0.5,
    0.7450980392,
    0.9882352941,
    0,
    0,
    1,
    0,
    -0.5,
    0.5,
    -0.5,
    0.9960784314,
    0.7764705882,
    0,
    0,
    1,
    0,
    0.5,
    0.5,
    0.5,
    0,
    1,
    0,
    0,
    1,
    0,
    -0.5,
    0.5,
    -0.5,
    0.9960784314,
    0.7764705882,
    0,
    0,
    1,
    0,
    0.5,
    0.5,
    -0.5,
    0.7450980392,
    0.9882352941,
    0,
    0,
    1,
    0,
    0.5,
    -0.5,
    0.5,
    0.7450980392,
    0.9882352941,
    0,
    1,
    0,
    0,
    0.5,
    0.5,
    0.5,
    0,
    1,
    0,
    1,
    0,
    0,
    0.5,
    0.5,
    -0.5,
    0.7450980392,
    0.9882352941,
    0,
    1,
    0,
    0,
    0.5,
    -0.5,
    0.5,
    0.7450980392,
    0.9882352941,
    0,
    1,
    0,
    0,
    0.5,
    0.5,
    -0.5,
    0.7450980392,
    0.9882352941,
    0,
    1,
    0,
    0,
    0.5,
    -0.5,
    -0.5,
    0.9960784314,
    0.7764705882,
    0,
    1,
    0,
    0,
    -0.5,
    -0.5,
    0.5,
    0.9960784314,
    0.7764705882,
    0,
    0,
    -1,
    0,
    0.5,
    -0.5,
    0.5,
    0.7450980392,
    0.9882352941,
    0,
    0,
    -1,
    0,
    0.5,
    -0.5,
    -0.5,
    0.9960784314,
    0.7764705882,
    0,
    0,
    -1,
    0,
    -0.5,
    -0.5,
    0.5,
    0.9960784314,
    0.7764705882,
    0,
    0,
    -1,
    0,
    0.5,
    -0.5,
    -0.5,
    0.9960784314,
    0.7764705882,
    0,
    0,
    -1,
    0,
    -0.5,
    -0.5,
    -0.5,
    1,
    0.1490196078,
    0,
    0,
    -1,
    0,
]

cube_indices = [
    0,
    1,
    2,
    3,
    4,
    5,
    6,
    7,
    8,
    9,
    10,
    11,
    12,
    13,
    14,
    15,
    16,
    17,
    18,
    19,
    20,
    21,
    22,
    23,
    24,
    25,
    26,
    27,
    28,
    29,
    30,
    31,
    32,
    33,
    34,
    35,
]

icosa_vertices = [
    0,
    0,
    0.3000000119,
    1,
    1,
    1,
    0.4911234949,
    0.3568220761,
    0.794654465,
    0.26832816,
    0,
    0.13416408,
    1,
    1,
    1,
    0.4911234949,
    0.3568220761,
    0.794654465,
    0.0829179659,
    0.25519526,
    0.13416408,
    1,
    1,
    1,
    0.4911234949,
    0.3568220761,
    0.794654465,
    0,
    0,
    0.3000000119,
    1,
    1,
    1,
    -0.1875924851,
    0.5773502685,
    0.7946544702,
    0.0829179659,
    0.25519526,
    0.13416408,
    1,
    1,
    1,
    -0.1875924851,
    0.5773502685,
    0.7946544702,
    -0.2170820385,
    0.1577193439,
    0.13416408,
    1,
    1,
    1,
    -0.1875924851,
    0.5773502685,
    0.7946544702,
    0,
    0,
    0.3000000119,
    1,
    1,
    1,
    -0.607062024,
    0,
    0.7946544526,
    -0.2170820385,
    0.1577193439,
    0.13416408,
    1,
    1,
    1,
    -0.607062024,
    0,
    0.7946544526,
    -0.2170820385,
    -0.1577193439,
    0.13416408,
    1,
    1,
    1,
    -0.607062024,
    0,
    0.7946544526,
    0,
    0,
    0.3000000119,
    1,
    1,
    1,
    -0.1875924851,
    -0.5773502685,
    0.7946544702,
    -0.2170820385,
    -0.1577193439,
    0.13416408,
    1,
    1,
    1,
    -0.1875924851,
    -0.5773502685,
    0.7946544702,
    0.0829179659,
    -0.25519526,
    0.13416408,
    1,
    1,
    1,
    -0.1875924851,
    -0.5773502685,
    0.7946544702,
    0,
    0,
    0.3000000119,
    1,
    1,
    1,
    0.4911234949,
    -0.3568220761,
    0.794654465,
    0.0829179659,
    -0.25519526,
    0.13416408,
    1,
    1,
    1,
    0.4911234949,
    -0.3568220761,
    0.794654465,
    0.26832816,
    0,
    0.13416408,
    1,
    1,
    1,
    0.4911234949,
    -0.3568220761,
    0.794654465,
    0.26832816,
    0,
    0.13416408,
    1,
    1,
    1,
    0.7946544968,
    -0.5773502395,
    0.1875924616,
    0.0829179659,
    -0.25519526,
    0.13416408,
    1,
    1,
    1,
    0.7946544968,
    -0.5773502395,
    0.1875924616,
    0.2170820385,
    -0.1577193439,
    -0.13416408,
    1,
    1,
    1,
    0.7946544968,
    -0.5773502395,
    0.1875924616,
    0.26832816,
    0,
    0.13416408,
    1,
    1,
    1,
    0.7946544968,
    0.5773502395,
    0.1875924616,
    0.2170820385,
    0.1577193439,
    -0.13416408,
    1,
    1,
    1,
    0.7946544968,
    0.5773502395,
    0.1875924616,
    0.0829179659,
    0.25519526,
    0.13416408,
    1,
    1,
    1,
    0.7946544968,
    0.5773502395,
    0.1875924616,
    0.26832816,
    0,
    0.13416408,
    1,
    1,
    1,
    0.9822469443,
    0,
    -0.1875924848,
    0.2170820385,
    -0.1577193439,
    -0.13416408,
    1,
    1,
    1,
    0.9822469443,
    0,
    -0.1875924848,
    0.2170820385,
    0.1577193439,
    -0.13416408,
    1,
    1,
    1,
    0.9822469443,
    0,
    -0.1875924848,
    0.0829179659,
    0.25519526,
    0.13416408,
    1,
    1,
    1,
    0.3035310144,
    0.9341723501,
    -0.1875924935,
    0.2170820385,
    0.1577193439,
    -0.13416408,
    1,
    1,
    1,
    0.3035310144,
    0.9341723501,
    -0.1875924935,
    -0.0829179659,
    0.25519526,
    -0.13416408,
    1,
    1,
    1,
    0.3035310144,
    0.9341723501,
    -0.1875924935,
    0.0829179659,
    0.25519526,
    0.13416408,
    1,
    1,
    1,
    -0.3035310144,
    0.9341723501,
    0.1875924935,
    -0.0829179659,
    0.25519526,
    -0.13416408,
    1,
    1,
    1,
    -0.3035310144,
    0.9341723501,
    0.1875924935,
    -0.2170820385,
    0.1577193439,
    0.13416408,
    1,
    1,
    1,
    -0.3035310144,
    0.9341723501,
    0.1875924935,
    -0.2170820385,
    0.1577193439,
    0.13416408,
    1,
    1,
    1,
    -0.7946544968,
    0.5773502395,
    -0.1875924616,
    -0.0829179659,
    0.25519526,
    -0.13416408,
    1,
    1,
    1,
    -0.7946544968,
    0.5773502395,
    -0.1875924616,
    -0.26832816,
    0,
    -0.13416408,
    1,
    1,
    1,
    -0.7946544968,
    0.5773502395,
    -0.1875924616,
    -0.2170820385,
    0.1577193439,
    0.13416408,
    1,
    1,
    1,
    -0.9822469443,
    0,
    0.1875924848,
    -0.26832816,
    0,
    -0.13416408,
    1,
    1,
    1,
    -0.9822469443,
    0,
    0.1875924848,
    -0.2170820385,
    -0.1577193439,
    0.13416408,
    1,
    1,
    1,
    -0.9822469443,
    0,
    0.1875924848,
    -0.2170820385,
    -0.1577193439,
    0.13416408,
    1,
    1,
    1,
    -0.7946544968,
    -0.5773502395,
    -0.1875924616,
    -0.26832816,
    0,
    -0.13416408,
    1,
    1,
    1,
    -0.7946544968,
    -0.5773502395,
    -0.1875924616,
    -0.0829179659,
    -0.25519526,
    -0.13416408,
    1,
    1,
    1,
    -0.7946544968,
    -0.5773502395,
    -0.1875924616,
    -0.2170820385,
    -0.1577193439,
    0.13416408,
    1,
    1,
    1,
    -0.3035310144,
    -0.9341723501,
    0.1875924935,
    -0.0829179659,
    -0.25519526,
    -0.13416408,
    1,
    1,
    1,
    -0.3035310144,
    -0.9341723501,
    0.1875924935,
    0.0829179659,
    -0.25519526,
    0.13416408,
    1,
    1,
    1,
    -0.3035310144,
    -0.9341723501,
    0.1875924935,
    0.0829179659,
    -0.25519526,
    0.13416408,
    1,
    1,
    1,
    0.3035310144,
    -0.9341723501,
    -0.1875924935,
    -0.0829179659,
    -0.25519526,
    -0.13416408,
    1,
    1,
    1,
    0.3035310144,
    -0.9341723501,
    -0.1875924935,
    0.2170820385,
    -0.1577193439,
    -0.13416408,
    1,
    1,
    1,
    0.3035310144,
    -0.9341723501,
    -0.1875924935,
    0.2170820385,
    0.1577193439,
    -0.13416408,
    1,
    1,
    1,
    0.607062024,
    0,
    -0.7946544526,
    0.2170820385,
    -0.1577193439,
    -0.13416408,
    1,
    1,
    1,
    0.607062024,
    0,
    -0.7946544526,
    0,
    0,
    -0.3000000119,
    1,
    1,
    1,
    0.607062024,
    0,
    -0.7946544526,
    0.2170820385,
    0.1577193439,
    -0.13416408,
    1,
    1,
    1,
    0.1875924851,
    0.5773502685,
    -0.7946544702,
    0,
    0,
    -0.3000000119,
    1,
    1,
    1,
    0.1875924851,
    0.5773502685,
    -0.7946544702,
    -0.0829179659,
    0.25519526,
    -0.13416408,
    1,
    1,
    1,
    0.1875924851,
    0.5773502685,
    -0.7946544702,
    -0.0829179659,
    0.25519526,
    -0.13416408,
    1,
    1,
    1,
    -0.4911234949,
    0.3568220761,
    -0.794654465,
    0,
    0,
    -0.3000000119,
    1,
    1,
    1,
    -0.4911234949,
    0.3568220761,
    -0.794654465,
    -0.26832816,
    0,
    -0.13416408,
    1,
    1,
    1,
    -0.4911234949,
    0.3568220761,
    -0.794654465,
    -0.26832816,
    0,
    -0.13416408,
    1,
    1,
    1,
    -0.4911234949,
    -0.3568220761,
    -0.794654465,
    0,
    0,
    -0.3000000119,
    1,
    1,
    1,
    -0.4911234949,
    -0.3568220761,
    -0.794654465,
    -0.0829179659,
    -0.25519526,
    -0.13416408,
    1,
    1,
    1,
    -0.4911234949,
    -0.3568220761,
    -0.794654465,
    -0.0829179659,
    -0.25519526,
    -0.13416408,
    1,
    1,
    1,
    0.1875924851,
    -0.5773502685,
    -0.7946544702,
    0,
    0,
    -0.3000000119,
    1,
    1,
    1,
    0.1875924851,
    -0.5773502685,
    -0.7946544702,
    0.2170820385,
    -0.1577193439,
    -0.13416408,
    1,
    1,
    1,
    0.1875924851,
    -0.5773502685,
    -0.7946544702,
]

icosa_indices = [
    0,
    1,
    2,
    3,
    4,
    5,
    6,
    7,
    8,
    9,
    10,
    11,
    12,
    13,
    14,
    15,
    16,
    17,
    18,
    19,
    20,
    21,
    22,
    23,
    24,
    25,
    26,
    27,
    28,
    29,
    30,
    31,
    32,
    33,
    34,
    35,
    36,
    37,
    38,
    39,
    40,
    41,
    42,
    43,
    44,
    45,
    46,
    47,
    48,
    49,
    50,
    51,
    52,
    53,
    54,
    55,
    56,
    57,
    58,
    59,
]


# ---------------- DEBUG QUAD ---------------------#

debug_vertices = np.array(debug_vertices, dtype=np.float32)
debug_indices = np.array(debug_indices, dtype=np.uint32)

VAO_debug = glGenVertexArrays(1)
glBindVertexArray(VAO_debug)

# Vertex buffer
VBO_debug = glGenBuffers(1)
glBindBuffer(GL_ARRAY_BUFFER, VBO_debug)
glBufferData(
    GL_ARRAY_BUFFER, len(debug_vertices) * 4, debug_vertices, GL_STATIC_DRAW
)  # Second argument is nr of bytes

# Element buffer
EBO_debug = glGenBuffers(1)
glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, EBO_debug)
glBufferData(
    GL_ELEMENT_ARRAY_BUFFER, len(debug_indices) * 4, debug_indices, GL_STATIC_DRAW
)

# Position
glEnableVertexAttribArray(0)  # 0 is the layout location for the vertex shader
glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, 20, ctypes.c_void_p(0))

# Texture coordinates
glEnableVertexAttribArray(1)  # 1 is the layout location for the vertex shader
glVertexAttribPointer(1, 2, GL_FLOAT, GL_FALSE, 20, ctypes.c_void_p(12))

# ---------------- FLOOR ---------------------#
floor_vertices = np.array(floor_vertices, dtype=np.float32)
floor_indices = np.array(floor_indices, dtype=np.uint32)

VAO_floor = glGenVertexArrays(1)
glBindVertexArray(VAO_floor)

# Vertex buffer
VBO_floor = glGenBuffers(1)
glBindBuffer(GL_ARRAY_BUFFER, VBO_floor)
glBufferData(
    GL_ARRAY_BUFFER, len(floor_vertices) * 4, floor_vertices, GL_STATIC_DRAW
)  # Second argument is nr of bytes

# Element buffer
EBO_floor = glGenBuffers(1)
glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, EBO_floor)
glBufferData(
    GL_ELEMENT_ARRAY_BUFFER, len(floor_indices) * 4, floor_indices, GL_STATIC_DRAW
)

# Position
glEnableVertexAttribArray(0)  # 0 is the layout location for the vertex shader
glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, 36, ctypes.c_void_p(0))

# Color
glEnableVertexAttribArray(1)  # 1 is the layout location for the vertex shader
glVertexAttribPointer(1, 3, GL_FLOAT, GL_FALSE, 36, ctypes.c_void_p(12))

# Normal
glEnableVertexAttribArray(2)  # 1 is the layout location for the vertex shader
glVertexAttribPointer(2, 3, GL_FLOAT, GL_FALSE, 36, ctypes.c_void_p(24))

# ---------------- CUBE ---------------------#

cube_vertices = np.array(cube_vertices, dtype=np.float32)
cube_indices = np.array(cube_indices, dtype=np.uint32)

cube_vertices[0::9] *= 4.0
cube_vertices[1::9] *= 4.0
cube_vertices[2::9] *= 4.0

VAO_cube = glGenVertexArrays(1)
glBindVertexArray(VAO_cube)

# Vertex buffer
VBO_cube = glGenBuffers(1)
glBindBuffer(GL_ARRAY_BUFFER, VBO_cube)
glBufferData(
    GL_ARRAY_BUFFER, len(cube_vertices) * 4, cube_vertices, GL_STATIC_DRAW
)  # Second argument is nr of bytes

# Element buffer
EBO_cube = glGenBuffers(1)
glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, EBO_cube)
glBufferData(
    GL_ELEMENT_ARRAY_BUFFER, len(cube_indices) * 4, cube_indices, GL_STATIC_DRAW
)

# Position
glEnableVertexAttribArray(0)  # 0 is the layout location for the vertex shader
glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, 36, ctypes.c_void_p(0))

# Color
glEnableVertexAttribArray(1)  # 1 is the layout location for the vertex shader
glVertexAttribPointer(1, 3, GL_FLOAT, GL_FALSE, 36, ctypes.c_void_p(12))

# Normal
glEnableVertexAttribArray(2)  # 1 is the layout location for the vertex shader
glVertexAttribPointer(2, 3, GL_FLOAT, GL_FALSE, 36, ctypes.c_void_p(24))


# ---------------- ICOSAHEDRON ---------------------#

icosa_vertices = np.array(icosa_vertices, dtype=np.float32)
icosa_indices = np.array(icosa_indices, dtype=np.uint32)

VAO_icosa = glGenVertexArrays(1)
glBindVertexArray(VAO_icosa)

# Vertex buffer
VBO_icosa = glGenBuffers(1)
glBindBuffer(GL_ARRAY_BUFFER, VBO_icosa)
glBufferData(
    GL_ARRAY_BUFFER, len(icosa_vertices) * 4, icosa_vertices, GL_STATIC_DRAW
)  # Second argument is nr of bytes

# Element buffer
EBO_icosa = glGenBuffers(1)
glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, EBO_icosa)
glBufferData(
    GL_ELEMENT_ARRAY_BUFFER, len(icosa_indices) * 4, icosa_indices, GL_STATIC_DRAW
)

# Position
glEnableVertexAttribArray(0)  # 0 is the layout location for the vertex shader
glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, 36, ctypes.c_void_p(0))

# Color
glEnableVertexAttribArray(1)  # 1 is the layout location for the vertex shader
glVertexAttribPointer(1, 3, GL_FLOAT, GL_FALSE, 36, ctypes.c_void_p(12))

# Normal
glEnableVertexAttribArray(2)  # 1 is the layout location for the vertex shader
glVertexAttribPointer(2, 3, GL_FLOAT, GL_FALSE, 36, ctypes.c_void_p(24))


# ---------------- NORMAL SHADER ---------------------#

shader_normal = compileProgram(
    compileShader(vertex_shader_normal, GL_VERTEX_SHADER),
    compileShader(fragment_shader_normal, GL_FRAGMENT_SHADER),
)

glUseProgram(shader_normal)

model_loc = glGetUniformLocation(shader_normal, "model")
project_loc = glGetUniformLocation(shader_normal, "project")
view_loc = glGetUniformLocation(shader_normal, "view")

light_color_loc = glGetUniformLocation(shader_normal, "light_color")
light_position_loc = glGetUniformLocation(shader_normal, "light_position")
view_pos_loc = glGetUniformLocation(shader_normal, "view_position")

light_pos = 3.0 * np.array([10.0, 10.0, 10.0], dtype=np.float32)
light_color = np.array([1.0, 1.0, 1.0], dtype=np.float32)

glUniform3f(light_color_loc, 1.0, 1.0, 1.0)
glUniform3f(light_position_loc, 0.0, 0.0, 10.0)


# ---------------- PICKING SHADER ---------------------#

shader_picking = compileProgram(
    compileShader(vertex_shader_picking, GL_VERTEX_SHADER),
    compileShader(fragment_shader_picking, GL_FRAGMENT_SHADER),
)

glUseProgram(shader_picking)

model_loc_picking = glGetUniformLocation(shader_picking, "model")
project_loc_picking = glGetUniformLocation(shader_picking, "project")
view_loc_picking = glGetUniformLocation(shader_picking, "view")
picking_color_loc = glGetUniformLocation(shader_picking, "picking_color")

glClearColor(0.0, 0.0, 0.0, 1)
glEnable(GL_DEPTH_TEST)


def calc_ray_coords():
    winx = 0.0  # action.select_x
    winy = 0.0  # action.select_y
    winz_near = 0.2
    winz_far = 1.0
    clip_w = 1.0

    # m = pyrr.matrix44.create_from_translation(pyrr.Vector3([0, 0, 0], dtype=np.float32))
    # mv = action.camera.get_view_matrix().astype("d")
    # pr = action.camera.get_perspective_matrix().astype("d")

    # glMatrixMode(GL_MODELVIEW)
    # glLoadIdentity()
    # gluLookAt(0, 1, 20, 0, 0, 0, 0, 0, 1)

    # mv = glGetDoublev(GL_MODELVIEW_MATRIX)

    # viewport = glGetIntegerv(GL_VIEWPORT)

    # near = gluUnProject(winx, winy, winz_near, mv, pr, viewport)

    # Ray end at far plane
    # far = gluUnProject(gluUnProject, winx, winy, winz_far, m, p, v)

    # print("Near: ", near)
    # print("Far: ", far)


def id_to_color(id):
    # Extracting color components
    r = (id & 0x000000FF) >> 0
    g = (id & 0x0000FF00) >> 8
    b = (id & 0x00FF0000) >> 16

    return np.array([r, g, b], dtype=np.float32)


def color_to_id(color):
    id = data[0] + data[1] * 256 + data[2] * 256 * 256
    return id


trans_vecs = []
trans_vecs.append([7, -7, 2])
trans_vecs.append([7, 7, 2])
trans_vecs.append([-7, 7, 2])
trans_vecs.append([-7, -7, 2])
trans_vecs = np.array(trans_vecs, dtype=np.float32)

cube_ids = [10, 2000, 300000, 40000]


def render_picking(time, proj, view):
    # Only the cubes are pickable
    glBindVertexArray(VAO_cube)
    for i in range(len(trans_vecs)):
        id = cube_ids[i]
        c = id_to_color(id)
        glUniform4f(picking_color_loc, c[0] / 255.0, c[1] / 255.0, c[2] / 255.0, 1.0)
        trans = pyrr.matrix44.create_from_translation(pyrr.Vector3(trans_vecs[i, :]))
        glUniformMatrix4fv(model_loc_picking, 1, GL_FALSE, trans)
        glDrawElements(GL_TRIANGLES, len(cube_indices), GL_UNSIGNED_INT, None)


def render_scene(time):
    # Floor
    model_floor = pyrr.matrix44.create_from_translation(pyrr.Vector3([0, 0, 0]))
    glUniformMatrix4fv(model_loc, 1, GL_FALSE, model_floor)
    glBindVertexArray(VAO_floor)
    glDrawElements(GL_TRIANGLES, len(floor_indices), GL_UNSIGNED_INT, None)

    glBindVertexArray(VAO_cube)
    for i in range(len(trans_vecs)):
        trans = pyrr.matrix44.create_from_translation(pyrr.Vector3(trans_vecs[i, :]))
        glUniformMatrix4fv(model_loc, 1, GL_FALSE, trans)
        glDrawElements(GL_TRIANGLES, len(cube_indices), GL_UNSIGNED_INT, None)

    glBindVertexArray(VAO_icosa)
    model_icosa = pyrr.matrix44.create_from_translation(pyrr.Vector3(light_pos))
    glUniformMatrix4fv(model_loc, 1, GL_FALSE, model_icosa)
    glDrawElements(GL_TRIANGLES, len(icosa_indices), GL_UNSIGNED_INT, None)


glUseProgram(shader_normal)
glClearColor(0, 0.1, 0, 1)
glEnable(GL_DEPTH_TEST)


# Main application loop
while not glfw.window_should_close(window):
    glfw.poll_events()
    time = glfw.get_time()
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

    # Camera input
    view = action.camera.get_view_matrix()
    proj = action.camera.get_perspective_matrix()

    # Picking pass
    if action.picking:
        glClearColor(1.0, 1.0, 1.0, 1.0)
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        glUseProgram(shader_picking)

        glUniformMatrix4fv(project_loc_picking, 1, GL_FALSE, proj)
        glUniformMatrix4fv(view_loc_picking, 1, GL_FALSE, view)

        render_picking(time, proj, view)
        glFlush()
        glFinish()

        glPixelStorei(GL_UNPACK_ALIGNMENT, 1)

        x = action.picked_x / action.width
        y = action.picked_y / action.height

        x = action.picked_x
        y = action.picked_y

        data = glReadPixels(x, y, 1, 1, GL_RGBA, GL_UNSIGNED_BYTE)

        picked_id = color_to_id(data)

        if picked_id != 0x00FFFFFF:
            print(data[0], data[1], data[2])
            print("picked_id: ", picked_id)

        action.picking = False

    # Normal pass
    glClearColor(0, 0.1, 0, 1)
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    glUseProgram(shader_normal)

    # Set uniforms
    glUniformMatrix4fv(project_loc, 1, GL_FALSE, proj)
    glUniformMatrix4fv(view_loc, 1, GL_FALSE, view)

    # Set light uniforms
    camera_pos = action.camera.camera_pos
    glUniform3f(light_color_loc, light_color[0], light_color[1], light_color[2])
    glUniform3f(view_pos_loc, camera_pos[0], camera_pos[1], camera_pos[2])

    render_scene(time)
    glfw.swap_buffers(window)

glfw.terminate()
