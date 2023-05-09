import glfw
from OpenGL.GL import *
from OpenGL.GL.shaders import compileProgram, compileShader
import numpy as np
import pyrr
from pprint import pp
from enum import Enum
import math
from obj_loader import ObjLoader, import_point_cloud_from_txt
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
    camera.process_scroll_movement(xoffset, yoffset) 
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
layout(location = 3) in vec3 a_icolor;

uniform mat4 model;
uniform mat4 project;
uniform mat4 view;
uniform int color_by;

out vec3 v_color;
void main()
{   
    vec4 final_pos = (model * vec4(a_position, 1.0)) + vec4(a_offset, 0.0);
    gl_Position = project * view * final_pos;
    if(color_by == 1)
    {
        v_color = a_icolor;
    }
    else
    {
        v_color = a_icolor * a_color;
    }
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

def create_circular_disc(radius, n):
    center = [0.0, 0.0, 0.0]
    center_color = [1.0, 1.0, 1.0]          # White
    edge_color = [0.0, 0.0, 0.0]          # Magenta
    angle_between_points = 2 * math.pi / n
    vertices = []
    vertices.extend(center)
    vertices.extend(center_color)
    face_indices = []
    # Iterate over each angle and calculate the corresponding point on the circle
    for i in range(n):
        angle = i * angle_between_points
        x = center[0]
        y = center[1] + radius * math.cos(angle)
        z = center[2] + radius * math.sin(angle)
        vertices.extend([x, y, z])
        vertices.extend(edge_color)
        if i > 0 and i < n:
            face_indices.extend([0, i+1, i])
        if i == n-1:
            face_indices.extend([0, 1, i+1])

    return vertices, face_indices

def create_instance_array_cube(n):
    instance_array = []
    offset = 0.05
    size = n

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

    return instance_array, n_instances 

def create_instance_array_from_file():
    
    #filename = 'data/city_point_cloud_69k.txt'
    filename = 'data/city_point_cloud_1109k.txt'
    point_cloud = import_point_cloud_from_txt(filename)
    n_instances = len(point_cloud)
    instance_array = np.array(point_cloud, np.float32).flatten()

    return instance_array, n_instances 


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

disc_size = 0.30
n_sides = 12

[vertices, face_indices] = create_circular_disc(disc_size, n_sides)

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

glEnableVertexAttribArray(0) # 0 is the layout location for the vertex shader
glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, 24, ctypes.c_void_p(0))

glEnableVertexAttribArray(1) # 1 is the layout location for the vertex shader
glVertexAttribPointer(1, 3, GL_FLOAT, GL_FALSE, 24, ctypes.c_void_p(12))

# Instance VBO

#[instance_array, n_instances] = create_instance_array_cube(1)
[instance_array, n_instances] = create_instance_array_from_file()
print("Number of instances: " +str(n_instances))           

instance_VBO = glGenBuffers(1)
glBindBuffer(GL_ARRAY_BUFFER, instance_VBO)
glBufferData(GL_ARRAY_BUFFER, instance_array.nbytes, instance_array, GL_STATIC_DRAW)

glEnableVertexAttribArray(2)
glVertexAttribPointer(2,3,GL_FLOAT, GL_FALSE, 0, ctypes.c_void_p(0))
glVertexAttribDivisor(2,1) # 2 is layout location, 1 means every instance will have it's own attribute (translation in this case).  

max_coord = np.max(instance_array)
min_coord = np.min(instance_array)
norm_max = max_coord - min_coord

color_array = []
for i in range(0, len(instance_array), 3):
    x = instance_array[i]
    y = instance_array[i+1]
    z = instance_array[i+2]
    x_norm = x - min_coord
    a = x_norm / norm_max 
    color = pyrr.Vector3([1.0-a, 0.0, a])
    color_array.append(color)
    
print(len(color_array))
color_array = np.array(color_array, np.float32).flatten()

color_VBO = glGenBuffers(1)
glBindBuffer(GL_ARRAY_BUFFER, color_VBO)
glBufferData(GL_ARRAY_BUFFER, color_array.nbytes, color_array, GL_STATIC_DRAW)

glEnableVertexAttribArray(3)
glVertexAttribPointer(3,3,GL_FLOAT, GL_FALSE, 0, ctypes.c_void_p(0))
glVertexAttribDivisor(3,1) # 3 is layout location, 1 means every instance will have it's own attribute (translation in this case).  

# Shader
shader = compileProgram(compileShader(vertex_src, GL_VERTEX_SHADER), compileShader(fragment_src, GL_FRAGMENT_SHADER))

glUseProgram(shader)
glClearColor(0.0, 0.0, 0.0, 1)
glEnable(GL_DEPTH_TEST)

model_loc = glGetUniformLocation(shader, "model")
project_loc = glGetUniformLocation(shader, "project")
view_loc = glGetUniformLocation(shader, "view")
color_by_loc = glGetUniformLocation(shader, "color_by")

color_by = 0
glUniform1i(color_by_loc, color_by)

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