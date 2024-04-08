import glfw
from OpenGL.GL import *
from OpenGL.GL.shaders import compileProgram, compileShader
import numpy as np
import pyrr
from enum import Enum
import math
from dtcc_viewer.opengl.action import Action

window_w = 1200
window_h = 800


action = Action(window_w, window_h)

vs_solid = """ 
#version 400 core
layout (location = 0) in vec3 position;
uniform mat4 model;
uniform mat4 view;
uniform mat4 project;
void main()
{
	gl_Position = project * view * model * vec4(position, 1.0f);
}
"""

fs_solid = """ 
#version 400 core
layout(location = 0) out vec4 frag;
uniform vec3 color;
void main()
{
	frag = vec4(color, 1.0f);
}
"""

vs_transparent = """
#version 400 core
layout(location = 0) in vec3 position;
uniform mat4 model;
uniform mat4 view;
uniform mat4 project;
void main()
{
	gl_Position = project * view * model * vec4(position, 1.0f);
}
"""

fs_transparent = """
#version 400 core
layout(location = 0) out vec4 accum;
layout(location = 1) out float reveal;
uniform vec4 color;
void main()
{
	// weight function
	float weight = clamp(pow(min(1.0, color.a * 10.0) + 0.01, 3.0) * 1e8 * pow(1.0 - gl_FragCoord.z * 0.9, 3.0), 1e-2, 3e3);
	
	// store pixel color accumulation
	accum = vec4(color.rgb * color.a, color.a) * weight;
	
	// store pixel revealage threshold
	reveal = color.a;
}
"""

vs_composit = """
#version 400 core
layout(location = 0) in vec3 position;
void main()
{
	gl_Position = vec4(position, 1.0f);
}
"""

fs_composit = """
#version 400 core
layout(location = 0) out vec4 frag;

uniform sampler2D accum;            // Color accumulation buffer
uniform sampler2D reveal;           // Revealage threshold buffer
const float EPSILON = 0.00001f;     // epsilon number 

// calculate floating point numbers equality accurately
bool isApproximatelyEqual(float a, float b)
{
	return abs(a - b) <= (abs(a) < abs(b) ? abs(b) : abs(a)) * EPSILON;
}

// get the max value between three values
float max3(vec3 v) 
{
	return max(max(v.x, v.y), v.z);
}

void main()
{
	// fragment coordination
	ivec2 coords = ivec2(gl_FragCoord.xy);
	
	// fragment revealage
	float revealage = texelFetch(reveal, coords, 0).r;
	
	// save the blending and color texture fetch cost if there is not a transparent fragment
	if (isApproximatelyEqual(revealage, 1.0f)) 
		discard;
 
	// fragment color
	vec4 accumulation = texelFetch(accum, coords, 0);
	
	// suppress overflow
	if (isinf(max3(abs(accumulation.rgb)))) 
		accumulation.rgb = vec3(accumulation.a);

	// prevent floating point precision bug
	vec3 average_color = accumulation.rgb / max(accumulation.a, EPSILON);

	// blend pixels
	frag = vec4(average_color, 1.0f - revealage);
}"""

vs_composit_2 = """
#version 400 core
layout(location = 0) in vec3 a_position; 
layout(location = 1) in vec3 a_color;
layout(location = 2) in vec3 a_normal;

out vec3 v_frag_pos;
out vec3 v_color;
out vec3 v_normal;

void main()
{
    gl_Position = vec4(a_position, 1.0);
    v_frag_pos = vec3(vec4(a_position, 1.0));
    v_color = a_color;
    v_normal = a_normal;
}
"""

fs_composit_2 = """
#version 400 core

in vec3 v_frag_pos;
in vec3 v_color;
in vec3 v_normal;

uniform vec3 light_color;
uniform vec3 light_position;

uniform sampler2D accum;            // Color accumulation buffer
uniform sampler2D reveal;           // Revealage threshold buffer
const float EPSILON = 0.00001f;     // epsilon number 

out vec4 frag_color;

// calculate floating point numbers equality accurately
bool isApproximatelyEqual(float a, float b)
{
	return abs(a - b) <= (abs(a) < abs(b) ? abs(b) : abs(a)) * EPSILON;
}

// get the max value between three values
float max3(vec3 v) 
{
	return max(max(v.x, v.y), v.z);
}

void main()
{   
    // TRANSPARENCY
	// fragment coordination
	ivec2 coords = ivec2(gl_FragCoord.xy);
	
	// fragment revealage
	float revealage = texelFetch(reveal, coords, 0).r;
	
	// save the blending and color texture fetch cost if there is not a transparent fragment
	if (isApproximatelyEqual(revealage, 1.0f)) 
		discard;
 
	// fragment color
	vec4 accumulation = texelFetch(accum, coords, 0);
	
	// suppress overflow
	if (isinf(max3(abs(accumulation.rgb)))) 
		accumulation.rgb = vec3(accumulation.a);

	// prevent floating point precision bug
	vec3 average_color = accumulation.rgb / max(accumulation.a, EPSILON);

	// blend pixels
	vec4 frag_transparency = vec4(average_color, 1.0f - revealage);
     
    // DIFFUSE
	float ambient_strength = 0.3;
	vec3 ambient = ambient_strength * light_color;

	vec3 norm = normalize(v_normal);
	vec3 light_dir = normalize(light_position); // - v_frag_pos);

	float diff = max(dot(norm, light_dir), 0.0);
	vec3 diffuse = diff * light_color;
	
    vec3 result = (ambient + diffuse) * vec3(v_color); // objectColor;
	vec4 frag_diffuse = vec4(result, 1.0); 
    
    frag_color = frag_diffuse + frag_transparency;
}
"""


vs_screen = """
#version 400 core
// shader inputs
layout (location = 0) in vec3 position;
layout (location = 1) in vec2 uv;

// shader outputs
out vec2 texture_coords;

void main()
{
	texture_coords = uv;

	gl_Position = vec4(position, 1.0f);
}
"""

fs_screen = """
#version 400 core
in vec2 texture_coords;
layout (location = 0) out vec4 frag;
uniform sampler2D screen;
void main()
{
	frag = vec4(texture(screen, texture_coords).rgb, 1.0f);
}
"""


# glfw callback function
def window_resize(window, width, height):
    global window_w
    global window_h
    global action
    fb_size = glfw.get_framebuffer_size(window)
    window_w = fb_size[0]
    window_h = fb_size[1]
    glViewport(0, 0, window_w, window_h)
    action.update_window_size(window_w, window_h)


if not glfw.init():
    raise Exception("glfw can not be initialised!")

glfw.window_hint(glfw.CONTEXT_VERSION_MAJOR, 4)
glfw.window_hint(glfw.CONTEXT_VERSION_MINOR, 0)
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


floor_size = 10
floor_z = 0.0
quad_size = 5.0

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

floor_vertices = np.array(floor_vertices, dtype=np.float32)
floor_indices = np.array(floor_indices, dtype=np.uint32)

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

cube_vertices = np.array(cube_vertices, dtype=np.float32)
cube_indices = np.array(cube_indices, dtype=np.uint32)

quadVertices = [
    -quad_size,
    0.0,
    -quad_size,
    0.0,
    0.0,
    quad_size,
    0.0,
    -quad_size,
    1.0,
    0.0,
    quad_size,
    0.0,
    quad_size,
    1.0,
    1.0,
    quad_size,
    0.0,
    quad_size,
    1.0,
    1.0,
    -quad_size,
    0.0,
    quad_size,
    0.0,
    1.0,
    -quad_size,
    0.0,
    -quad_size,
    0.0,
    0.0,
]

quadVertices = np.array(quadVertices, dtype=np.float32)

screenVertices = [
    -1.0,
    -1.0,
    0.0,
    0.0,
    0.0,
    1.0,
    -1.0,
    0.0,
    1.0,
    0.0,
    1.0,
    1.0,
    0.0,
    1.0,
    1.0,
    1.0,
    1.0,
    0.0,
    1.0,
    1.0,
    -1.0,
    1.0,
    0.0,
    0.0,
    1.0,
    -1.0,
    -1.0,
    0.0,
    0.0,
    0.0,
]

screenVertices = np.array(screenVertices, dtype=np.float32)


# --------------------------------------------------------------------------------#

# quad VAO
cubeVAO = glGenVertexArrays(1)
glBindVertexArray(cubeVAO)

cubeVBO = glGenBuffers(1)
glBindBuffer(GL_ARRAY_BUFFER, cubeVBO)
glBufferData(GL_ARRAY_BUFFER, len(cube_vertices) * 4, cube_vertices, GL_STATIC_DRAW)

# Element buffer
cubeEBO = glGenBuffers(1)
glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, cubeEBO)
glBufferData(
    GL_ELEMENT_ARRAY_BUFFER, len(cube_indices) * 4, cube_indices, GL_STATIC_DRAW
)

# Position
glEnableVertexAttribArray(0)
glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, 36, ctypes.c_void_p(0))

# Color
glEnableVertexAttribArray(1)
glVertexAttribPointer(1, 3, GL_FLOAT, GL_FALSE, 36, ctypes.c_void_p(12))

# Normal
glEnableVertexAttribArray(2)
glVertexAttribPointer(2, 3, GL_FLOAT, GL_FALSE, 36, ctypes.c_void_p(24))

# --------------------------------------------------------------------------------#

quadVBO = glGenBuffers(1)
glBindBuffer(GL_ARRAY_BUFFER, quadVBO)
glBufferData(GL_ARRAY_BUFFER, len(quadVertices) * 4, quadVertices, GL_STATIC_DRAW)

# quad VAO
quadVAO = glGenVertexArrays(1)
glBindVertexArray(quadVAO)

# Position
glEnableVertexAttribArray(0)
glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, 20, ctypes.c_void_p(0))

# Texture
glEnableVertexAttribArray(1)
glVertexAttribPointer(1, 2, GL_FLOAT, GL_FALSE, 20, ctypes.c_void_p(12))


# --------------------------------------------------------------------------------#

screenVBO = glGenBuffers(1)
glBindBuffer(GL_ARRAY_BUFFER, screenVBO)
glBufferData(GL_ARRAY_BUFFER, len(screenVertices) * 4, screenVertices, GL_STATIC_DRAW)

# quad VAO
screenVAO = glGenVertexArrays(1)
glBindVertexArray(screenVAO)

# Position
glEnableVertexAttribArray(0)
glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, 20, ctypes.c_void_p(0))

# Texture
glEnableVertexAttribArray(1)
glVertexAttribPointer(1, 2, GL_FLOAT, GL_FALSE, 20, ctypes.c_void_p(12))


# ---------------- SOLID SHADER ---------------------#
solid_shader = compileProgram(
    compileShader(vs_solid, GL_VERTEX_SHADER),
    compileShader(fs_solid, GL_FRAGMENT_SHADER),
)
glUseProgram(solid_shader)
model_loc_s = glGetUniformLocation(solid_shader, "model")
view_loc_s = glGetUniformLocation(solid_shader, "view")
project_loc_s = glGetUniformLocation(solid_shader, "project")
col_loc_s = glGetUniformLocation(solid_shader, "color")


# ---------------- TRANSPARENT SHADER ---------------------#
trans_shader = compileProgram(
    compileShader(vs_transparent, GL_VERTEX_SHADER),
    compileShader(fs_transparent, GL_FRAGMENT_SHADER),
)
glUseProgram(trans_shader)
model_loc_t = glGetUniformLocation(trans_shader, "model")
view_loc_t = glGetUniformLocation(trans_shader, "view")
project_loc_t = glGetUniformLocation(trans_shader, "project")
col_loc_t = glGetUniformLocation(trans_shader, "color")

# ---------------- COMPOSITE SHADER ---------------------#
compo_shader = compileProgram(
    compileShader(vs_composit, GL_VERTEX_SHADER),
    compileShader(fs_composit, GL_FRAGMENT_SHADER),
)
glUseProgram(compo_shader)
accum_loc_c = glGetUniformLocation(compo_shader, "accum")
reveal_loc_c = glGetUniformLocation(compo_shader, "reveal")

# ---------------- COMPOSITE SHADER 2 ---------------------#
compo_shader_2 = compileProgram(
    compileShader(vs_composit_2, GL_VERTEX_SHADER),
    compileShader(fs_composit_2, GL_FRAGMENT_SHADER),
)
glUseProgram(compo_shader_2)
accum_loc_c_2 = glGetUniformLocation(compo_shader_2, "accum")
reveal_loc_c_2 = glGetUniformLocation(compo_shader_2, "reveal")

light_color_loc_c = glGetUniformLocation(compo_shader_2, "light_color")
light_pos_loc_c = glGetUniformLocation(compo_shader_2, "light_position")

light_color = pyrr.Vector3([1.0, 1.0, 1.0])
glUniform3fv(light_color_loc_c, 1, light_color)

light_position = pyrr.Vector3([10.0, 10.0, 10.0])
glUniform3fv(light_pos_loc_c, 1, light_position)


# ---------------- SCREEN SHADER ---------------------#
screen_shader = compileProgram(
    compileShader(vs_screen, GL_VERTEX_SHADER),
    compileShader(fs_screen, GL_FRAGMENT_SHADER),
)
glUseProgram(screen_shader)
screen_loc_c = glGetUniformLocation(screen_shader, "screen")

# ---------------- FRAMBUFFERS ---------------------#
opaqueFBO = glGenFramebuffers(1)
transparentFBO = glGenFramebuffers(1)

SCR_WIDTH = window_w
SCR_HEIGHT = window_h

# Set up attachments for opaque SOLID framebuffer
opaque_texture = glGenTextures(1)
glBindTexture(GL_TEXTURE_2D, opaque_texture)
glTexImage2D(
    GL_TEXTURE_2D, 0, GL_RGBA16F, SCR_WIDTH, SCR_HEIGHT, 0, GL_RGBA, GL_HALF_FLOAT, None
)
glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
glBindTexture(GL_TEXTURE_2D, 0)

depth_texture = glGenTextures(1)
glBindTexture(GL_TEXTURE_2D, depth_texture)
glTexImage2D(
    GL_TEXTURE_2D,
    0,
    GL_DEPTH_COMPONENT,
    SCR_WIDTH,
    SCR_HEIGHT,
    0,
    GL_DEPTH_COMPONENT,
    GL_FLOAT,
    None,
)
glBindTexture(GL_TEXTURE_2D, 0)

glBindFramebuffer(GL_FRAMEBUFFER, opaqueFBO)
glFramebufferTexture2D(
    GL_FRAMEBUFFER, GL_COLOR_ATTACHMENT0, GL_TEXTURE_2D, opaque_texture, 0
)
glFramebufferTexture2D(
    GL_FRAMEBUFFER, GL_DEPTH_ATTACHMENT, GL_TEXTURE_2D, depth_texture, 0
)

if glCheckFramebufferStatus(GL_FRAMEBUFFER) != GL_FRAMEBUFFER_COMPLETE:
    print("ERROR::FRAMEBUFFER:: Opaque framebuffer is not complete!")

glBindFramebuffer(GL_FRAMEBUFFER, 0)

# Set up attachments for TRANSPARENT framebuffer
accum_texture = glGenTextures(1)
glBindTexture(GL_TEXTURE_2D, accum_texture)
glTexImage2D(
    GL_TEXTURE_2D, 0, GL_RGBA16F, SCR_WIDTH, SCR_HEIGHT, 0, GL_RGBA, GL_HALF_FLOAT, None
)
glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
glBindTexture(GL_TEXTURE_2D, 0)

reveal_texture = glGenTextures(1)
glBindTexture(GL_TEXTURE_2D, reveal_texture)
glTexImage2D(GL_TEXTURE_2D, 0, GL_R8, SCR_WIDTH, SCR_HEIGHT, 0, GL_RED, GL_FLOAT, None)
glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
glBindTexture(GL_TEXTURE_2D, 0)

glBindFramebuffer(GL_FRAMEBUFFER, transparentFBO)
glFramebufferTexture2D(
    GL_FRAMEBUFFER, GL_COLOR_ATTACHMENT0, GL_TEXTURE_2D, accum_texture, 0
)
glFramebufferTexture2D(
    GL_FRAMEBUFFER, GL_COLOR_ATTACHMENT1, GL_TEXTURE_2D, reveal_texture, 0
)
glFramebufferTexture2D(
    GL_FRAMEBUFFER, GL_DEPTH_ATTACHMENT, GL_TEXTURE_2D, depth_texture, 0
)  # opaque framebuffer's depth texture

# Don't forget to explicitly tell OpenGL that your transparent framebuffer has two draw buffers
transparentDrawBuffers = [GL_COLOR_ATTACHMENT0, GL_COLOR_ATTACHMENT1]
glDrawBuffers(2, transparentDrawBuffers)

if glCheckFramebufferStatus(GL_FRAMEBUFFER) != GL_FRAMEBUFFER_COMPLETE:
    print("ERROR::FRAMEBUFFER:: Transparent framebuffer is not complete!")

glBindFramebuffer(GL_FRAMEBUFFER, 0)

# Main application loop
while not glfw.window_should_close(window):
    # ---------------------- Camera Update ------------------------------------#

    view = action.camera._get_perspective_view_matrix()
    proj = action.camera._get_perspective_matrix()

    # -------------------- Opaque pass (drawing solid objects) -------------------------#
    # Configure render states
    glEnable(GL_DEPTH_TEST)
    glDepthFunc(GL_LESS)
    glDepthMask(GL_TRUE)
    glDisable(GL_BLEND)
    glClearColor(0.0, 0.0, 0.0, 0.0)

    # Bind opaque framebuffer to render solid objects
    glBindFramebuffer(GL_FRAMEBUFFER, opaqueFBO)
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

    glUseProgram(solid_shader)

    # Draw red quad
    model_0 = pyrr.matrix44.create_from_translation(pyrr.Vector3([1.0, 0.0, 0.0]))
    color_0 = pyrr.Vector3([1.0, 0.0, 0.0])

    glUniformMatrix4fv(model_loc_s, 1, GL_FALSE, model_0)
    glUniformMatrix4fv(view_loc_s, 1, GL_FALSE, view)
    glUniformMatrix4fv(project_loc_s, 1, GL_FALSE, proj)

    glUniform3fv(col_loc_s, 1, color_0)
    glBindVertexArray(cubeVAO)
    glDrawElements(GL_TRIANGLES, len(cube_indices), GL_UNSIGNED_INT, None)

    # -------------------- Transparent pass -------------------------#

    # configure render states
    glDepthMask(GL_FALSE)
    glEnable(GL_BLEND)
    glBlendFunci(0, GL_ONE, GL_ONE)
    glBlendFunci(1, GL_ZERO, GL_ONE_MINUS_SRC_COLOR)
    glBlendEquation(GL_FUNC_ADD)

    # bind transparent framebuffer to render transparent objects
    glBindFramebuffer(GL_FRAMEBUFFER, transparentFBO)
    glClearBufferfv(GL_COLOR, 0, pyrr.Vector4([0.0, 0.0, 0.0, 0.0]))
    glClearBufferfv(GL_COLOR, 1, pyrr.Vector4([1.0, 1.0, 1.0, 1.0]))

    glUseProgram(trans_shader)

    # draw blue quad
    model_1 = pyrr.matrix44.create_from_translation(pyrr.Vector3([0.25, -1.5, 0.0]))
    color_1 = pyrr.Vector4([0.5, 0.0, 0.5, 0.2])

    glUniformMatrix4fv(model_loc_t, 1, GL_FALSE, model_1)
    glUniformMatrix4fv(view_loc_t, 1, GL_FALSE, view)
    glUniformMatrix4fv(project_loc_t, 1, GL_FALSE, proj)

    glUniform4fv(col_loc_t, 1, color_1)
    glBindVertexArray(cubeVAO)
    glDrawElements(GL_TRIANGLES, len(cube_indices), GL_UNSIGNED_INT, None)

    # draw green quad
    model_2 = pyrr.matrix44.create_from_translation(pyrr.Vector3([0.5, -3.0, 0.0]))
    color_2 = pyrr.Vector4([0.0, 1.0, 0.0, 0.2])

    glUniformMatrix4fv(model_loc_t, 1, GL_FALSE, model_2)
    glUniformMatrix4fv(view_loc_t, 1, GL_FALSE, view)
    glUniformMatrix4fv(project_loc_t, 1, GL_FALSE, proj)

    glUniform4fv(col_loc_t, 1, color_2)
    glBindVertexArray(cubeVAO)
    glDrawElements(GL_TRIANGLES, len(cube_indices), GL_UNSIGNED_INT, None)

    # draw blue quad
    model_3 = pyrr.matrix44.create_from_translation(pyrr.Vector3([0.75, 1.5, 0.0]))
    color_3 = pyrr.Vector4([0.0, 0.0, 1.0, 0.2])

    glUniformMatrix4fv(model_loc_t, 1, GL_FALSE, model_3)
    glUniformMatrix4fv(view_loc_t, 1, GL_FALSE, view)
    glUniformMatrix4fv(project_loc_t, 1, GL_FALSE, proj)

    glUniform4fv(col_loc_t, 1, color_3)
    glBindVertexArray(cubeVAO)
    glDrawElements(GL_TRIANGLES, len(cube_indices), GL_UNSIGNED_INT, None)

    # draw yellow quad
    model_4 = pyrr.matrix44.create_from_translation(pyrr.Vector3([0.0, 3.0, 0.0]))
    color_4 = pyrr.Vector4([1.0, 0.5, 0.0, 0.2])

    glUniformMatrix4fv(model_loc_t, 1, GL_FALSE, model_4)
    glUniformMatrix4fv(view_loc_t, 1, GL_FALSE, view)
    glUniformMatrix4fv(project_loc_t, 1, GL_FALSE, proj)

    glUniform4fv(col_loc_t, 1, color_4)
    glBindVertexArray(cubeVAO)
    glDrawElements(GL_TRIANGLES, len(cube_indices), GL_UNSIGNED_INT, None)

    # ------------------ Draw composite image (composite pass) ------------------
    # set render states
    glDepthFunc(GL_ALWAYS)
    glEnable(GL_BLEND)
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)

    # Bind opaque framebuffer
    glBindFramebuffer(GL_FRAMEBUFFER, opaqueFBO)

    # Use composite shader
    glUseProgram(compo_shader)

    # draw screen quad
    glActiveTexture(GL_TEXTURE0)
    glBindTexture(GL_TEXTURE_2D, accum_texture)
    glUniform1i(accum_loc_c, 0)

    glActiveTexture(GL_TEXTURE1)
    glBindTexture(GL_TEXTURE_2D, reveal_texture)
    glUniform1i(reveal_loc_c, 1)

    glBindVertexArray(screenVAO)
    glDrawArrays(GL_TRIANGLES, 0, 6)

    # set render states
    glDisable(GL_DEPTH_TEST)
    glDepthMask(
        GL_TRUE
    )  # enable depth writes so glClear won't ignore clearing the depth buffer
    glDisable(GL_BLEND)

    # bind backbuffer
    glBindFramebuffer(GL_FRAMEBUFFER, 0)
    glClearColor(0.0, 0.0, 0.0, 0.0)
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT | GL_STENCIL_BUFFER_BIT)

    # use screen shader
    glUseProgram(screen_shader)

    # draw final screen quad
    glActiveTexture(GL_TEXTURE0)
    glBindTexture(GL_TEXTURE_2D, opaque_texture)
    glBindVertexArray(screenVAO)
    glDrawArrays(GL_TRIANGLES, 0, 6)

    glfw.poll_events()
    glfw.swap_buffers(window)


glfw.terminate()
