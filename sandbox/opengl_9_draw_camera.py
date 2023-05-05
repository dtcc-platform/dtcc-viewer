import glfw
from OpenGL.GL import *
from OpenGL.GL.shaders import compileProgram, compileShader
import numpy as np
import pyrr
from pprint import pp
from enum import Enum
import math
from obj_loader import ObjLoader
from camera import Camera

class Projection(Enum):
    Pespective = 1
    Orthographic = 2

class KeyAction(Enum):
    NONE = 1
    mouse = 2
    keyboard = 3    

WIDTH = 1200
HEIGHT = 1000
last_x = WIDTH/2.0 
last_y = HEIGHT/2.0
first_mouse = True
camera = Camera(float(WIDTH)/float(HEIGHT))

left_mbtn_pressed = False

def key_input_callback(window, key, scancode, action, mode):
    if key == glfw.KEY_ESCAPE and action == glfw.PRESS:
        glfw.set_window_should_close(window, True)

def scroll_input_callback(window, xoffset, yoffset):
    camera.distance_to_target += yoffset
    camera.process_mouse_movement(xoffset, yoffset) 
    pass

def mouse_input_callback(window, button, action, mod):  
    global left_mbtn_pressed
    global first_mouse
    if button == glfw.MOUSE_BUTTON_LEFT and action == glfw.PRESS:
        left_mbtn_pressed = True
    elif button == glfw.MOUSE_BUTTON_LEFT and action == glfw.RELEASE:
        left_mbtn_pressed = False
        first_mouse = True
    
def mouse_look_callback(window, xpos, ypos):
    global last_x
    global last_y
    global first_mouse

    if(left_mbtn_pressed):
        if first_mouse:
            last_x = xpos
            last_y = ypos
            first_mouse = False

        xoffset = xpos - last_x
        yoffset = last_y - ypos
        last_x = xpos
        last_y = ypos
        camera.process_mouse_movement(xoffset, yoffset)


vertex_src = """
# version 330 core

layout(location = 0) in vec3 a_position; 
layout(location = 1) in vec3 a_color;
layout(location = 2) in vec3 a_normal;

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
    camera.aspect_ratio = width / height
    proj = camera.get_perspective_matrix()
    glUniformMatrix4fv(project_loc, 1, GL_FALSE, proj)
    

if not glfw.init():
    raise Exception("glfw can not be initialised!")
    
glfw.window_hint(glfw.CONTEXT_VERSION_MAJOR, 3)
glfw.window_hint(glfw.CONTEXT_VERSION_MINOR, 3)
glfw.window_hint(glfw.OPENGL_FORWARD_COMPAT, True)
glfw.window_hint(glfw.OPENGL_PROFILE, glfw.OPENGL_CORE_PROFILE)
window = glfw.create_window(WIDTH, HEIGHT, "OpenGL Window", None, None)      # Create window

if not window:
    glfw.terminate()
    raise Exception("glfw window can not be created!")
    
glfw.set_window_pos(window, 400, 200)
glfw.set_window_size_callback(window, window_resize)
glfw.set_cursor_pos_callback(window, mouse_look_callback)
glfw.set_key_callback(window, key_input_callback)
glfw.set_mouse_button_callback(window, mouse_input_callback)
glfw.set_scroll_callback(window, scroll_input_callback)

# Calls can be made after the contex is made current
glfw.make_context_current(window)

#[face_indices, vert_coord, vert_color, vertices] = ObjLoader.load_model("./data/simple_city_2_color.obj")
[face_indices, vert_coord, vert_color, vertices] = ObjLoader.load_model("./data/simple_city_dense.obj")

# Generating VAO. Any subsequent vertex attribute calls will be stored in the VAO if it is bound.
VAO = glGenVertexArrays(1)
glBindVertexArray(VAO)

# Vertex buffer
VBO = glGenBuffers(1)
glBindBuffer(GL_ARRAY_BUFFER, VBO)
glBufferData(GL_ARRAY_BUFFER, len(vertices) * 4, vertices, GL_STATIC_DRAW) # Second argument is nr of bytes

# Element buffer
EBO = glGenBuffers(1)
glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, EBO)
glBufferData(GL_ELEMENT_ARRAY_BUFFER, len(face_indices)* 4, face_indices, GL_STATIC_DRAW)

shader = compileProgram(compileShader(vertex_src, GL_VERTEX_SHADER), compileShader(fragment_src, GL_FRAGMENT_SHADER))

glEnableVertexAttribArray(0) # 0 is the layout location for the vertex shader
glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, 24, ctypes.c_void_p(0))

glEnableVertexAttribArray(1) # 1 is the layout location for the vertex shader
glVertexAttribPointer(1, 3, GL_FLOAT, GL_FALSE, 24, ctypes.c_void_p(12))

glUseProgram(shader)
glClearColor(0, 0.1, 0, 1)
glEnable(GL_DEPTH_TEST)

proj = camera.get_perspective_matrix()
trans = pyrr.matrix44.create_from_translation(pyrr.Vector3([0, 0, 0]))
#project = pyrr.matrix44.create_perspective_projection(45, WIDTH / HEIGHT, 0.1, 100)

model_loc = glGetUniformLocation(shader, "model")
project_loc = glGetUniformLocation(shader, "project")
view_loc = glGetUniformLocation(shader, "view")

glUniformMatrix4fv(project_loc, 1, GL_FALSE, proj)
glUniformMatrix4fv(model_loc, 1, GL_FALSE, trans)

# Main application loop
while not glfw.window_should_close(window):
    glfw.poll_events()
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

    proj = camera.get_perspective_matrix()
    glUniformMatrix4fv(project_loc, 1, GL_FALSE, proj)
    
    view = camera.get_view_matrix()
    glUniformMatrix4fv(view_loc, 1, GL_FALSE, view)

    glDrawElements(GL_TRIANGLES, len(face_indices), GL_UNSIGNED_INT, None)
    glfw.swap_buffers(window)


glfw.terminate()    