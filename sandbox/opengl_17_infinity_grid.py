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

window_w = 800
window_h = 800

action = Action(window_w, window_h)

vs_normal = """
# version 330 core

layout(location = 0) in vec3 a_position; 
layout(location = 1) in vec3 a_tex_coords;

uniform mat4 model;
uniform mat4 view;
uniform mat4 project;

out vec3 v_frag_pos;
out vec3 v_color;

void main()
{
    gl_Position = project * view * model * vec4(a_position, 1.0);
    v_frag_pos = vec3(model * vec4(a_position, 1.0));
    v_color = vec3(1,0,1);
}
"""

fs_normal = """ 
# version 330 core

in vec3 v_frag_pos;
in vec3 v_color;

out vec4 frag_color;

uniform vec2 u_resolution;

void main()
{
    vec2 st = gl_FragCoord.xy / u_resolution.xy;
    vec2 left_bottom = step(0.3, st);
    vec2 right_top = step(0.3, 1.0 - st);

    vec3 canvas = vec3(1.0, 0.0, 0.0) * (left_bottom.x * left_bottom.y * right_top.x * right_top.y);

	frag_color = vec4(canvas, 1.0);
}
"""

vs_checkb = """ 
# version 330 core

layout (location = 0) in vec3 aPos;
layout (location = 1) in vec2 aTexCoord;

out vec2 TexCoord;

uniform mat4 model;
uniform mat4 view;
uniform mat4 project;

void main()
{
    gl_Position = project * view * model * vec4(aPos, 1.0);
    TexCoord = aTexCoord;
}
"""


fs_checkb = """
# version 330 core

in vec2 TexCoord;
out vec4 FragColor;

vec3 color1 = vec3(0.0, 0.0, 0.0);
vec3 color2 = vec3(1.0, 1.0, 1.0);
float tileSize = 0.01;

void main()
{
    int x = int(TexCoord.x / tileSize);
    int y = int(TexCoord.y / tileSize);
    int sum = x + y;
    if (sum % 2 == 0)
        FragColor = vec4(color1, 1.0);
    else
        FragColor = vec4(color2, 0.0);
}
"""

fs_grid = """ 
#version 330 core

in vec2 TexCoord;
out vec4 FragColor;

float gridLineCountX = 10; // Number of grid lines in the X direction
float gridLineCountY = 10; // Number of grid lines in the Y direction
float gridLineWidth = 0.02;  // Width of the grid lines
vec3 lineColor = vec3(0, 0, 0);       // Color of the grid lines

void main()
{
    // Calculate the distance to the nearest grid line in the X direction
    float distToGridX = mod(TexCoord.x * gridLineCountX, 1.0) * 2.0 - 1.0;
    
    // Calculate the distance to the nearest grid line in the Y direction
    float distToGridY = mod(TexCoord.y * gridLineCountY, 1.0) * 2.0 - 1.0;
    
    // Check if the fragment is close to a grid line in either direction
    bool isGridLineX = abs(distToGridX) < gridLineWidth;
    bool isGridLineY = abs(distToGridY) < gridLineWidth;
    
    // Check if the fragment is part of a grid line
    if (isGridLineX || isGridLineY)
    {
        // Set color to grid line color
        FragColor = vec4(lineColor, 1.0);
    }
    else
    {
        // Set color to transparent
        discard;
    }
}
"""

fs_grid_2 = """ 
#version 330 core

in vec2 TexCoord;
out vec4 FragColor;

float gridLineCountX = 100; // Number of grid lines in the X direction
float gridLineCountY = 100; // Number of grid lines in the Y direction
float gridLineWidth = 0.05; // Width of the grid lines
vec3 lineColor = vec3(0, 0, 0); // Color of the grid lines
float aa = 1.0/20.0; // Anti-aliasing factor

void main()
{
    // Calculate the distance to the nearest grid line in the X direction
    float distToGridX = mod(TexCoord.x * gridLineCountX, 1.0) * 2.0 - 1.0;
    
    // Calculate the distance to the nearest grid line in the Y direction
    float distToGridY = mod(TexCoord.y * gridLineCountY, 1.0) * 2.0 - 1.0;
    
    // Apply anti-aliasing to the grid lines
    float smoothX = smoothstep(0, gridLineWidth, abs(distToGridX));
    float smoothY = smoothstep(0, gridLineWidth, abs(distToGridY));
    
    // Calculate the alpha value based on the minimum of the smoothstep factors
    float alpha = 1.0 - min(smoothX, smoothY);
    
    // Check if the fragment is part of a grid line or a grid square
    bool isGridLineX = abs(distToGridX) < gridLineWidth;
    bool isGridLineY = abs(distToGridY) < gridLineWidth;
    
    // Set color to grid line color with alpha value
    FragColor = vec4(lineColor, isGridLineX || isGridLineY ? alpha : 0.0);
}
"""


# glfw callback function
def window_resize(window, width, height):
    global window_w
    global window_h
    window_w = width
    window_h = height
    fb_size = glfw.get_framebuffer_size(window)
    glViewport(0, 0, width, height)
    global action
    action.update_window_size(fb_size[0], fb_size[1], width, height)
    project = action.camera._get_perspective_matrix()
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

size = 100
floor_z = -2.0

tex_min = 0
tex_max = 1

(vertices, indices) = get_quad(size, tex_min, tex_max)


# ---------------- DEBUG QUAD ---------------------#

vertices = np.array(vertices, dtype=np.float32)
indices = np.array(indices, dtype=np.uint32)

VAO_debug = glGenVertexArrays(1)
glBindVertexArray(VAO_debug)

# Vertex buffer
VBO_debug = glGenBuffers(1)
glBindBuffer(GL_ARRAY_BUFFER, VBO_debug)
glBufferData(
    GL_ARRAY_BUFFER, len(vertices) * 4, vertices, GL_STATIC_DRAW
)  # Second argument is nr of bytes

# Element buffer
EBO_debug = glGenBuffers(1)
glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, EBO_debug)
glBufferData(GL_ELEMENT_ARRAY_BUFFER, len(indices) * 4, indices, GL_STATIC_DRAW)

# Position
glEnableVertexAttribArray(0)  # 0 is the layout location for the vertex shader
glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, 20, ctypes.c_void_p(0))

# Texture coordinates
glEnableVertexAttribArray(1)  # 1 is the layout location for the vertex shader
glVertexAttribPointer(1, 2, GL_FLOAT, GL_FALSE, 20, ctypes.c_void_p(12))

# ---------------- NORMAL SHADER ---------------------#

shader_normal = compileProgram(
    compileShader(vs_checkb, GL_VERTEX_SHADER),
    compileShader(fs_grid_2, GL_FRAGMENT_SHADER),
)

glUseProgram(shader_normal)

model_loc = glGetUniformLocation(shader_normal, "model")
view_loc = glGetUniformLocation(shader_normal, "view")
project_loc = glGetUniformLocation(shader_normal, "project")

glUseProgram(shader_normal)
glClearColor(0.5, 0.5, 0.5, 1)
glEnable(GL_DEPTH_TEST)

glEnable(GL_BLEND)
glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)

fb_size = glfw.get_framebuffer_size(window)
mac_window_w = fb_size[0]
mac_window_h = fb_size[1]

view_selection_colors = False

# Main application loop
while not glfw.window_should_close(window):
    glfw.poll_events()
    time = glfw.get_time()
    # Clearing the default framebuffer
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

    # Camera input
    model = action.camera.get_move_matrix()
    view = action.camera._get_perspective_view_matrix()
    proj = action.camera._get_perspective_matrix()

    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    glUseProgram(shader_normal)

    # Set uniforms
    glUniformMatrix4fv(model_loc, 1, GL_FALSE, model)
    glUniformMatrix4fv(view_loc, 1, GL_FALSE, view)
    glUniformMatrix4fv(project_loc, 1, GL_FALSE, proj)

    glBindVertexArray(VAO_debug)
    glDrawElements(GL_TRIANGLES, len(indices), GL_UNSIGNED_INT, None)

    glfw.swap_buffers(window)

glfw.terminate()
