import glfw
from OpenGL.GL import *
from OpenGL.GL.shaders import compileProgram, compileShader
import numpy as np
import pyrr
from PIL import Image
import pkg_resources

vertex_src = """
# version 330 core
layout(location = 0) in vec3 a_position; 
layout(location = 1) in vec3 a_color;
layout(location = 2) in vec2 a_texture;

uniform mat4 rotation;

out vec3 v_color;
out vec2 v_texture;

void main()
{
    gl_Position = rotation * vec4(a_position, 1.0);
    v_color = a_color;
    v_texture = a_texture;
}
"""

fragment_src = """
# version 330 core
in vec3 v_color;
in vec2 v_texture;

out vec4 out_color;

uniform sampler2D s_texture;

void main()
{
    out_color = texture(s_texture, v_texture);  // * vec4(v_color, 1.0);
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
    0.5,
    1.0,
    0.0,
    1.0,
    0.0,
    0.0,
    0.5,
    -0.5,
    0.5,
    0.0,
    1.0,
    0.0,
    1.0,
    0.0,
    0.5,
    0.5,
    0.5,
    0.0,
    0.0,
    1.0,
    1.0,
    1.0,
    -0.5,
    0.5,
    0.5,
    1.0,
    1.0,
    1.0,
    0.0,
    1.0,
    -0.5,
    -0.5,
    -0.5,
    1.0,
    0.0,
    1.0,
    0.0,
    0.0,
    0.5,
    -0.5,
    -0.5,
    0.0,
    1.0,
    0.0,
    1.0,
    0.0,
    0.5,
    0.5,
    -0.5,
    0.0,
    0.0,
    1.0,
    1.0,
    1.0,
    -0.5,
    0.5,
    -0.5,
    1.0,
    1.0,
    1.0,
    0.0,
    1.0,
    0.5,
    -0.5,
    -0.5,
    1.0,
    0.0,
    1.0,
    0.0,
    0.0,
    0.5,
    0.5,
    -0.5,
    0.0,
    1.0,
    0.0,
    1.0,
    0.0,
    0.5,
    0.5,
    0.5,
    0.0,
    0.0,
    1.0,
    1.0,
    1.0,
    0.5,
    -0.5,
    0.5,
    1.0,
    1.0,
    1.0,
    0.0,
    1.0,
    -0.5,
    0.5,
    -0.5,
    1.0,
    0.0,
    1.0,
    0.0,
    0.0,
    -0.5,
    -0.5,
    -0.5,
    0.0,
    1.0,
    0.0,
    1.0,
    0.0,
    -0.5,
    -0.5,
    0.5,
    0.0,
    0.0,
    1.0,
    1.0,
    1.0,
    -0.5,
    0.5,
    0.5,
    1.0,
    1.0,
    1.0,
    0.0,
    1.0,
    -0.5,
    -0.5,
    -0.5,
    1.0,
    0.0,
    1.0,
    0.0,
    0.0,
    0.5,
    -0.5,
    -0.5,
    0.0,
    1.0,
    0.0,
    1.0,
    0.0,
    0.5,
    -0.5,
    0.5,
    0.0,
    0.0,
    1.0,
    1.0,
    1.0,
    -0.5,
    -0.5,
    0.5,
    1.0,
    1.0,
    1.0,
    0.0,
    1.0,
    0.5,
    0.5,
    -0.5,
    1.0,
    0.0,
    1.0,
    0.0,
    0.0,
    -0.5,
    0.5,
    -0.5,
    0.0,
    1.0,
    0.0,
    1.0,
    0.0,
    -0.5,
    0.5,
    0.5,
    0.0,
    0.0,
    1.0,
    1.0,
    1.0,
    0.5,
    0.5,
    0.5,
    1.0,
    1.0,
    1.0,
    0.0,
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
    8,
    9,
    10,
    10,
    11,
    8,
    12,
    13,
    14,
    14,
    15,
    12,
    16,
    17,
    18,
    18,
    19,
    16,
    20,
    21,
    22,
    22,
    23,
    20,
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
glVertexAttribPointer(
    0, 3, GL_FLOAT, GL_FALSE, vertices.itemsize * 8, ctypes.c_void_p(0)
)  # 0 is layout location, 3 is vec3

glEnableVertexAttribArray(1)  # 1 is the layout location for the vertex shader
glVertexAttribPointer(
    1, 3, GL_FLOAT, GL_FALSE, vertices.itemsize * 8, ctypes.c_void_p(12)
)  # 1 is layout location, 3 is vec3

glEnableVertexAttribArray(2)  # 1 is the layout location for the vertex shader
glVertexAttribPointer(
    2, 2, GL_FLOAT, GL_FALSE, vertices.itemsize * 8, ctypes.c_void_p(24)
)  # 2 is layout location, 2 is vec2

texture = glGenTextures(1)
glBindTexture(GL_TEXTURE_2D, texture)

# Set the texture wrapping parameters
glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_REPEAT)
glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_REPEAT)

# Set the texture filtering parameters
glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)

# Load image
image = Image.open("data/sky_square.png")
image = image.transpose(
    Image.FLIP_TOP_BOTTOM
)  # Image coordinates start at the top left corner, while opengl starts at lower left.
image_data = image.convert("RGBA").tobytes()
image_data = np.array(list(image.getdata()), np.int8)

# ts = pkg_resources.resource_stream(__name__,'data/sky_square.png')
# image = Image.open(ts).convert('RGBA')
# image_data = np.array(list(image.getdata()), np.uint8)

glTexImage2D(
    GL_TEXTURE,
    0,
    GL_RGBA,
    image.width,
    image.height,
    0,
    GL_RGBA,
    GL_UNSIGNED_BYTE,
    image_data,
)

glUseProgram(shader)
glClearColor(0, 0.1, 0, 1)
glEnable(GL_DEPTH_TEST)
rotation_loc = glGetUniformLocation(shader, "rotation")


# Main application loop
while not glfw.window_should_close(window):
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    rot_x = pyrr.Matrix44.from_x_rotation(0.5 * glfw.get_time())
    rot_y = pyrr.Matrix44.from_y_rotation(0.8 * glfw.get_time())

    glUniformMatrix4fv(rotation_loc, 1, GL_FALSE, pyrr.matrix44.multiply(rot_x * rot_y))
    glDrawElements(GL_TRIANGLES, len(indices), GL_UNSIGNED_INT, None)
    glfw.poll_events()
    glfw.swap_buffers(window)


glfw.terminate()
