import glfw
from OpenGL.GL import *
from OpenGL.GLU import *
from OpenGL.GL.shaders import compileProgram, compileShader
from ctypes import *
import numpy as np
import pyrr
from enum import Enum
import math
from dtcc_viewer.opengl.action import Action
from picking_interaction import PickingInteraction
from load_primitives import *
from pprint import PrettyPrinter
from dtcc_io import meshes
from string import Template
import trimesh
from dtcc_model import Mesh

window_w = 800
window_h = 800

action = PickingInteraction(window_w, window_h)

vertex_shader_normal = """
# version 330 core

layout(location = 0) in vec3 a_position; 
layout(location = 1) in vec3 a_color;
layout(location = 2) in vec3 a_normal;

uniform mat4 model;
uniform mat4 view;
uniform mat4 project;

// Uniforms representing the global minimum and maximum values
uniform float min_value; 
uniform float max_value;
uniform int color_map_type;

out vec3 v_frag_pos;
out vec3 v_color;
out vec3 v_normal;

$color_map1
$color_map2
$color_map3

void main()
{
    gl_Position = project * view * model * vec4(a_position, 1.0);
    v_frag_pos = vec3(model * vec4(a_position, 1.0));
    //v_color = a_color;
    
    if(color_map_type == 1)
    {
        v_color = rainbow(a_position.z);
    }
    else if(color_map_type == 2)
    {
        v_color = inferno(a_position.z);
    }
    else if(color_map_type == 3)
    {
        v_color = black_body(a_position.z);
    }

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
	float ambient_strength = 0.4;
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

color_map_rainbow = """ 
vec3 rainbow(float value) 
{
    // Normalize the value between 0 and 1 using the global minimum and maximum values
    float normalizedValue = (value - min_value) / (max_value - min_value);
    
    // Calculate the hue value (scaled to the range [0, 6])
    float hue = 6.0 * (1.0 - normalizedValue);
    
    // Calculate the individual color components based on the hue
    float r = max(0.0, min(1.0, abs(hue - 3.0) - 1.0));
    float g = max(0.0, min(1.0, 2.0 - abs(hue - 2.0)));
    float b = max(0.0, min(1.0, 2.0 - abs(hue - 4.0)));
    
    return vec3(r, g, b);
}
"""


color_map_inferno = """vec3 inferno(float value) {
    // Normalize the value between 0 and 1 using the global minimum and maximum values
    float normalizedValue = (value - min_value) / (max_value - min_value);
    
    // Define the color points of the color map
    vec3 black = vec3(0.0, 0.0, 0.0);
    vec3 magenta = vec3(1.0, 0.0, 1.0);
    vec3 orange = vec3(1.0, 0.647, 0.0);
    vec3 white = vec3(1.0, 1.0, 1.0);
    
    float interpolationValue = 3.0;

    // Calculate color interpolation
    vec3 color;
    if (normalizedValue <= 0.333) {
        color = mix(black, magenta, normalizedValue * interpolationValue);
    } else if (normalizedValue <= 0.666) {
        color = mix(magenta, orange, (normalizedValue - 0.333) * interpolationValue);
    } else if (normalizedValue <= 1.0) {
        color = mix(orange, white, (normalizedValue - 0.666) * interpolationValue);
    } else {
        color = white;
    }
    return color;
}"""

color_map_black_body = """vec3 black_body(float value) {
    // Normalize the value between 0 and 1 using the global minimum and maximum values
    float normalizedValue = (value - min_value) / (max_value - min_value);
    
    // Define the color points of the color map
    vec3 black = vec3(0.0, 0.0, 0.0);
    vec3 red = vec3(1.0, 0.0, 0.0);
    vec3 yellow = vec3(1.0, 1.0, 0.0);
    vec3 white = vec3(1.0, 1.0, 1.0);
    
    float interpolationValue = 3.0;

    // Calculate color interpolation
    vec3 color;
    if (normalizedValue <= 0.333) {
        color = mix(black, red, normalizedValue * interpolationValue);
    } else if (normalizedValue <= 0.666) {
        color = mix(red, yellow, (normalizedValue - 0.333) * interpolationValue);
    } else if (normalizedValue <= 1.0) {
        color = mix(yellow, white, (normalizedValue - 0.666) * interpolationValue);
    } else {
        color = white;
    }
    
    return color;
}"""

color_map_plasma = """vec3 plasma(float value) {

    vec3 sampleColors[18] = vec3[18](
        vec3(0.050383, 0.029803, 0.527975),
        vec3(0.186213, 0.018803, 0.587228),
        vec3(0.287076, 0.010855, 0.627295),
        vec3(0.381047, 0.001814, 0.653068),
        vec3(0.471457, 0.005678, 0.659897),
        vec3(0.557243, 0.047331, 0.643443),
        vec3(0.636008, 0.112092, 0.605205),
        vec3(0.706178, 0.178437, 0.553657),
        vec3(0.76809,  0.244817, 0.498465),
        vec3(0.823132, 0.311261, 0.444806),
        vec3(0.872303, 0.378774, 0.393355),
        vec3(0.915471, 0.448807, 0.34289),
        vec3(0.951344, 0.52285,  0.292275),
        vec3(0.977856, 0.602051, 0.241387),
        vec3(0.992541, 0.68703,  0.19217),
        vec3(0.992505, 0.777967, 0.152855),
        vec3(0.974443, 0.874622, 0.144061),
        vec3(0.940015, 0.975158, 0.131326)
    );

    float normalizedValue = clamp((value - data_min) / (data_max - data_min), 0.0, 1.0);

    int lastIndex = sampleColors.length() - 1;
    
    // Calculate color segments
    int index = int(normalizedValue * lastIndex);
    float weight = fract(normalizedValue * lastIndex);

    vec3 color0 = sampleColors[index];
    vec3 color1 = sampleColors[index + 1];
    vec3 color = mix(color0, color1, weight);

    return color;
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


# ------------------ Load Model --------------------#

"""
(icosa_vs_1, icosa_is_1) = get_icosahedron([-10, -10, 0], 10.0)
(icosa_vs_2, icosa_is_2) = get_icosahedron([-10, 10, 0], 10.0)
(icosa_vs_3, icosa_is_3) = get_icosahedron([10, 10, 0], 10.0)
(icosa_vs_4, icosa_is_4) = get_icosahedron([10, -10, 0], 10.0)

icosa_index_count = len(icosa_is_1)

icosa_is_2 += icosa_index_count
icosa_is_3 += icosa_index_count * 2
icosa_is_4 += icosa_index_count * 3

icosa_vertices = np.concatenate((icosa_vs_1, icosa_vs_2, icosa_vs_3, icosa_vs_4))
icosa_indices = np.concatenate((icosa_is_1, icosa_is_2, icosa_is_3, icosa_is_4))

vertices = np.array(icosa_vertices, dtype=np.float32)
indices = np.array(icosa_indices, dtype=np.uint32)
"""

# ---------------- Load Mesh Model ------------------#

mesh = meshes.load_mesh("../data/models/CitySurface.obj")

print("Face count: " + str(len(mesh.faces)))
print("Vertex count: " + str(len(mesh.vertices)))

tri_mesh = trimesh.Trimesh(vertices=mesh.vertices, faces=mesh.faces)

vs, fs = trimesh.remesh.subdivide_to_size(
    mesh.vertices, mesh.faces, max_edge=2.0, max_iter=6
)

subdee_mesh = Mesh(vertices=vs, faces=fs)

print("Face count: " + str(len(subdee_mesh.faces)))
print("Vertex count: " + str(len(subdee_mesh.vertices)))

mesh = subdee_mesh

array_length = len(mesh.faces) * 3 * 9
new_vertices = np.zeros(array_length)
face_verts = mesh.vertices[mesh.faces.flatten()]
c1 = face_verts[:-1]
c2 = face_verts[1:]
mask = np.ones(len(c1), dtype=bool)
mask[2::3] = False  # [True, True, False, True, True, False, ...]
cross_vecs = (c2 - c1)[mask]  # (v2 - v1), (v3 - v2)
cross_p = np.cross(cross_vecs[::2], cross_vecs[1::2])  # (v2 - v1) x (v3 - v2)
cross_p = cross_p / np.linalg.norm(cross_p, axis=1)[:, np.newaxis]  # normalize
vertex_mask = np.array([1, 1, 1, 0, 0, 0, 0, 0, 0], dtype=bool)
color_mask = np.array([0, 0, 0, 1, 1, 1, 0, 0, 0], dtype=bool)
normal_mask = np.array([0, 0, 0, 0, 0, 0, 1, 1, 1], dtype=bool)
mask = np.tile(vertex_mask, array_length // len(vertex_mask) + 1)[:array_length]
new_vertices[mask] = face_verts.flatten()
mask = np.tile(color_mask, array_length // len(color_mask) + 1)[:array_length]
new_vertices[mask] = np.array([1.0, 0.0, 1.0] * len(mesh.faces) * 3).flatten()
mask = np.tile(normal_mask, array_length // len(normal_mask) + 1)[:array_length]
new_vertices[mask] = np.tile(cross_p, 3).flatten()
new_faces = np.arange(array_length // 9)

debug_vertices = np.reshape(new_vertices, (-1, 9))
debug_faces = np.reshape(new_faces, (-1, 3))

# np.set_printoptions(precision=2)

vertices = np.array(new_vertices, dtype="float32").flatten()
indices = np.array(new_faces, dtype="uint32").flatten()


# ---------------- MODEL ---------------------#


VAO_icosa = glGenVertexArrays(1)
glBindVertexArray(VAO_icosa)

# Vertex buffer
VBO_icosa = glGenBuffers(1)
glBindBuffer(GL_ARRAY_BUFFER, VBO_icosa)
glBufferData(GL_ARRAY_BUFFER, len(vertices) * 4, vertices, GL_STATIC_DRAW)

# Element buffer
EBO_icosa = glGenBuffers(1)
glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, EBO_icosa)
glBufferData(GL_ELEMENT_ARRAY_BUFFER, len(indices) * 4, indices, GL_STATIC_DRAW)

# Position
glEnableVertexAttribArray(0)  # 0 is the layout location for the vertex shader
glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, 36, ctypes.c_void_p(0))

# Color
glEnableVertexAttribArray(1)  # 1 is the layout location for the vertex shader
glVertexAttribPointer(1, 3, GL_FLOAT, GL_FALSE, 36, ctypes.c_void_p(12))

# Normal
glEnableVertexAttribArray(2)  # 2 is the layout location for the vertex shader
glVertexAttribPointer(2, 3, GL_FLOAT, GL_FALSE, 36, ctypes.c_void_p(24))

# ---------------- NORMAL SHADER ---------------------#


vertex_shader_normal = Template(vertex_shader_normal).substitute(
    color_map1=color_map_rainbow,
    color_map2=color_map_inferno,
    color_map3=color_map_black_body,
)

shader_normal = compileProgram(
    compileShader(vertex_shader_normal, GL_VERTEX_SHADER),
    compileShader(fragment_shader_normal, GL_FRAGMENT_SHADER),
)

glUseProgram(shader_normal)

model_loc = glGetUniformLocation(shader_normal, "model")
project_loc = glGetUniformLocation(shader_normal, "project")
view_loc = glGetUniformLocation(shader_normal, "view")

min_loc = glGetUniformLocation(shader_normal, "min_value")
max_loc = glGetUniformLocation(shader_normal, "max_value")

cmap_loc = glGetUniformLocation(shader_normal, "color_map_type")

light_color_loc = glGetUniformLocation(shader_normal, "light_color")
light_position_loc = glGetUniformLocation(shader_normal, "light_position")
view_pos_loc = glGetUniformLocation(shader_normal, "view_position")


light_pos = 3.0 * np.array([10.0, 10.0, 10.0], dtype=np.float32)
light_color = np.array([1.0, 1.0, 1.0], dtype=np.float32)

glUniform3f(light_color_loc, 1.0, 1.0, 1.0)
glUniform3f(light_position_loc, 0.0, 0.0, 10.0)

# ----------------------- Calc min max -------------------------#

min = vertices[2::9].min()  # x values
max = vertices[2::9].max()

glUniform1f(min_loc, min)
glUniform1f(max_loc, max)


# ----------------------------------------------------------#

glUseProgram(shader_normal)
glClearColor(0, 0.1, 0, 1)
glEnable(GL_DEPTH_TEST)

# Main application loop
while not glfw.window_should_close(window):
    glfw.poll_events()
    time = glfw.get_time()
    # Clearing the default framebuffer
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

    glUniform1i(cmap_loc, action.cmap_index)

    # Camera input
    view = action.camera._get_perspective_view_matrix()
    proj = action.camera._get_perspective_matrix()

    # Normal pass
    glClearColor(0, 0.1, 0, 1)
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    glUseProgram(shader_normal)

    # Set uniforms
    glUniformMatrix4fv(project_loc, 1, GL_FALSE, proj)
    glUniformMatrix4fv(view_loc, 1, GL_FALSE, view)

    # Set light uniforms
    camera_pos = action.camera.position
    glUniform3f(light_color_loc, light_color[0], light_color[1], light_color[2])
    glUniform3f(view_pos_loc, camera_pos[0], camera_pos[1], camera_pos[2])

    glBindVertexArray(VAO_icosa)
    trans = pyrr.matrix44.create_from_translation(pyrr.Vector3([0, 0, 0]))
    glUniformMatrix4fv(model_loc, 1, GL_FALSE, trans)
    glDrawElements(GL_TRIANGLES, len(indices), GL_UNSIGNED_INT, None)

    glfw.swap_buffers(window)

glfw.terminate()
