import glfw
from OpenGL.GL import *
from OpenGL.GL.shaders import compileProgram, compileShader
import numpy as np

vertex_src = """
# version 330 core
layout(location = 0) in vec3 a_position; 
layout(location = 1) in vec3 a_color;
out vec3 v_color;
void main()
{
    gl_Position = vec4(a_position, 1.0);
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

if not glfw.init():
    raise Exception("glfw can not be initialised!")

glfw.window_hint(glfw.CONTEXT_VERSION_MAJOR, 3)
glfw.window_hint(glfw.CONTEXT_VERSION_MINOR, 3)
glfw.window_hint(glfw.OPENGL_FORWARD_COMPAT, True)
glfw.window_hint(glfw.OPENGL_PROFILE, glfw.OPENGL_CORE_PROFILE)
window = glfw.create_window(1200, 1000, "OpenGL Window", None, None)  # Create window

if not window:
    glfw.terminate()
    raise Exception("glfw window can not be created!")

glfw.set_window_pos(window, 400, 200)

# Calls can be made after the contex is made current
glfw.make_context_current(window)

vertices = [
    -0.5,
    -0.5,
    0.0,
    1.0,
    0.0,
    1.0,
    0.5,
    -0.5,
    0.0,
    0.0,
    1.0,
    0.0,
    -0.5,
    0.5,
    0.0,
    0.0,
    0.0,
    1.0,
    0.5,
    0.5,
    0.0,
    1.0,
    1.0,
    1.0,
    0.0,
    0.75,
    0.0,
    1.0,
    1.0,
    0.0,
]

indices = [0, 1, 2, 1, 2, 3, 2, 3, 4]

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

# Main application loop
while not glfw.window_should_close(window):
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    glDrawElements(GL_TRIANGLES, len(indices), GL_UNSIGNED_INT, None)
    glfw.poll_events()
    glfw.swap_buffers(window)


glfw.terminate()
