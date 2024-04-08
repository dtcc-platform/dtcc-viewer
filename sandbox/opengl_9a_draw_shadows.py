import glfw
from OpenGL.GL import *
from OpenGL.GL.shaders import compileProgram, compileShader
import numpy as np
import pyrr
from enum import Enum
import math
from load_primitives import *
from dtcc_viewer.opengl.action import Action

window_w = 1200
window_h = 800


action = Action(window_w, window_h)

vertex_shader_fancy = """
# version 330 core

layout(location = 0) in vec3 a_position; 
layout(location = 1) in vec3 a_color;
layout(location = 2) in vec3 a_normal;

out vec3 v_frag_pos;
out vec3 v_normal;
out vec3 v_color;
out vec4 v_frag_pos_light_space;

uniform mat4 light_space_matrix;
uniform mat4 model;
uniform mat4 view;
uniform mat4 project;


void main()
{   
    v_frag_pos = vec3(model * vec4(a_position, 1.0));
    v_normal = transpose(inverse(mat3(model))) * a_normal;
    v_frag_pos_light_space = light_space_matrix * vec4(v_frag_pos, 1.0);
    v_color = a_color;
    gl_Position = project * view * vec4(v_frag_pos, 1.0);

}
"""

fragment_shader_fancy = """ 
# version 330 core

in vec3 v_frag_pos;
in vec3 v_normal;
in vec3 v_color;
in vec4 v_frag_pos_light_space;

out vec4 out_frag_color;

uniform sampler2D shadow_map;

uniform vec3 light_color;
uniform vec3 light_position;
uniform vec3 view_position;


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
    float bias = max(0.05 * (1.0 - dot_light_normal), 0.0005);   
    
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
	float ambient_strength = 0.2;
	vec3 ambient = ambient_strength * light_color;

	vec3 norm = normalize(v_normal);
	vec3 light_dir = normalize(light_position); // - v_frag_pos);

    float dot_light_normal = dot(norm, light_dir);

	float diff = max(dot_light_normal, 0.0);
	vec3 diffuse = diff * light_color;

    float shadow = shadow_calc(dot_light_normal);
    
    vec3 lightning = (shadow * (diffuse) + ambient) * v_color;

    out_frag_color = vec4(lightning, 1.0);

}
"""

vertex_shader_shadow = """
#version 330 core
layout (location = 0) in vec3 a_pos;

uniform mat4 light_space_matrix;
uniform mat4 model;

void main()
{
    gl_Position = light_space_matrix * model * vec4(a_pos, 1.0);
} 
"""

fragment_shader_shadow = """
#version 330 core

void main()
{             
    // gl_FragDepth = gl_FragCoord.z;
} 
"""

vertex_shader_debug = """
#version 330 core
layout (location = 0) in vec3 a_pos;
layout (location = 1) in vec2 a_tex_coords;

out vec2 tex_coords;

void main()
{
    tex_coords = a_tex_coords;
    gl_Position = vec4(a_pos, 1.0);
} 
"""

fragment_shader_debug = """
#version 330 core

out vec4 frag_color;
in vec2 tex_coords;

uniform sampler2D depth_map;

void main()
{   
    float depth_value = texture(depth_map, tex_coords).r;          
    frag_color = vec4(vec3(depth_value), 1.0); 
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


(cube_vertices, cube_indices) = get_cube()
(icosa_vertices, icosa_indices) = get_icosahedron([0, 0, 0], 1.0)
(floor_vertices, floor_indices) = get_plane(floor_size, floor_z)

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

shader_fancy = compileProgram(
    compileShader(vertex_shader_fancy, GL_VERTEX_SHADER),
    compileShader(fragment_shader_fancy, GL_FRAGMENT_SHADER),
)

glUseProgram(shader_fancy)

model_loc = glGetUniformLocation(shader_fancy, "model")
project_loc = glGetUniformLocation(shader_fancy, "project")
view_loc = glGetUniformLocation(shader_fancy, "view")

light_color_loc = glGetUniformLocation(shader_fancy, "light_color")
light_position_loc = glGetUniformLocation(shader_fancy, "light_position")
view_position_loc = glGetUniformLocation(shader_fancy, "view_position")
light_space_matrix_loc = glGetUniformLocation(shader_fancy, "light_space_matrix")

light_position = 3.0 * np.array([10.0, 10.0, 10.0], dtype=np.float32)
light_color = np.array([1.0, 1.0, 1.0], dtype=np.float32)

# ---------------- DEBUG SHADER ---------------------#

shader_debug = compileProgram(
    compileShader(vertex_shader_debug, GL_VERTEX_SHADER),
    compileShader(fragment_shader_debug, GL_FRAGMENT_SHADER),
)

glUseProgram(shader_debug)


# ---------------- SHADOW MAP ---------------------#
# Frambuffer for the shadow map
FBO = glGenFramebuffers(1)

# Creating a texture which will be used as the framebuffers depth buffer
depth_map = glGenTextures(1)
glBindTexture(GL_TEXTURE_2D, depth_map)
shadow_map_resolution = 1024
glTexImage2D(
    GL_TEXTURE_2D,
    0,
    GL_DEPTH_COMPONENT,
    shadow_map_resolution,
    shadow_map_resolution,
    0,
    GL_DEPTH_COMPONENT,
    GL_FLOAT,
    None,
)
glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST)
glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST)
glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_BORDER)
glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_BORDER)
border_color = np.array([1.0, 1.0, 1.0, 1.0], dtype=np.float32)
glTexParameterfv(GL_TEXTURE_2D, GL_TEXTURE_BORDER_COLOR, border_color)

glBindFramebuffer(GL_FRAMEBUFFER, FBO)
glFramebufferTexture2D(GL_FRAMEBUFFER, GL_DEPTH_ATTACHMENT, GL_TEXTURE_2D, depth_map, 0)
glDrawBuffer(
    GL_NONE
)  # Disable drawing to the color attachements since we only care about the depth
glReadBuffer(GL_NONE)  # We don't want to read color attachements either
glBindFramebuffer(GL_FRAMEBUFFER, 0)


# ---------------- SHADOW MAP SHADER ---------------------#

shader_shadow = compileProgram(
    compileShader(vertex_shader_shadow, GL_VERTEX_SHADER),
    compileShader(fragment_shader_shadow, GL_FRAGMENT_SHADER),
)

glUseProgram(shader_shadow)

light_space_matrix_loc = glGetUniformLocation(shader_shadow, "light_space_matrix")
model_loc = glGetUniformLocation(shader_shadow, "model")


glClearColor(0.0, 0.0, 0.0, 1)
glEnable(GL_DEPTH_TEST)


def render_scene(time):
    # Floor
    model_floor = pyrr.matrix44.create_from_translation(pyrr.Vector3([0, 0, 0]))
    glUniformMatrix4fv(model_loc, 1, GL_FALSE, model_floor)
    glBindVertexArray(VAO_floor)
    glDrawElements(GL_TRIANGLES, len(floor_indices), GL_UNSIGNED_INT, None)

    # Cubes
    model_cube_rotat = pyrr.matrix44.create_from_z_rotation(time)
    model_cube_trans = pyrr.matrix44.create_from_translation(pyrr.Vector3([7, -7, 2]))
    model_cube_1 = pyrr.matrix44.multiply(model_cube_rotat, model_cube_trans)
    glUniformMatrix4fv(model_loc, 1, GL_FALSE, model_cube_1)
    glBindVertexArray(VAO_cube)
    glDrawElements(GL_TRIANGLES, len(cube_indices), GL_UNSIGNED_INT, None)

    model_cube_rotat = pyrr.matrix44.create_from_y_rotation(time)
    model_cube_trans = pyrr.matrix44.create_from_translation(pyrr.Vector3([7, 7, 2]))
    model_cube_2 = pyrr.matrix44.multiply(model_cube_rotat, model_cube_trans)
    glUniformMatrix4fv(model_loc, 1, GL_FALSE, model_cube_2)
    glDrawElements(GL_TRIANGLES, len(cube_indices), GL_UNSIGNED_INT, None)

    model_cube_rotat = pyrr.matrix44.create_from_x_rotation(time)
    model_cube_trans = pyrr.matrix44.create_from_translation(pyrr.Vector3([-7, 7, 2]))
    model_cube_3 = pyrr.matrix44.multiply(model_cube_rotat, model_cube_trans)
    glUniformMatrix4fv(model_loc, 1, GL_FALSE, model_cube_3)
    glDrawElements(GL_TRIANGLES, len(cube_indices), GL_UNSIGNED_INT, None)

    model_cube_rotat = pyrr.matrix44.create_from_x_rotation(time)
    model_cube_trans = pyrr.matrix44.create_from_translation(pyrr.Vector3([-7, -7, 2]))
    model_cube_4 = pyrr.matrix44.multiply(model_cube_rotat, model_cube_trans)
    glUniformMatrix4fv(model_loc, 1, GL_FALSE, model_cube_4)
    glDrawElements(GL_TRIANGLES, len(cube_indices), GL_UNSIGNED_INT, None)

    model_cube_rotat = pyrr.matrix44.create_from_x_rotation(time)
    model_cube_trans = pyrr.matrix44.create_from_translation(pyrr.Vector3([7, 7, 11]))
    model_cube_5 = pyrr.matrix44.multiply(model_cube_rotat, model_cube_trans)
    glUniformMatrix4fv(model_loc, 1, GL_FALSE, model_cube_5)
    glDrawElements(GL_TRIANGLES, len(cube_indices), GL_UNSIGNED_INT, None)

    glBindVertexArray(VAO_icosa)
    model_icosa = pyrr.matrix44.create_from_translation(pyrr.Vector3(light_position))
    glUniformMatrix4fv(model_loc, 1, GL_FALSE, model_icosa)
    glDrawElements(GL_TRIANGLES, len(icosa_indices), GL_UNSIGNED_INT, None)


def render_debug():
    glBindVertexArray(VAO_debug)
    glDrawElements(GL_TRIANGLES, len(debug_indices), GL_UNSIGNED_INT, None)


debug = False

# Main application loop
while not glfw.window_should_close(window):
    glfw.poll_events()

    # first pass: Capture shadow map
    op_size = 20
    light_projection = pyrr.matrix44.create_orthogonal_projection(
        -op_size, op_size, -op_size, op_size, 1.0, 100.0, dtype=np.float32
    )
    look_target = np.array([0, 0, 0], dtype=np.float32)
    global_up = np.array([0, 0, 1], dtype=np.float32)
    light_view = pyrr.matrix44.create_look_at(
        light_position, look_target, global_up, dtype=np.float32
    )
    light_space_matrix = pyrr.matrix44.multiply(
        light_view, light_projection
    )  # Other order?
    glUseProgram(shader_shadow)
    light_space_matrix_loc = glGetUniformLocation(shader_shadow, "light_space_matrix")
    model_loc = glGetUniformLocation(shader_shadow, "model")
    glUniformMatrix4fv(light_space_matrix_loc, 1, GL_FALSE, light_space_matrix)

    glViewport(0, 0, shadow_map_resolution, shadow_map_resolution)
    glBindFramebuffer(GL_FRAMEBUFFER, FBO)
    glClear(
        GL_DEPTH_BUFFER_BIT
    )  # Only clearing depth buffer since there is no color attachement
    render_scene(glfw.get_time())

    # debug pass: Draw shadow map on a quad for visual debugging
    if debug:
        glBindFramebuffer(GL_FRAMEBUFFER, 0)
        # frameBufferSize = glfw.get_framebuffer_size(window)
        # glViewport(0,0,frameBufferSize[0], frameBufferSize[1])
        glViewport(0, 0, window_w, window_h)
        glClearColor(0.0, 0.0, 0.0, 1.0)
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        glUseProgram(shader_debug)
        glActiveTexture(GL_TEXTURE0)
        glBindTexture(GL_TEXTURE_2D, depth_map)
        render_debug()
    else:
        # second pass: Rendering 3D
        glBindFramebuffer(GL_FRAMEBUFFER, 0)  # Setting default buffer
        # frameBufferSize = glfw.get_framebuffer_size(window)
        # glViewport(0,0,frameBufferSize[0], frameBufferSize[1])
        glViewport(0, 0, window_w, window_h)
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        glUseProgram(shader_fancy)
        light_space_matrix_loc = glGetUniformLocation(
            shader_fancy, "light_space_matrix"
        )
        model_loc = glGetUniformLocation(shader_fancy, "model")

        # Camera input
        view = action.camera._get_perspective_view_matrix()
        proj = action.camera._get_perspective_matrix()
        glUniformMatrix4fv(project_loc, 1, GL_FALSE, proj)
        glUniformMatrix4fv(view_loc, 1, GL_FALSE, view)

        # Set light uniforms
        glUniform3f(light_color_loc, light_color[0], light_color[1], light_color[2])
        glUniform3f(
            view_position_loc,
            action.camera.position[0],
            action.camera.position[1],
            action.camera.position[2],
        )
        glUniform3f(
            light_position_loc, light_position[0], light_position[1], light_position[2]
        )
        glUniformMatrix4fv(light_space_matrix_loc, 1, GL_FALSE, light_space_matrix)

        glActiveTexture(GL_TEXTURE0)
        glBindTexture(GL_TEXTURE_2D, depth_map)

        render_scene(glfw.get_time())

    glfw.swap_buffers(window)


glfw.terminate()
