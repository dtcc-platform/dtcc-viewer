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
from pprint import pp
from dtcc_io import meshes
from dtcc_viewer.opengl.utils import concatenate_meshes

window_w = 800
window_h = 800


action = PickingInteraction(window_w, window_h)

vertex_shader_quad = """
#version 330 core

layout (location = 0) in vec2 aPos;
layout (location = 1) in vec2 aTexCoords;

out vec2 TexCoords;

void main()
{
    gl_Position = vec4(aPos.x, aPos.y, 0.0, 1.0); 
    TexCoords = aTexCoords;
}
"""

fragment_shader_quad = """ 
#version 330 core
out vec4 FragColor;
  
in vec2 TexCoords;

uniform sampler2D screenTexture;

void main()
{ 
    FragColor = texture(screenTexture, TexCoords);
}
"""

vertex_shader_picking = """
# version 330 core

// Input vertex data, different for all executions of this shader.
layout(location = 0) in vec3 a_position; 
layout(location = 1) in vec3 a_color;
layout(location = 2) in vec3 a_normal;
layout(location = 3) in float a_index;

// Values that stay constant for the whole mesh.
uniform mat4 model;
uniform mat4 view;
uniform mat4 project;

out vec3 v_color;


//Convert id to color
vec3 id_to_color(int id) {
    float r = float((id & 0x000000FF) >> 0) / 255.0;
    float g = float((id & 0x0000FF00) >> 8) / 255.0;
    float b = float((id & 0x00FF0000) >> 16) / 255.0;
    return vec3(r, g, b);
}

void main()
{
    // Output position of the vertex, in clip space : MVP * position
    gl_Position = project * view * model * vec4(a_position, 1.0);
    highp int index_int = int(a_index);
    v_color = id_to_color(index_int);
}

"""

fragment_shader_picking = """ 
# version 330 core

// Input from vertex shader
in vec3 v_color;

// Ouput data
out vec4 color;

void main()
{
    color =  vec4(v_color, 1.0);
}
"""

vertex_shader_normal = """
# version 330 core

layout(location = 0) in vec3 a_position; 
layout(location = 1) in vec3 a_color;
layout(location = 2) in vec3 a_normal;
layout(location = 3) in float a_index;

uniform mat4 model;
uniform mat4 view;
uniform mat4 project;
uniform int picked_id;

out vec3 v_frag_pos;
out vec3 v_color;
out vec3 v_normal;

void main()
{
    gl_Position = project * view * model * vec4(a_position, 1.0);
    v_frag_pos = vec3(model * vec4(a_position, 1.0));

    highp int index_int = int(a_index);

    if (index_int == picked_id) // If the vertex id is the picked id
    {
        v_color = vec3(1.0, 0.0, 1.0);
    }
    else
    {
        v_color = a_color;
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


def id_to_color(id):
    # Extracting color components
    r = (id & 0x000000FF) >> 0
    g = (id & 0x0000FF00) >> 8
    b = (id & 0x00FF0000) >> 16

    return np.array([r, g, b], dtype=np.float32)


def color_to_id(color):
    id = color[0] + color[1] * 256 + color[2] * 256 * 256
    return id


def create_face_picking_attributes(n_faces):
    indices = np.arange(0, n_faces, dtype=np.uint32)
    picking_colors = np.zeros((n_faces, 9))
    picking_ids = np.zeros((n_faces, 3))

    for face_index in indices:
        id = (face_index + 1) * 1000
        c = id_to_color(id)
        d = [c[0] / 255.0, c[1] / 255.0, c[2] / 255.0] * 3
        picking_colors[face_index, :] = d
        picking_ids[face_index, :] = [id, id, id]  # Each vertex has the same id

    picking_colors = np.array(picking_colors, dtype=np.float32).flatten()
    picking_ids = np.array(picking_ids, dtype=np.float32).flatten()

    return picking_colors, picking_ids


def create_group_picking_attributes(n_faces, faces_per_group):
    n_groups = n_faces // faces_per_group
    picking_colors = []
    picking_ids = []
    for group_index in range(n_groups):
        id = (group_index + 1) * 1000
        c = id_to_color(id)
        d = [c[0] / 255.0, c[1] / 255.0, c[2] / 255.0] * 3
        for i in range(faces_per_group):
            picking_colors.append(d)
            picking_ids.append([id, id, id])  # Each vertex has the same id

    picking_colors = np.array(picking_colors, dtype=np.float32).flatten()
    picking_ids = np.array(picking_ids, dtype=np.float32).flatten()

    return picking_colors, picking_ids


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

# mesh = meshes.load_mesh("../data/models/CitySurface.obj")

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

# Vertex attributes for a quad that fills the entire screen in Normalized Device Coordinates.
# position_x, position_y, tex_coords_x, tex_coords_y
quad_vertices = [
    -1.0,
    1.0,
    0.0,
    1.0,
    -1.0,
    -1.0,
    0.0,
    0.0,
    1.0,
    -1.0,
    1.0,
    0.0,
    -1.0,
    1.0,
    0.0,
    1.0,
    1.0,
    -1.0,
    1.0,
    0.0,
    1.0,
    1.0,
    1.0,
    1.0,
]

quad_indices = [0, 1, 2, 3, 4, 5]

# ------------------ Picking Attributes --------------------#

n_vertices = len(icosa_vertices) // 9
n_faces = len(icosa_indices) // 3

(picking_colors, picking_ids) = create_face_picking_attributes(n_faces)
(picking_colors, picking_ids) = create_group_picking_attributes(n_faces, 5)

# ---------------- ICOSAHEDRON ---------------------#

icosa_vertices = np.array(icosa_vertices, dtype=np.float32)
icosa_vs_2 = np.zeros(n_vertices * 10)

mask1 = np.array([1, 1, 1, 1, 1, 1, 1, 1, 1, 0], dtype=bool)
mask2 = np.array([0, 0, 0, 0, 0, 0, 0, 0, 0, 1], dtype=bool)

mask1 = np.tile(mask1, n_vertices)
mask2 = np.tile(mask2, n_vertices)

icosa_vs_2[mask1] = icosa_vertices
icosa_vs_2[mask2] = picking_ids

icosa_vertices = np.array(icosa_vs_2, dtype=np.float32)

icosa_indices = np.array(icosa_indices, dtype=np.uint32)

VAO_icosa = glGenVertexArrays(1)
glBindVertexArray(VAO_icosa)

# Vertex buffer
VBO_icosa = glGenBuffers(1)
glBindBuffer(GL_ARRAY_BUFFER, VBO_icosa)
glBufferData(GL_ARRAY_BUFFER, len(icosa_vertices) * 4, icosa_vertices, GL_STATIC_DRAW)

# Element buffer
EBO_icosa = glGenBuffers(1)
glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, EBO_icosa)
glBufferData(
    GL_ELEMENT_ARRAY_BUFFER, len(icosa_indices) * 4, icosa_indices, GL_STATIC_DRAW
)

# Position
glEnableVertexAttribArray(0)  # 0 is the layout location for the vertex shader
glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, 40, ctypes.c_void_p(0))

# Color
glEnableVertexAttribArray(1)  # 1 is the layout location for the vertex shader
glVertexAttribPointer(1, 3, GL_FLOAT, GL_FALSE, 40, ctypes.c_void_p(12))

# Normal
glEnableVertexAttribArray(2)  # 2 is the layout location for the vertex shader
glVertexAttribPointer(2, 3, GL_FLOAT, GL_FALSE, 40, ctypes.c_void_p(24))

# Face id for picking
glEnableVertexAttribArray(3)  # 3 is the layout location for the vertex shader
glVertexAttribPointer(3, 1, GL_FLOAT, GL_FALSE, 40, ctypes.c_void_p(36))

# ---------------- QUAD ---------------------#

quad_vertices = np.array(quad_vertices, dtype=np.float32)
quad_indices = np.array(quad_indices, dtype=np.uint32)

VAO_quad = glGenVertexArrays(1)
glBindVertexArray(VAO_quad)

# Vertex buffer
VBO_quad = glGenBuffers(1)
glBindBuffer(GL_ARRAY_BUFFER, VBO_quad)
glBufferData(
    GL_ARRAY_BUFFER, len(quad_vertices) * 4, quad_vertices, GL_STATIC_DRAW
)  # Second argument is nr of bytes

# Element buffer
EBO_quad = glGenBuffers(1)
glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, EBO_quad)
glBufferData(
    GL_ELEMENT_ARRAY_BUFFER, len(quad_indices) * 4, quad_indices, GL_STATIC_DRAW
)

# Position x,y
glEnableVertexAttribArray(0)  # 0 is the layout location for the vertex shader
glVertexAttribPointer(0, 2, GL_FLOAT, GL_FALSE, 16, ctypes.c_void_p(0))

# Texture x,y
glEnableVertexAttribArray(1)  # 1 is the layout location for the vertex shader
glVertexAttribPointer(1, 2, GL_FLOAT, GL_FALSE, 16, ctypes.c_void_p(8))


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
picked_id_loc = glGetUniformLocation(shader_normal, "picked_id")

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

glClearColor(0.0, 0.0, 0.0, 1)
glEnable(GL_DEPTH_TEST)


# ---------------- QUAD SHADER ---------------------#

shader_quad = compileProgram(
    compileShader(vertex_shader_quad, GL_VERTEX_SHADER),
    compileShader(fragment_shader_quad, GL_FRAGMENT_SHADER),
)

glUseProgram(shader_quad)

text_loc_quad = glGetUniformLocation(shader_quad, "screenTexture")

# ---------------- CLICK RESULTS TEXTURE ---------------------#

ids = icosa_vertices[9::10]
n_objects = len(np.unique(ids))

TBO = glGenBuffers(1)
glBindBuffer(GL_TEXTURE_BUFFER, TBO)
glBufferData(GL_TEXTURE_BUFFER, n_objects * 4, None, GL_DYNAMIC_DRAW)


# ---------------- PICKING FRAMEBUFFER ---------------------#

FBO = glGenFramebuffers(1)
glBindFramebuffer(GL_FRAMEBUFFER, FBO)  # Bind our frame buffer

pick_texture = glGenTextures(1)
glBindTexture(GL_TEXTURE_2D, pick_texture)
glTexImage2D(GL_TEXTURE_2D, 0, GL_RGB, window_w, window_h, 0, GL_RGB, GL_FLOAT, None)
# glTexImage2D(GL_TEXTURE_2D, 0, GL_RGB, 1600, 1600, 0, GL_RGB, GL_FLOAT, None)
glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
glBindTexture(GL_TEXTURE_2D, 0)  # Unbind our texture
glFramebufferTexture2D(
    GL_FRAMEBUFFER, GL_COLOR_ATTACHMENT0, GL_TEXTURE_2D, pick_texture, 0
)

RBO = glGenRenderbuffers(1)
glBindRenderbuffer(GL_RENDERBUFFER, RBO)
glRenderbufferStorage(GL_RENDERBUFFER, GL_DEPTH24_STENCIL8, window_w, window_h)
# glRenderbufferStorage(GL_RENDERBUFFER, GL_DEPTH24_STENCIL8, 1600, 1600)

glFramebufferRenderbuffer(
    GL_FRAMEBUFFER, GL_DEPTH_STENCIL_ATTACHMENT, GL_RENDERBUFFER, RBO
)

if glCheckFramebufferStatus(GL_FRAMEBUFFER) == GL_FRAMEBUFFER_COMPLETE:
    print("Framebuffer is complete")

glBindFramebuffer(GL_FRAMEBUFFER, 0)  # Unbind our frame buffer


# ----------------------------------------------------------#


def render_scene(time):
    glBindVertexArray(VAO_icosa)
    trans = pyrr.matrix44.create_from_translation(pyrr.Vector3([0, 0, 0]))
    glUniformMatrix4fv(model_loc, 1, GL_FALSE, trans)
    glDrawElements(GL_TRIANGLES, len(icosa_indices), GL_UNSIGNED_INT, None)


glUseProgram(shader_normal)
glClearColor(0, 0.1, 0, 1)
glEnable(GL_DEPTH_TEST)


fb_size = glfw.get_framebuffer_size(window)
print(fb_size)
mac_window_w = fb_size[0]
mac_window_h = fb_size[1]

picked_id = -1

# Main application loop
while not glfw.window_should_close(window):
    glfw.poll_events()
    time = glfw.get_time()
    # Clearing the default framebuffer
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

    # Camera input
    view = action.camera._get_perspective_view_matrix()
    proj = action.camera._get_perspective_matrix()

    # Picking pass
    # if action.picking:
    glBindFramebuffer(GL_FRAMEBUFFER, FBO)
    glEnable(GL_DEPTH_TEST)
    glClearColor(1.0, 1.0, 1.0, 1.0)
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    glUseProgram(shader_picking)

    glUniformMatrix4fv(project_loc_picking, 1, GL_FALSE, proj)
    glUniformMatrix4fv(view_loc_picking, 1, GL_FALSE, view)

    render_scene(time)

    if action.picking:
        # picked_id = -1
        glPixelStorei(GL_UNPACK_ALIGNMENT, 1)
        x = action.picked_x
        y = action.picked_y

        if window_w != mac_window_w:
            x = 2 * x
            y = 2 * y

        print(x, y)
        action.picking = False

        data = glReadPixels(x, y, 1, 1, GL_RGBA, GL_UNSIGNED_BYTE)

        picked_id_new = color_to_id(data)

        if picked_id_new == picked_id:
            picked_id = -1
        else:
            picked_id = picked_id_new

        if picked_id != 0x00FFFFFF:
            print(picked_id)
            print(id_to_color(picked_id))

    # action.picking = False
    glBindFramebuffer(GL_FRAMEBUFFER, 0)

    if action.render_fbo:
        glDisable(GL_DEPTH_TEST)
        glUseProgram(shader_quad)
        glBindVertexArray(VAO_quad)
        glBindTexture(GL_TEXTURE_2D, pick_texture)
        # glUniform1i(text_loc_quad, 0)
        glDrawElements(GL_TRIANGLES, len(quad_indices), GL_UNSIGNED_INT, None)
    else:
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
        glUniform1i(picked_id_loc, picked_id)

        render_scene(time)

    glfw.swap_buffers(window)

glfw.terminate()
