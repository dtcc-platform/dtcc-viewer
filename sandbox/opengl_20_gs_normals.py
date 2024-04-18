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

vs_normals = """
#version 330 core

layout(location=0) in vec3 a_position;
layout(location=1) in vec3 a_color;
layout(location=2) in vec3 a_normal;

out vec3 normal;

void main() 
{
    gl_Position = vec4(a_position, 1);
    normal = a_normal;
}
"""

gs_normals_vertex = """ 
#version 330 core

layout(triangles) in;
layout(line_strip, max_vertices = 6) out;

uniform mat4 model;
uniform mat4 view;
uniform mat4 project;

in vec3 normal[];

void main() 
{
    mat4 mvp = project * view * model;

    for (int i = 0; i < 3; i++) {
 
        // Draw a line from the vertex to represent the normal
        
        vec4 startPos = mvp * gl_in[i].gl_Position;
        gl_Position = startPos; 
        EmitVertex();

        vec3 vertexNormal = normal[i];
        vec3 vertexPos = gl_in[i].gl_Position.xyz;

        vec4 endPos = mvp * vec4((vertexPos + vertexNormal), 1.0);
        gl_Position = endPos;
        EmitVertex();

        EndPrimitive();
    }
}
"""

gs_normals_face = """ 
#version 330 core

layout(triangles) in;
layout(line_strip, max_vertices = 2) out;

uniform mat4 model;
uniform mat4 view;
uniform mat4 project;

in vec3 normal[];

void main() 
{
    mat4 mvp = project * view * model;

    vec4 faceAverage = (gl_in[0].gl_Position + gl_in[1].gl_Position + gl_in[2].gl_Position) / 3.0;
    
    vec3 faceCenter = faceAverage.xyz;

    vec4 lineStart = mvp *  vec4(faceCenter, 1.0);
    gl_Position = lineStart;
    EmitVertex();

    vec3 faceNormal = (normal[0] + normal[1] + normal[2]) / 3.0; 

    vec4 lineEnd = mvp * vec4((faceCenter + faceNormal), 1.0);
    gl_Position = lineEnd;
    EmitVertex();

    EndPrimitive();
}
"""

fs_normals = """ 
#version 330 core

layout(location=0) out vec4 FragColor;

void main() 
{
    FragColor = vec4(1,0,1,1);
}
"""

vs_mesh = """
#version 330 core

layout(location=0) in vec3 a_position;
layout(location=1) in vec3 a_color;
layout(location=2) in vec3 a_normal;

uniform mat4 model;
uniform mat4 view;
uniform mat4 project;

out vec3 color;

void main() 
{
    gl_Position = project * view * model * vec4(a_position, 1);
    color = a_color;
}
"""


fs_mesh = """ 
#version 330 core

layout(location=0) out vec4 FragColor;

in vec3 color;

void main() 
{
    FragColor = vec4(color,1);
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
    glUniformMatrix4fv(ploc_m, 1, GL_FALSE, project)


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

# get vertices with structure v = (x, y, z, r, g, b, nx, ny, nz)
# (vertices, indices) = get_city_model(sub_x=[-0.05, 0.05], sub_y=[-0.05, 0.05])

(vertices, indices) = get_city_model()


minx = np.min(vertices[0::9])
maxx = np.max(vertices[0::9])
normx = (vertices[0::9] - minx) / (maxx - minx)

minz = np.min(vertices[2::9])
maxz = np.max(vertices[2::9])
normz = (vertices[2::9] - minz) / (maxz - minz)

vertices[3::9] = normx
vertices[5::9] = normz


# ---------------- VAO ---------------------#

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

# Position
glEnableVertexAttribArray(0)  # 0 is the layout location for the vertex shader
glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, 36, ctypes.c_void_p(0))

# Color
glEnableVertexAttribArray(1)  # 0 is the layout location for the vertex shader
glVertexAttribPointer(1, 3, GL_FLOAT, GL_FALSE, 36, ctypes.c_void_p(12))

# Normals
glEnableVertexAttribArray(2)  # 0 is the layout location for the vertex shader
glVertexAttribPointer(2, 3, GL_FLOAT, GL_FALSE, 36, ctypes.c_void_p(24))


# ----------------- SHADER FOR NORMALS ---------------------#

shader_normals = compileProgram(
    compileShader(vs_normals, GL_VERTEX_SHADER),
    compileShader(gs_normals_face, GL_GEOMETRY_SHADER),
    compileShader(fs_normals, GL_FRAGMENT_SHADER),
)

glUseProgram(shader_normals)

mloc_n = glGetUniformLocation(shader_normals, "model")
vloc_n = glGetUniformLocation(shader_normals, "view")
ploc_n = glGetUniformLocation(shader_normals, "project")


# ------------------- SHADER FOR MESH ----------------------#

shader_mesh = compileProgram(
    compileShader(vs_mesh, GL_VERTEX_SHADER),
    compileShader(fs_mesh, GL_FRAGMENT_SHADER),
)

glUseProgram(shader_mesh)

mloc_m = glGetUniformLocation(shader_mesh, "model")
vloc_m = glGetUniformLocation(shader_mesh, "view")
ploc_m = glGetUniformLocation(shader_mesh, "project")

# ----------------------------------------------------------#

glClearColor(0, 0, 0, 1)
glEnable(GL_DEPTH_TEST)

glEnable(GL_BLEND)
glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)

fb_size = glfw.get_framebuffer_size(window)
mac_window_w = fb_size[0]
mac_window_h = fb_size[1]


glPolygonMode(GL_FRONT_AND_BACK, GL_LINE)

# Main application loop
while not glfw.window_should_close(window):
    glfw.poll_events()

    # Clearing the default framebuffer
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

    # Camera input
    model = action.camera.get_move_matrix()
    view = action.camera._get_perspective_view_matrix()
    proj = action.camera._get_perspective_matrix()

    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

    # Draw the mesh
    glUseProgram(shader_mesh)
    glUniformMatrix4fv(mloc_m, 1, GL_FALSE, model)
    glUniformMatrix4fv(vloc_m, 1, GL_FALSE, view)
    glUniformMatrix4fv(ploc_m, 1, GL_FALSE, proj)

    glBindVertexArray(VAO)
    glDrawElements(GL_TRIANGLES, len(indices), GL_UNSIGNED_INT, None)

    # Draw the normals
    glUseProgram(shader_normals)
    glUniformMatrix4fv(mloc_n, 1, GL_FALSE, model)
    glUniformMatrix4fv(vloc_n, 1, GL_FALSE, view)
    glUniformMatrix4fv(ploc_n, 1, GL_FALSE, proj)

    glBindVertexArray(VAO)
    glDrawElements(GL_TRIANGLES, len(indices), GL_UNSIGNED_INT, None)

    glfw.swap_buffers(window)

glfw.terminate()
