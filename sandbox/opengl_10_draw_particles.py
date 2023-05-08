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
layout(location = 2) in vec3 a_offset;

uniform mat4 model;
uniform mat4 project;
uniform mat4 view;

out vec3 v_color;
void main()
{   
    vec4 bill_pos = model * vec4(a_position, 1.0);
    vec4 final_pos = bill_pos + vec4(a_offset, 0.0);
    gl_Position = project * view * final_pos;
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


#vec3 final_pos = a_position + a_offset;
#gl_Position = project * view * model * vec4(final_pos, 1.0);
#v_color = a_color;

# glfw callback function
def window_resize(window, width, height):
    glViewport(0, 0, width, height)
    camera.aspect_ratio = width / height
    proj = camera.get_perspective_matrix()
    glUniformMatrix4fv(project_loc, 1, GL_FALSE, proj)
    

def fps_calculations(prev_time, time_acum, fps, print_results = True):
    new_time = glfw.get_time()
    time_passed = new_time - prev_time
    prev_time = new_time
    time_acum += time_passed
    fps += 1

    if(time_acum > 1):
        time_acum = 0
        if(print_results):
            print("FPS:" + str(fps))
        fps = 0

    return prev_time, time_acum, fps    

def get_billborad_transform():

    dir_from_camera = pyrr.Vector3([0,0,0]) - camera.camera_pos
    angle1 = np.arctan2(-dir_from_camera[1], dir_from_camera[0])        # arctan(dy/dx)
    dist2d = math.sqrt(dir_from_camera[0]**2 + dir_from_camera[1]**2)   # sqrt(dx^2 + dy^2)
    angle2 = np.arctan2(dir_from_camera[2], dist2d)                     # angle around vertical axis

    model_transform = pyrr.matrix44.create_identity(dtype=np.float32)
    model_transform = pyrr.matrix44.multiply(model_transform, pyrr.matrix44.create_from_y_rotation(theta=angle2, dtype=np.float32))
    model_transform = pyrr.matrix44.multiply(model_transform, pyrr.matrix44.create_from_z_rotation(theta=angle1, dtype=np.float32))

    return model_transform

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
#[face_indices, vert_coord, vert_color, vertices] = ObjLoader.load_model("./data/simple_city_dense.obj")

square_size = 0.1

vertices = [ 0, -square_size,  -square_size, 1.0, 0.0, 1.0, 
             0, -square_size,   square_size, 0.0, 1.0, 0.0, 
             0,  square_size,   square_size, 0.0, 0.0, 1.0,
             0,  square_size,  -square_size, 1.0, 1.0, 1.0]

face_indices = [0, 1, 2, 2, 3, 0]

"""
vertices = [ -cube_size, -cube_size,  cube_size, 1.0, 0.0, 1.0, 
              cube_size, -cube_size,  cube_size, 0.0, 1.0, 0.0, 
              cube_size,  cube_size,  cube_size, 0.0, 0.0, 1.0,
             -cube_size,  cube_size,  cube_size, 1.0, 1.0, 1.0,

             -cube_size, -cube_size, -cube_size, 1.0, 0.0, 1.0, 
              cube_size, -cube_size, -cube_size, 0.0, 1.0, 0.0, 
              cube_size,  cube_size, -cube_size, 0.0, 0.0, 1.0,
             -cube_size,  cube_size, -cube_size, 1.0, 1.0, 1.0]

face_indices = [0, 1, 2, 2, 3, 0,
                4, 5, 6, 6, 7, 4,
                4, 5, 1, 1, 0, 4,
                6, 7, 3, 3, 2, 6,
                5, 6, 2, 2, 1, 5,
                7, 4, 0, 0, 3, 7]
"""

vertices = np.array(vertices, dtype=np.float32)
face_indices = np.array(face_indices, dtype=np.uint32)       

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

# Instance VBO
instance_array = []
offset = 0.05
size = 100

for z in range(-size, size+1, 1):
    for y in range(-size, size+1, 1):
        for x in range(-size, size+1, 1):
            translation = pyrr.Vector3([0.0, 0.0, 0.0])
            translation.x = x + offset
            translation.y = y + offset
            translation.z = z + offset
            instance_array.append(translation)

n_instances = len(instance_array)
instance_array = np.array(instance_array, np.float32).flatten() 
print("Number of instances: " +str(n_instances))           

instance_VBO = glGenBuffers(1)
glBindBuffer(GL_ARRAY_BUFFER, instance_VBO)
glBufferData(GL_ARRAY_BUFFER, instance_array.nbytes, instance_array, GL_STATIC_DRAW)

glEnableVertexAttribArray(2)
glVertexAttribPointer(2,3,GL_FLOAT, GL_FALSE, 0, ctypes.c_void_p(0))
glVertexAttribDivisor(2,1) # 2 is layout location, 1 means every instance will have it's own attribute (translation in this case).  

glUseProgram(shader)
glClearColor(0.1, 0.1, 0.1, 1)
glEnable(GL_DEPTH_TEST)

proj = camera.get_perspective_matrix()
translation = pyrr.matrix44.create_from_translation(pyrr.Vector3([0, 0, 0]))

model_loc = glGetUniformLocation(shader, "model")
project_loc = glGetUniformLocation(shader, "project")
view_loc = glGetUniformLocation(shader, "view")

glUniformMatrix4fv(project_loc, 1, GL_FALSE, proj)
glUniformMatrix4fv(model_loc, 1, GL_FALSE, translation)

time = 0.0
time_acum = 0.0
fps = 0

# Main application loop
while not glfw.window_should_close(window):
    
    glfw.poll_events()
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

    proj = camera.get_perspective_matrix()
    glUniformMatrix4fv(project_loc, 1, GL_FALSE, proj)
    
    view = camera.get_view_matrix()
    glUniformMatrix4fv(view_loc, 1, GL_FALSE, view)

    tans = get_billborad_transform()
    glUniformMatrix4fv(model_loc, 1, GL_FALSE, tans)

    glDrawElementsInstanced(GL_TRIANGLES, len(face_indices), GL_UNSIGNED_INT, None, n_instances)

    [time, time_acum, fps] = fps_calculations(time, time_acum, fps, print_results=True)
    
    glfw.swap_buffers(window)


glfw.terminate()    