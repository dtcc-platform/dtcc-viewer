import glfw
from OpenGL.GL import *
from OpenGL.GL.shaders import compileProgram, compileShader
import numpy as np
import pyrr
from enum import Enum
import math


class Projection(Enum):
    Pespective = 1
    Orthographic = 2


window_w = 1200
window_h = 1000
proj = Projection.Orthographic

vertex_src = """
# version 330 core

layout(location = 0) in vec3 a_position; 
layout(location = 1) in vec3 a_color;

uniform mat4 model;
uniform mat4 project;
uniform mat4 view;

out vec3 v_color;
void main()
{
    gl_Position = project * model * view * vec4(a_position, 1.0);
    v_color = a_color;
}
"""

fragment_src = """
# version 330 core
in vec3 v_color;
out vec4 out_color;
void main()
{
    out_color = vec4(v_color, 1.0);
}
"""


# glfw callback function
def window_resize(window, width, height):
    glViewport(0, 0, width, height)
    project = pyrr.matrix44.create_perspective_projection(45, width / height, 0.1, 100)
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

glfw.set_window_size_callback(window, window_resize)

# Calls can be made after the contex is made current
glfw.make_context_current(window)

vertices = [
    -0.5,
    -0.5,
    0.5,
    1.0,
    0.0,
    1.0,
    0.5,
    -0.5,
    0.5,
    0.0,
    1.0,
    0.0,
    0.5,
    0.5,
    0.5,
    0.0,
    0.0,
    1.0,
    -0.5,
    0.5,
    0.5,
    1.0,
    1.0,
    1.0,
    -0.5,
    -0.5,
    -0.5,
    1.0,
    0.0,
    1.0,
    0.5,
    -0.5,
    -0.5,
    0.0,
    1.0,
    0.0,
    0.5,
    0.5,
    -0.5,
    0.0,
    0.0,
    1.0,
    -0.5,
    0.5,
    -0.5,
    1.0,
    1.0,
    1.0,
]

indices = [
    0,
    1,
    2,
    2,
    3,
    0,
    4,
    5,
    6,
    6,
    7,
    4,
    4,
    5,
    1,
    1,
    0,
    4,
    6,
    7,
    3,
    3,
    2,
    6,
    5,
    6,
    2,
    2,
    1,
    5,
    7,
    4,
    0,
    0,
    3,
    7,
]

vertices = np.array(vertices, dtype=np.float32)
indices = np.array(indices, dtype=np.uint32)


VAO = glGenVertexArrays(1)
glBindVertexArray(VAO)

# Vertex buffer
VBO = glGenBuffers(1)
glBindBuffer(GL_ARRAY_BUFFER, VBO)
glBufferData(
    GL_ARRAY_BUFFER, len(vertices) * 4, vertices, GL_STATIC_DRAW
)  # Second argument is nr of bytes

# Element buffer
EBO = glGenBuffers(1)
glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, EBO)
glBufferData(GL_ELEMENT_ARRAY_BUFFER, len(indices) * 4, indices, GL_STATIC_DRAW)


shader = compileProgram(
    compileShader(vertex_src, GL_VERTEX_SHADER),
    compileShader(fragment_src, GL_FRAGMENT_SHADER),
)

glEnableVertexAttribArray(0)  # 0 is the layout location for the vertex shader
glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, 24, ctypes.c_void_p(0))

glEnableVertexAttribArray(1)  # 1 is the layout location for the vertex shader
glVertexAttribPointer(1, 3, GL_FLOAT, GL_FALSE, 24, ctypes.c_void_p(12))

glUseProgram(shader)
glClearColor(0, 0.1, 0, 1)
glEnable(GL_DEPTH_TEST)

project = pyrr.matrix44.create_perspective_projection(45, window_w / window_h, 0.1, 100)
translate = pyrr.matrix44.create_from_translation(pyrr.Vector3([0, 0, 0]))
# eye position, target position, up vector
view = pyrr.matrix44.create_look_at(
    pyrr.Vector3([0, 3, 0]), pyrr.Vector3([0, 0, 0]), pyrr.Vector3([0, 0, 1])
)


model_loc = glGetUniformLocation(shader, "model")
project_loc = glGetUniformLocation(shader, "project")
view_loc = glGetUniformLocation(shader, "view")

# Only change when the window size changes
glUniformMatrix4fv(project_loc, 1, GL_FALSE, project)
glUniformMatrix4fv(model_loc, 1, GL_FALSE, translate)
glUniformMatrix4fv(view_loc, 1, GL_FALSE, view)


# Main application loop
while not glfw.window_should_close(window):
    glfw.poll_events()
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

    cam_x = math.sin(glfw.get_time()) * 4
    cam_y = math.cos(glfw.get_time()) * 4

    view = pyrr.matrix44.create_look_at(
        pyrr.Vector3([cam_x, cam_y, 1]),
        pyrr.Vector3([0, 0, 0]),
        pyrr.Vector3([0, 0, 1]),
    )

    glUniformMatrix4fv(view_loc, 1, GL_FALSE, view)

    glDrawElements(GL_TRIANGLES, len(indices), GL_UNSIGNED_INT, None)
    glfw.swap_buffers(window)


glfw.terminate()
