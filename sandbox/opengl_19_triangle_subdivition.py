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

vs = """
#version 330 core

layout(location=0) in vec3 a_position;

void main() 
{
    gl_Position =  vec4(a_position, 1);
}
"""

gs = """ 
#version 330 core

layout (triangles) in;
layout (triangle_strip, max_vertices=256) out; 
uniform int sub_divisions;

uniform mat4 model;
uniform mat4 view;
uniform mat4 project;

void main() 
{
    vec4 v0 = gl_in[0].gl_Position;
    vec4 v1 = gl_in[1].gl_Position;
    vec4 v2 = gl_in[2].gl_Position;
    float dx = abs(v0.x-v2.x)/sub_divisions;
    float dy = abs(v0.y-v1.y)/sub_divisions;
    float x=v0.x;
    float y=v0.y;

    mat4 mvp = project * view * model;

    for(int j=0;j<sub_divisions*sub_divisions;j++) 
    {
        gl_Position =  mvp * vec4(x, y, 0, 1);
        EmitVertex();
        gl_Position =  mvp * vec4(x, y+dy, 0, 1);
        EmitVertex();
        gl_Position =  mvp * vec4(x+dx, y, 0, 1);
        EmitVertex();
        gl_Position =  mvp * vec4(x+dx, y+dy, 0, 1);
        EmitVertex();
        EndPrimitive();
        x+=dx;
        
        if((j+1) %sub_divisions == 0) 
        {
            x=v0.x;
            y+=dy;
        }
    }
}
"""

fs = """ 
#version 330 core

layout(location=0) out vec4 FragColor;

void main() 
{
    FragColor = vec4(1,0,1,1);
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

size = 50

vertices = [-size, -size, 0, -size, size, 0, size, size, 0, size, -size, 0]
indices = [0, 1, 2, 0, 2, 3]

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
glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, 12, ctypes.c_void_p(0))


# ---------------- NORMAL SHADER ---------------------#

shader = compileProgram(
    compileShader(vs, GL_VERTEX_SHADER),
    compileShader(gs, GL_GEOMETRY_SHADER),
    compileShader(fs, GL_FRAGMENT_SHADER),
)

glUseProgram(shader)

model_loc = glGetUniformLocation(shader, "model")
view_loc = glGetUniformLocation(shader, "view")
project_loc = glGetUniformLocation(shader, "project")
subdee_loc = glGetUniformLocation(shader, "sub_divisions")

glUseProgram(shader)
glClearColor(0, 0, 0, 1)
glEnable(GL_DEPTH_TEST)

glEnable(GL_BLEND)
glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)

fb_size = glfw.get_framebuffer_size(window)
mac_window_w = fb_size[0]
mac_window_h = fb_size[1]

view_selection_colors = False

counter = 0
subdee = 1

glPolygonMode(GL_FRONT_AND_BACK, GL_LINE)

# Main application loop
while not glfw.window_should_close(window):
    glfw.poll_events()
    time = glfw.get_time()

    counter += 1

    if counter % 100 == 0:
        subdee += 1

    if counter % 1000 == 0:
        subdee = 1
        counter = 0

    # Clearing the default framebuffer
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

    # Camera input
    model = action.camera.get_move_matrix()
    view = action.camera._get_perspective_view_matrix()
    proj = action.camera._get_perspective_matrix()

    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    glUseProgram(shader)

    # Set uniforms
    glUniformMatrix4fv(model_loc, 1, GL_FALSE, model)
    glUniformMatrix4fv(view_loc, 1, GL_FALSE, view)
    glUniformMatrix4fv(project_loc, 1, GL_FALSE, proj)
    glUniform1i(subdee_loc, subdee)

    glBindVertexArray(VAO_debug)
    glDrawElements(GL_TRIANGLES, len(indices), GL_UNSIGNED_INT, None)

    glfw.swap_buffers(window)

glfw.terminate()
