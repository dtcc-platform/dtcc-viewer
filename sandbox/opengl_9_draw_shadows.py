import glfw
from OpenGL.GL import *
from OpenGL.GL.shaders import compileProgram, compileShader
import numpy as np
import pyrr
from enum import Enum
import math
from dtcc_viewer.opengl_viewer.interaction import Interaction

class Projection(Enum):
    Pespective = 1
    Orthographic = 2

window_w = 1200
window_h = 1000
proj = Projection.Orthographic

vertex_shader_fancy = """
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
	float ambient_strength = 0.2;
	vec3 ambient = ambient_strength * light_color;

	vec3 norm = normalize(v_normal);
	vec3 light_dir = normalize(light_position); // - v_frag_pos);

	float diff = max(dot(norm, light_dir), 0.0);
	vec3 diffuse = diff * light_color;

	float specular_strength = 0.7;
	vec3 view_dir = normalize(view_position - v_frag_pos);
	vec3 reflect_dir = reflect(-light_dir, norm);

	//float spec = pow(max(dot(view_dir, reflect_dir), 0.0), 16);
	//vec3 specular = specular_strength * spec * light_color;

	//vec3 result = (ambient + diffuse + specular) * vec3(v_color); // objectColor;
	vec3 result = (ambient + diffuse) * vec3(v_color); // objectColor;
    out_frag_color = vec4(result, 1.0);

}
"""

vertex_shader_dm = """
#version 330 core
layout (location = 0) in vec3 a_pos;

uniform mat4 light_space_matrix;
uniform mat4 model;

void main()
{
    gl_Position = light_space_matrix * model * vec4(a_pos, 1.0);
} 
"""

fragment_shader_dm = """
#version 330 core

void main()
{             
    // gl_FragDepth = gl_FragCoord.z;
} 
"""


# glfw callback function
def window_resize(window, width, height):
    glViewport(0, 0, width, height)
    project = pyrr.matrix44.create_perspective_projection(45,width / height, 0.1, 100)
    glUniformMatrix4fv(project_loc, 1, GL_FALSE, project)
    

if not glfw.init():
    raise Exception("glfw can not be initialised!")
    
glfw.window_hint(glfw.CONTEXT_VERSION_MAJOR, 3)
glfw.window_hint(glfw.CONTEXT_VERSION_MINOR, 3)
glfw.window_hint(glfw.OPENGL_FORWARD_COMPAT, True)
glfw.window_hint(glfw.OPENGL_PROFILE, glfw.OPENGL_CORE_PROFILE)
window = glfw.create_window(window_w, window_h, "OpenGL Window", None, None)      # Create window

if not window:
    glfw.terminate()
    raise Exception("glfw window can not be created!")
    
glfw.set_window_pos(window, 400, 200)

action = Interaction(window_w, window_h)

glfw.set_cursor_pos_callback(window, action.mouse_look_callback)
glfw.set_key_callback(window, action.key_input_callback)
glfw.set_mouse_button_callback(window, action.mouse_input_callback)
glfw.set_scroll_callback(window, action.scroll_input_callback)

glfw.set_window_size_callback(window, window_resize)

# Calls can be made after the contex is made current
glfw.make_context_current(window)

floor_size = 10

floor_vertices = [ -floor_size, -floor_size, -1, 1, 1, 1, 0, 0, 1,
                    floor_size, -floor_size, -1, 1, 1, 1, 0, 0, 1,
                   -floor_size,  floor_size, -1, 1, 1, 1, 0, 0, 1,
                    floor_size, -floor_size, -1, 1, 1, 1, 0, 0, 1,
                   -floor_size,  floor_size, -1, 1, 1, 1, 0, 0, 1,
                    floor_size,  floor_size, -1, 1, 1, 1, 0, 0, 1]

floor_indices = [0,1,2,
                 3,4,5,]

cube_vertices = [-0.5,0.5,-0.5,0.9960784314,0.7764705882,0,0,0,-1,
                -0.5,-0.5,-0.5,1,0.1490196078,0,0,0,-1,
                0.5,-0.5,-0.5,0.9960784314,0.7764705882,0,0,0,-1,
                -0.5,0.5,-0.5,0.9960784314,0.7764705882,0,0,0,-1,
                0.5,-0.5,-0.5,0.9960784314,0.7764705882,0,0,0,-1,
                0.5,0.5,-0.5,0.7450980392,0.9882352941,0,0,0,-1,
                -0.5,0.5,0.5,0.7450980392,0.9882352941,0,0,0,1,
                0.5,0.5,0.5,0,1,0,0,0,1,
                0.5,-0.5,0.5,0.7450980392,0.9882352941,0,0,0,1,
                -0.5,0.5,0.5,0.7450980392,0.9882352941,0,0,0,1,
                0.5,-0.5,0.5,0.7450980392,0.9882352941,0,0,0,1,
                -0.5,-0.5,0.5,0.9960784314,0.7764705882,0,0,0,1,
                -0.5,0.5,0.5,0.7450980392,0.9882352941,0,-1,0,0,
                -0.5,-0.5,0.5,0.9960784314,0.7764705882,0,-1,0,0,
                -0.5,-0.5,-0.5,1,0.1490196078,0,-1,0,0,
                -0.5,0.5,0.5,0.7450980392,0.9882352941,0,-1,0,0,
                -0.5,-0.5,-0.5,1,0.1490196078,0,-1,0,0,
                -0.5,0.5,-0.5,0.9960784314,0.7764705882,0,-1,0,0,
                0.5,0.5,0.5,0,1,0,0,1,0,
                -0.5,0.5,0.5,0.7450980392,0.9882352941,0,0,1,0,
                -0.5,0.5,-0.5,0.9960784314,0.7764705882,0,0,1,0,
                0.5,0.5,0.5,0,1,0,0,1,0,
                -0.5,0.5,-0.5,0.9960784314,0.7764705882,0,0,1,0,
                0.5,0.5,-0.5,0.7450980392,0.9882352941,0,0,1,0,
                0.5,-0.5,0.5,0.7450980392,0.9882352941,0,1,0,0,
                0.5,0.5,0.5,0,1,0,1,0,0,
                0.5,0.5,-0.5,0.7450980392,0.9882352941,0,1,0,0,
                0.5,-0.5,0.5,0.7450980392,0.9882352941,0,1,0,0,
                0.5,0.5,-0.5,0.7450980392,0.9882352941,0,1,0,0,
                0.5,-0.5,-0.5,0.9960784314,0.7764705882,0,1,0,0,
                -0.5,-0.5,0.5,0.9960784314,0.7764705882,0,0,-1,0,
                0.5,-0.5,0.5,0.7450980392,0.9882352941,0,0,-1,0,
                0.5,-0.5,-0.5,0.9960784314,0.7764705882,0,0,-1,0,
                -0.5,-0.5,0.5,0.9960784314,0.7764705882,0,0,-1,0,
                0.5,-0.5,-0.5,0.9960784314,0.7764705882,0,0,-1,0,
                -0.5,-0.5,-0.5,1,0.1490196078,0,0,-1,0]

cube_indices = [ 0,1,2,
                3,4,5,
                6,7,8,
                9,10,11,
                12,13,14,
                15,16,17,
                18,19,20,
                21,22,23,
                24,25,26,
                27,28,29,
                30,31,32,
                33,34,35]

icosa_vertices = [0,0,0.3000000119,1,1,1,0.4911234949,0.3568220761,0.794654465,
                0.26832816,0,0.13416408,1,1,1,0.4911234949,0.3568220761,0.794654465,
                0.0829179659,0.25519526,0.13416408,1,1,1,0.4911234949,0.3568220761,0.794654465,
                0,0,0.3000000119,1,1,1,-0.1875924851,0.5773502685,0.7946544702,
                0.0829179659,0.25519526,0.13416408,1,1,1,-0.1875924851,0.5773502685,0.7946544702,
                -0.2170820385,0.1577193439,0.13416408,1,1,1,-0.1875924851,0.5773502685,0.7946544702,
                0,0,0.3000000119,1,1,1,-0.607062024,0,0.7946544526,
                -0.2170820385,0.1577193439,0.13416408,1,1,1,-0.607062024,0,0.7946544526,
                -0.2170820385,-0.1577193439,0.13416408,1,1,1,-0.607062024,0,0.7946544526,
                0,0,0.3000000119,1,1,1,-0.1875924851,-0.5773502685,0.7946544702,
                -0.2170820385,-0.1577193439,0.13416408,1,1,1,-0.1875924851,-0.5773502685,0.7946544702,
                0.0829179659,-0.25519526,0.13416408,1,1,1,-0.1875924851,-0.5773502685,0.7946544702,
                0,0,0.3000000119,1,1,1,0.4911234949,-0.3568220761,0.794654465,
                0.0829179659,-0.25519526,0.13416408,1,1,1,0.4911234949,-0.3568220761,0.794654465,
                0.26832816,0,0.13416408,1,1,1,0.4911234949,-0.3568220761,0.794654465,
                0.26832816,0,0.13416408,1,1,1,0.7946544968,-0.5773502395,0.1875924616,
                0.0829179659,-0.25519526,0.13416408,1,1,1,0.7946544968,-0.5773502395,0.1875924616,
                0.2170820385,-0.1577193439,-0.13416408,1,1,1,0.7946544968,-0.5773502395,0.1875924616,
                0.26832816,0,0.13416408,1,1,1,0.7946544968,0.5773502395,0.1875924616,
                0.2170820385,0.1577193439,-0.13416408,1,1,1,0.7946544968,0.5773502395,0.1875924616,
                0.0829179659,0.25519526,0.13416408,1,1,1,0.7946544968,0.5773502395,0.1875924616,
                0.26832816,0,0.13416408,1,1,1,0.9822469443,0,-0.1875924848,
                0.2170820385,-0.1577193439,-0.13416408,1,1,1,0.9822469443,0,-0.1875924848,
                0.2170820385,0.1577193439,-0.13416408,1,1,1,0.9822469443,0,-0.1875924848,
                0.0829179659,0.25519526,0.13416408,1,1,1,0.3035310144,0.9341723501,-0.1875924935,
                0.2170820385,0.1577193439,-0.13416408,1,1,1,0.3035310144,0.9341723501,-0.1875924935,
                -0.0829179659,0.25519526,-0.13416408,1,1,1,0.3035310144,0.9341723501,-0.1875924935,
                0.0829179659,0.25519526,0.13416408,1,1,1,-0.3035310144,0.9341723501,0.1875924935,
                -0.0829179659,0.25519526,-0.13416408,1,1,1,-0.3035310144,0.9341723501,0.1875924935,
                -0.2170820385,0.1577193439,0.13416408,1,1,1,-0.3035310144,0.9341723501,0.1875924935,
                -0.2170820385,0.1577193439,0.13416408,1,1,1,-0.7946544968,0.5773502395,-0.1875924616,
                -0.0829179659,0.25519526,-0.13416408,1,1,1,-0.7946544968,0.5773502395,-0.1875924616,
                -0.26832816,0,-0.13416408,1,1,1,-0.7946544968,0.5773502395,-0.1875924616,
                -0.2170820385,0.1577193439,0.13416408,1,1,1,-0.9822469443,0,0.1875924848,
                -0.26832816,0,-0.13416408,1,1,1,-0.9822469443,0,0.1875924848,
                -0.2170820385,-0.1577193439,0.13416408,1,1,1,-0.9822469443,0,0.1875924848,
                -0.2170820385,-0.1577193439,0.13416408,1,1,1,-0.7946544968,-0.5773502395,-0.1875924616,
                -0.26832816,0,-0.13416408,1,1,1,-0.7946544968,-0.5773502395,-0.1875924616,
                -0.0829179659,-0.25519526,-0.13416408,1,1,1,-0.7946544968,-0.5773502395,-0.1875924616,
                -0.2170820385,-0.1577193439,0.13416408,1,1,1,-0.3035310144,-0.9341723501,0.1875924935,
                -0.0829179659,-0.25519526,-0.13416408,1,1,1,-0.3035310144,-0.9341723501,0.1875924935,
                0.0829179659,-0.25519526,0.13416408,1,1,1,-0.3035310144,-0.9341723501,0.1875924935,
                0.0829179659,-0.25519526,0.13416408,1,1,1,0.3035310144,-0.9341723501,-0.1875924935,
                -0.0829179659,-0.25519526,-0.13416408,1,1,1,0.3035310144,-0.9341723501,-0.1875924935,
                0.2170820385,-0.1577193439,-0.13416408,1,1,1,0.3035310144,-0.9341723501,-0.1875924935,
                0.2170820385,0.1577193439,-0.13416408,1,1,1,0.607062024,0,-0.7946544526,
                0.2170820385,-0.1577193439,-0.13416408,1,1,1,0.607062024,0,-0.7946544526,
                0,0,-0.3000000119,1,1,1,0.607062024,0,-0.7946544526,
                0.2170820385,0.1577193439,-0.13416408,1,1,1,0.1875924851,0.5773502685,-0.7946544702,
                0,0,-0.3000000119,1,1,1,0.1875924851,0.5773502685,-0.7946544702,
                -0.0829179659,0.25519526,-0.13416408,1,1,1,0.1875924851,0.5773502685,-0.7946544702,
                -0.0829179659,0.25519526,-0.13416408,1,1,1,-0.4911234949,0.3568220761,-0.794654465,
                0,0,-0.3000000119,1,1,1,-0.4911234949,0.3568220761,-0.794654465,
                -0.26832816,0,-0.13416408,1,1,1,-0.4911234949,0.3568220761,-0.794654465,
                -0.26832816,0,-0.13416408,1,1,1,-0.4911234949,-0.3568220761,-0.794654465,
                0,0,-0.3000000119,1,1,1,-0.4911234949,-0.3568220761,-0.794654465,
                -0.0829179659,-0.25519526,-0.13416408,1,1,1,-0.4911234949,-0.3568220761,-0.794654465,
                -0.0829179659,-0.25519526,-0.13416408,1,1,1,0.1875924851,-0.5773502685,-0.7946544702,
                0,0,-0.3000000119,1,1,1,0.1875924851,-0.5773502685,-0.7946544702,
                0.2170820385,-0.1577193439,-0.13416408,1,1,1,0.1875924851,-0.5773502685,-0.7946544702]

icosa_indices = [0,1,2,
                3,4,5,
                6,7,8,
                9,10,11,
                12,13,14,
                15,16,17,
                18,19,20,
                21,22,23,
                24,25,26,
                27,28,29,
                30,31,32,
                33,34,35,
                36,37,38,
                39,40,41,
                42,43,44,
                45,46,47,
                48,49,50,
                51,52,53,
                54,55,56,
                57,58,59]

# ---------------- FLOOR ---------------------#

floor_vertices = np.array(floor_vertices, dtype=np.float32)
floor_indices = np.array(floor_indices, dtype=np.uint32)

VAO_floor = glGenVertexArrays(1)
glBindVertexArray(VAO_floor)

# Vertex buffer
VBO_floor = glGenBuffers(1)
glBindBuffer(GL_ARRAY_BUFFER, VBO_floor)
glBufferData(GL_ARRAY_BUFFER, len(floor_vertices) * 4, floor_vertices, GL_STATIC_DRAW) # Second argument is nr of bytes

# Element buffer
EBO_floor = glGenBuffers(1)
glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, EBO_floor)
glBufferData(GL_ELEMENT_ARRAY_BUFFER, len(floor_indices)* 4, floor_indices, GL_STATIC_DRAW)

# Position
glEnableVertexAttribArray(0) # 0 is the layout location for the vertex shader
glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, 36, ctypes.c_void_p(0))

# Color
glEnableVertexAttribArray(1) # 1 is the layout location for the vertex shader
glVertexAttribPointer(1, 3, GL_FLOAT, GL_FALSE, 36, ctypes.c_void_p(12))

# Normal
glEnableVertexAttribArray(2) # 1 is the layout location for the vertex shader
glVertexAttribPointer(2, 3, GL_FLOAT, GL_FALSE, 36, ctypes.c_void_p(24))


# ---------------- CUBE ---------------------#
cube_vertices = np.array(cube_vertices, dtype=np.float32)
cube_indices = np.array(cube_indices, dtype=np.uint32)

VAO_cube = glGenVertexArrays(1)
glBindVertexArray(VAO_cube)

# Vertex buffer
VBO_cube = glGenBuffers(1)
glBindBuffer(GL_ARRAY_BUFFER, VBO_cube)
glBufferData(GL_ARRAY_BUFFER, len(cube_vertices) * 4, cube_vertices, GL_STATIC_DRAW) # Second argument is nr of bytes

# Element buffer
EBO_cube = glGenBuffers(1)
glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, EBO_cube)
glBufferData(GL_ELEMENT_ARRAY_BUFFER, len(cube_indices)* 4, cube_indices, GL_STATIC_DRAW)

# Position
glEnableVertexAttribArray(0) # 0 is the layout location for the vertex shader
glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, 36, ctypes.c_void_p(0))

# Color
glEnableVertexAttribArray(1) # 1 is the layout location for the vertex shader
glVertexAttribPointer(1, 3, GL_FLOAT, GL_FALSE, 36, ctypes.c_void_p(12))

# Normal
glEnableVertexAttribArray(2) # 1 is the layout location for the vertex shader
glVertexAttribPointer(2, 3, GL_FLOAT, GL_FALSE, 36, ctypes.c_void_p(24))


# ---------------- ICOSAHEDRON ---------------------#

icosa_vertices = np.array(icosa_vertices, dtype=np.float32)
icosa_indices = np.array(icosa_indices, dtype=np.uint32)

VAO_icosa = glGenVertexArrays(1)
glBindVertexArray(VAO_icosa)

# Vertex buffer
VBO_icosa = glGenBuffers(1)
glBindBuffer(GL_ARRAY_BUFFER, VBO_icosa)
glBufferData(GL_ARRAY_BUFFER, len(icosa_vertices) * 4, icosa_vertices, GL_STATIC_DRAW) # Second argument is nr of bytes

# Element buffer
EBO_icosa = glGenBuffers(1)
glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, EBO_icosa)
glBufferData(GL_ELEMENT_ARRAY_BUFFER, len(icosa_indices)* 4, icosa_indices, GL_STATIC_DRAW)

# Position
glEnableVertexAttribArray(0) # 0 is the layout location for the vertex shader
glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, 36, ctypes.c_void_p(0))

# Color
glEnableVertexAttribArray(1) # 1 is the layout location for the vertex shader
glVertexAttribPointer(1, 3, GL_FLOAT, GL_FALSE, 36, ctypes.c_void_p(12))

# Normal
glEnableVertexAttribArray(2) # 1 is the layout location for the vertex shader
glVertexAttribPointer(2, 3, GL_FLOAT, GL_FALSE, 36, ctypes.c_void_p(24))


# ---------------- NORMAL SHADER ---------------------#

shader = compileProgram(compileShader(vertex_shader_fancy, GL_VERTEX_SHADER), compileShader(fragment_shader_fancy, GL_FRAGMENT_SHADER))

glUseProgram(shader)

model_loc = glGetUniformLocation(shader, "model")
project_loc = glGetUniformLocation(shader, "project")
view_loc = glGetUniformLocation(shader, "view")

object_color_loc = glGetUniformLocation(shader, "object_color")
light_color_loc = glGetUniformLocation(shader, "light_color")
light_position_loc = glGetUniformLocation(shader, "light_position")
view_position_loc = glGetUniformLocation(shader, "view_position")

project = pyrr.matrix44.create_perspective_projection(45, window_w / window_h, 0.1, 100)
model = pyrr.matrix44.create_from_translation(pyrr.Vector3([0, 0, 0]))

glUniformMatrix4fv(project_loc, 1, GL_FALSE, project)
glUniformMatrix4fv(model_loc, 1, GL_FALSE, model)

light_position = [4.0, 4.0, 4.0]

glUniform3f(object_color_loc, 1.0, 0.5, 0.31)
glUniform3f(light_color_loc, 1.0, 1.0, 1.0)
glUniform3f(light_position_loc, light_position[0], light_position[1], light_position[2])
glUniform3f(view_position_loc, action.camera.camera_pos[0], action.camera.camera_pos[1], action.camera.camera_pos[2])


# ---------------- SHADOW MAP ---------------------#
# Frambuffer for the shadow map
FBO = glGenFramebuffers(1)
glGenTextures(1, FBO)

# Creating a texture which will be used as the framebuffers depth buffer
depth_map = glGenTextures(1)
glBindTexture(GL_TEXTURE_2D, depth_map)
shadow_map_resolution = 1024
glTexImage2D(GL_TEXTURE_2D, 0, GL_DEPTH_COMPONENT, shadow_map_resolution, shadow_map_resolution, 0, GL_DEPTH_COMPONENT, GL_FLOAT, None);
glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST)
glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST)
glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_BORDER) 
glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_BORDER) 

glBindFramebuffer(GL_FRAMEBUFFER, FBO)
glFramebufferTexture2D(GL_FRAMEBUFFER, GL_DEPTH_ATTACHMENT, GL_TEXTURE_2D, depth_map, 0)
glDrawBuffer(GL_NONE)   #Disable drawing to the color attachements since we only care about the depth
glReadBuffer(GL_NONE)   #We don't want to read color attachements either
glBindFramebuffer(GL_FRAMEBUFFER, 0) 

shader_dm = compileProgram(compileShader(vertex_shader_dm, GL_VERTEX_SHADER), compileShader(fragment_shader_dm, GL_FRAGMENT_SHADER))

glUseProgram(shader_dm)

light_space_transform_loc = glGetUniformLocation(shader_dm, "light_space_transform")


glClearColor(0, 0.0, 0, 1)
glEnable(GL_DEPTH_TEST)


def render_scene():

    #Floor
    model_floor = pyrr.matrix44.create_from_translation(pyrr.Vector3([0, 0, 0]))
    glUniformMatrix4fv(model_loc, 1, GL_FALSE, model_floor)
    glBindVertexArray(VAO_floor)
    glDrawElements(GL_TRIANGLES, len(floor_indices), GL_UNSIGNED_INT, None)

    #Cubes
    model_cube_1 = pyrr.matrix44.create_from_translation(pyrr.Vector3([2, 0, 0]))
    glUniformMatrix4fv(model_loc, 1, GL_FALSE, model_cube_1)
    glBindVertexArray(VAO_cube)
    glDrawElements(GL_TRIANGLES, len(cube_indices), GL_UNSIGNED_INT, None)

    model_cube_2 = pyrr.matrix44.create_from_translation(pyrr.Vector3([-2, 0, 0]))
    glUniformMatrix4fv(model_loc, 1, GL_FALSE, model_cube_2)
    glDrawElements(GL_TRIANGLES, len(cube_indices), GL_UNSIGNED_INT, None)

    model_cube_3 = pyrr.matrix44.create_from_translation(pyrr.Vector3([0, 0, 3]))
    glUniformMatrix4fv(model_loc, 1, GL_FALSE, model_cube_3)
    glDrawElements(GL_TRIANGLES, len(cube_indices), GL_UNSIGNED_INT, None)

    glBindVertexArray(VAO_icosa)
    model_icosa = pyrr.matrix44.create_from_translation(pyrr.Vector3(light_position))
    glUniformMatrix4fv(model_loc, 1, GL_FALSE, model_icosa)
    glDrawElements(GL_TRIANGLES, len(icosa_indices), GL_UNSIGNED_INT, None)




# Main application loop
while not glfw.window_should_close(window):
    glfw.poll_events()

    #first pass: Capture shadow map
    light_projection = pyrr.matrix44.create_orthogonal_projection(-10, 10, -10, 10, 1.0, 20.0, dtype=np.float32) 
    light_position = np.array(light_position, dtype=np.float32)   
    look_target = np.array([0, 0, 0], dtype=np.float32)
    global_up = np.array([0, 0, 1], dtype= np.float32)
    light_view = pyrr.matrix44.create_look_at(light_position, look_target, global_up, dtype= np.float32)
    light_space_transform = pyrr.matrix44.multiply(light_view, light_projection) # Other order?
    
    #glUseProgram(shader_dm)
    #glUniformMatrix4fv(light_space_transform_loc, 1, GL_FALSE, light_space_transform)

    #glViewport(0,0,shadow_map_resolution, shadow_map_resolution)
    #glBindFramebuffer(GL_FRAMEBUFFER, FBO)
    #render_scene()
    #glClear(GL_DEPTH_BUFFER_BIT)
    
    #second pass: Rendering 3D
    #glBindFramebuffer(GL_FRAMEBUFFER, 0)        #Setting default buffer
    #glDrawBuffers()
    glUseProgram(shader)
    glViewport(0,0,window_w, window_h)
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    glBindTexture(GL_TEXTURE_2D, depth_map)


    #Camera input
    view = action.camera.get_view_matrix()
    proj = action.camera.get_perspective_matrix()
    glUniformMatrix4fv(project_loc, 1, GL_FALSE, proj)
    glUniformMatrix4fv(view_loc, 1, GL_FALSE, view)    

    render_scene()

    glfw.swap_buffers(window)


glfw.terminate()    


