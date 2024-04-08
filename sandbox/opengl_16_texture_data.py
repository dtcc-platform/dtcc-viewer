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
from dtcc_viewer.utils import get_sub_mesh
from pprint import pp
import time

window_w = 800
window_h = 800

action = PickingInteraction(window_w, window_h)

vertex_shader_normal = """
# version 330 core

layout(location = 0) in vec3 a_position; 
layout(location = 1) in vec2 a_tex_index;
layout(location = 2) in vec3 a_normal;

uniform mat4 model;
uniform mat4 view;
uniform mat4 project;

// Uniforms representing the global minimum and maximum values
uniform float min_value; 
uniform float max_value;
uniform int color_map_type;

uniform sampler2D data_texture;

out vec3 v_frag_pos;
out vec3 v_color;
out vec3 v_normal;

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

void main()
{
    //vec4 data = texture(data_texture, a_tex_coords);
    ivec2 texel_coords = ivec2(a_tex_index);
    vec4 data = texelFetch(data_texture, texel_coords, 0);
    
    gl_Position = project * view * model * vec4(a_position, 1.0);
    v_frag_pos = vec3(model * vec4(a_position, 1.0));
    
    v_color = rainbow(data.r);

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


def reformat_texture_data(data: np.ndarray, max_texture_size: int):
    d_count = len(data)

    if d_count < max_texture_size:
        data = np.reshape(data, (1, d_count))
    else:
        row_count = math.ceil(len(data) / max_texture_size)
        new_data = np.zeros((row_count, max_texture_size))
        print(f"New data shape: {new_data.shape}")

        new_data = new_data.flatten()
        new_data[0:d_count] = data
        data = np.reshape(new_data, (row_count, max_texture_size))

    return data


def get_texel_indices(max_texture_size: int, new_v_count: int):
    if new_v_count < max_texture_size:
        tex_index_x = np.arange(0, new_v_count)
        tex_index_y = np.zeros(new_v_count)
    else:
        row_count = math.ceil(new_v_count / max_texture_size)
        tex_index_x = np.arange(0, max_texture_size)
        tex_index_x = np.tile(tex_index_x, row_count)[:new_v_count]
        tex_index_y = np.arange(0, row_count)
        tex_index_y = np.repeat(tex_index_y, max_texture_size)[:new_v_count]

    return tex_index_x, tex_index_y


def subdivide_mesh(mesh: Mesh, target_edge_length: float = 2.0, max_iter: int = 6):
    tri_mesh = trimesh.Trimesh(vertices=mesh.vertices, faces=mesh.faces)

    vs, fs = trimesh.remesh.subdivide_to_size(
        mesh.vertices,
        mesh.faces,
        max_edge=target_edge_length,
        max_iter=max_iter,
    )

    subdee_mesh = Mesh(vertices=vs, faces=fs)

    print("Subdee mesh: ")
    print("Face count: " + str(len(subdee_mesh.faces)))
    print("Vertex count: " + str(len(subdee_mesh.vertices)))

    return subdee_mesh


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


# ---------------- Load Mesh Model ------------------#

mesh = meshes.load_mesh("../data/models/CitySurface.obj")

mesh = get_sub_mesh([-0.02, 0.02], [-0.02, 0.02], mesh)

# mesh = subdivide_mesh(mesh, 2.0, 6)

print("Imported mesh")
print("Face count: " + str(len(mesh.faces)))
print("Vertex count: " + str(len(mesh.vertices)))

array_length = len(mesh.faces) * 3 * 8
new_vertices = np.zeros(array_length)
new_v_count = array_length // 8
face_verts = mesh.vertices[mesh.faces.flatten()]
c1 = face_verts[:-1]
c2 = face_verts[1:]
mask = np.ones(len(c1), dtype=bool)
mask[2::3] = False  # => [True, True, False, True, True, False, ...]
cross_vecs = (c2 - c1)[mask]  # => (v2 - v1), (v3 - v2)
cross_p = np.cross(cross_vecs[::2], cross_vecs[1::2])  # (v2 - v1) x (v3 - v2)
cross_p = cross_p / np.linalg.norm(cross_p, axis=1)[:, np.newaxis]  # normalize
vertex_mask = np.array([1, 1, 1, 0, 0, 0, 0, 0], dtype=bool)
text_mask_x = np.array([0, 0, 0, 1, 0, 0, 0, 0], dtype=bool)
text_mask_y = np.array([0, 0, 0, 0, 1, 0, 0, 0], dtype=bool)
normal_mask = np.array([0, 0, 0, 0, 0, 1, 1, 1], dtype=bool)

# Set coordinates
mask = np.tile(vertex_mask, array_length // len(vertex_mask) + 1)[:array_length]
new_vertices[mask] = face_verts.flatten()

# Set texel indices
max_texture_size = 50  # 16384  # from -> glGetInteger(GL_MAX_TEXTURE_SIZE)
tex_index_x, tex_index_y = get_texel_indices(max_texture_size, new_v_count)

mask = np.tile(text_mask_x, array_length // len(text_mask_x) + 1)[:array_length]
new_vertices[mask] = tex_index_x

mask = np.tile(text_mask_y, array_length // len(text_mask_y) + 1)[:array_length]
new_vertices[mask] = tex_index_y

# Set normals
mask = np.tile(normal_mask, array_length // len(normal_mask) + 1)[:array_length]
new_vertices[mask] = np.tile(cross_p, 3).flatten()
new_faces = np.arange(array_length // 8)

debug_vertices = np.reshape(new_vertices, (-1, 8))
# debug_faces = np.reshape(new_faces, (-1, 3))

vertices = np.array(new_vertices, dtype="float32").flatten()
indices = np.array(new_faces, dtype="uint32").flatten()

v_count = len(vertices) // 8
f_count = len(indices) // 3

# Generate some data
data_1 = vertices[0::8]
data_2 = vertices[1::8]
data_3 = vertices[2::8]

data_1 = reformat_texture_data(data_1, max_texture_size)
data_2 = reformat_texture_data(data_2, max_texture_size)
data_3 = reformat_texture_data(data_3, max_texture_size)

print(f"New data shape: {data_1.shape}")

np.set_printoptions(precision=3, suppress=True)

for i, v in enumerate(debug_vertices):
    pp(v[:5])

print("Restructured mesh")
print("Face count: " + str(f_count))
print("Vertex count: " + str(v_count))


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
glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, 32, ctypes.c_void_p(0))

# Texture coords
glEnableVertexAttribArray(1)  # 1 is the layout location for the vertex shader
glVertexAttribPointer(1, 2, GL_FLOAT, GL_FALSE, 32, ctypes.c_void_p(12))

# Normal
glEnableVertexAttribArray(2)  # 2 is the layout location for the vertex shader
glVertexAttribPointer(2, 3, GL_FLOAT, GL_FALSE, 32, ctypes.c_void_p(20))

# ---------------- NORMAL SHADER ---------------------#

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

data_tex_loc = glGetUniformLocation(shader_normal, "data_texture")

light_pos = 3.0 * np.array([10.0, 10.0, 10.0], dtype=np.float32)
light_color = np.array([1.0, 1.0, 1.0], dtype=np.float32)

glUniform3f(light_color_loc, 1.0, 1.0, 1.0)
glUniform3f(light_position_loc, 0.0, 0.0, 10.0)

glUniform1i(data_tex_loc, 0)

# -------------------- Texture 2D for data ------------------------#

texture_2d = glGenTextures(1)
glBindTexture(GL_TEXTURE_2D, texture_2d)

# Configure texture filtering and wrapping options
glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_EDGE)
glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_EDGE)
glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST)
glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST)

width = data_1.shape[1]
height = data_1.shape[0]

# Transfer data to the texture
glTexImage2D(
    GL_TEXTURE_2D,
    0,
    GL_R32F,
    width,
    height,
    0,
    GL_RED,
    GL_FLOAT,
    data_1,
)

# ---------------------- Update texture data ----------------------#

x_offset = 0
y_offset = 0
width = data_3.shape[1]
height = data_3.shape[0]

tic = time.perf_counter()

glTexSubImage2D(
    GL_TEXTURE_2D,
    0,
    x_offset,
    y_offset,
    width,
    height,
    GL_RED,
    GL_FLOAT,
    data_3,
)

toc = time.perf_counter()

print(f"Texture update time: {toc - tic:0.4f} seconds")

# ----------------------- Calc min max -------------------------#

min = data_3.min()  # x values
max = data_3.max()

glUniform1f(min_loc, min)
glUniform1f(max_loc, max)

# --------------------------------------------------------------#


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
