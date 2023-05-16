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

vertex_shader_fancy = """
# version 330 core

layout(location = 0) in vec3 a_position; 
layout(location = 1) in vec3 a_color;
layout(location = 2) in vec3 a_normal;

uniform mat4 model;
uniform mat4 view;
uniform mat4 project;

out vec3 v_frag_pos;
out vec3 v_color;
out vec3 v_normal;

void main()
{
    gl_Position = project * view * model * vec4(a_position, 1.0);
    v_frag_pos = vec3(model * vec4(a_position, 1.0));
    v_color = a_color;
    v_normal = a_normal;
}
"""

fragment_shader_fancy = """ 
# version 330 core

in vec3 v_frag_pos;
in vec3 v_color;
in vec3 v_normal;

uniform vec3 object_color;
uniform vec3 light_color;
uniform vec3 light_position;
uniform vec3 view_position;

out vec4 out_frag_color;

void main()
{
	float ambient_strength = 0.2;
	vec3 ambient = ambient_strength * light_color;

	vec3 norm = normalize(v_normal);
	vec3 light_dir = normalize(light_position - v_frag_pos);

	float diff = max(dot(norm, light_dir), 0.0);
	vec3 diffuse = diff * light_color;

	float specular_strength = 0.7;
	vec3 view_dir = normalize(view_position - v_frag_pos);
	vec3 reflect_dir = reflect(-light_dir, norm);

	float spec = pow(max(dot(view_dir, reflect_dir), 0.0), 16);
	vec3 specular = specular_strength * spec * light_color;

	vec3 result = (ambient + diffuse + specular) * vec3(v_color); // objectColor;
	out_frag_color = vec4(result, 1.0);

}
"""

# glfw callback function
def window_resize(window, width, height):
    glViewport(0, 0, width, height)
    project = pyrr.matrix44.create_perspective_projection(45,width / height, 0.1, 100)
    glUniformMatrix4fv(project_loc, 1, GL_FALSE, project)
    

if not glfw.init():
    raise Exception("glfw can not be initialised!")
    
glfw.window_hint(glfw.CONTEXT_VERSION_MAJOR, 3)
glfw.window_hint(glfw.CONTEXT_VERSION_MINOR, 3)
glfw.window_hint(glfw.OPENGL_FORWARD_COMPAT, True)
glfw.window_hint(glfw.OPENGL_PROFILE, glfw.OPENGL_CORE_PROFILE)
window = glfw.create_window(window_w, window_h, "OpenGL Window", None, None)      # Create window

if not window:
    glfw.terminate()
    raise Exception("glfw window can not be created!")
    
glfw.set_window_pos(window, 400, 200)

glfw.set_window_size_callback(window, window_resize)

# Calls can be made after the contex is made current
glfw.make_context_current(window)

vertices = [    -3, -3, -1, 1, 1, 1, 0, 0, 1,
                 3, -3, -1, 1, 1, 1, 0, 0, 1,
                -3,  3, -1, 1, 1, 1, 0, 0, 1,

                 3, -3, -1, 1, 1, 1, 0, 0, 1,
                -3,  3, -1, 1, 1, 1, 0, 0, 1,
                 3,  3, -1, 1, 1, 1, 0, 0, 1,
    
               -0.5,0.5,-0.5,0.9960784314,0.7764705882,0,0,0,-1,
                -0.5,-0.5,-0.5,1,0.1490196078,0,0,0,-1,
                0.5,-0.5,-0.5,0.9960784314,0.7764705882,0,0,0,-1,
                -0.5,0.5,-0.5,0.9960784314,0.7764705882,0,0,0,-1,
                0.5,-0.5,-0.5,0.9960784314,0.7764705882,0,0,0,-1,
                0.5,0.5,-0.5,0.7450980392,0.9882352941,0,0,0,-1,
                -0.5,0.5,0.5,0.7450980392,0.9882352941,0,0,0,1,
                0.5,0.5,0.5,0,1,0,0,0,1,
                0.5,-0.5,0.5,0.7450980392,0.9882352941,0,0,0,1,
                -0.5,0.5,0.5,0.7450980392,0.9882352941,0,0,0,1,
                0.5,-0.5,0.5,0.7450980392,0.9882352941,0,0,0,1,
                -0.5,-0.5,0.5,0.9960784314,0.7764705882,0,0,0,1,
                -0.5,0.5,0.5,0.7450980392,0.9882352941,0,-1,0,0,
                -0.5,-0.5,0.5,0.9960784314,0.7764705882,0,-1,0,0,
                -0.5,-0.5,-0.5,1,0.1490196078,0,-1,0,0,
                -0.5,0.5,0.5,0.7450980392,0.9882352941,0,-1,0,0,
                -0.5,-0.5,-0.5,1,0.1490196078,0,-1,0,0,
                -0.5,0.5,-0.5,0.9960784314,0.7764705882,0,-1,0,0,
                0.5,0.5,0.5,0,1,0,0,1,0,
                -0.5,0.5,0.5,0.7450980392,0.9882352941,0,0,1,0,
                -0.5,0.5,-0.5,0.9960784314,0.7764705882,0,0,1,0,
                0.5,0.5,0.5,0,1,0,0,1,0,
                -0.5,0.5,-0.5,0.9960784314,0.7764705882,0,0,1,0,
                0.5,0.5,-0.5,0.7450980392,0.9882352941,0,0,1,0,
                0.5,-0.5,0.5,0.7450980392,0.9882352941,0,1,0,0,
                0.5,0.5,0.5,0,1,0,1,0,0,
                0.5,0.5,-0.5,0.7450980392,0.9882352941,0,1,0,0,
                0.5,-0.5,0.5,0.7450980392,0.9882352941,0,1,0,0,
                0.5,0.5,-0.5,0.7450980392,0.9882352941,0,1,0,0,
                0.5,-0.5,-0.5,0.9960784314,0.7764705882,0,1,0,0,
                -0.5,-0.5,0.5,0.9960784314,0.7764705882,0,0,-1,0,
                0.5,-0.5,0.5,0.7450980392,0.9882352941,0,0,-1,0,
                0.5,-0.5,-0.5,0.9960784314,0.7764705882,0,0,-1,0,
                -0.5,-0.5,0.5,0.9960784314,0.7764705882,0,0,-1,0,
                0.5,-0.5,-0.5,0.9960784314,0.7764705882,0,0,-1,0,
                -0.5,-0.5,-0.5,1,0.1490196078,0,0,-1,0]


indices = [ 0,1,2,
            3,4,5,
            
            6,7,8,
            9,10,11,
            12,13,14,
            15,16,17,
            18,19,20,
            21,22,23,
            24,25,26,
            27,28,29,
            30,31,32,
            33,34,35,
            36,37,38,
            39,40,41]


vertices = np.array(vertices, dtype=np.float32)
indices = np.array(indices, dtype=np.uint32)


VAO = glGenVertexArrays(1)
glBindVertexArray(VAO)

# Vertex buffer
VBO = glGenBuffers(1)
glBindBuffer(GL_ARRAY_BUFFER, VBO)
glBufferData(GL_ARRAY_BUFFER, len(vertices) * 4, vertices, GL_STATIC_DRAW) # Second argument is nr of bytes

# Element buffer
EBO = glGenBuffers(1)
glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, EBO)
glBufferData(GL_ELEMENT_ARRAY_BUFFER, len(indices)* 4, indices, GL_STATIC_DRAW)


#shader = compileProgram(compileShader(vertex_src, GL_VERTEX_SHADER), compileShader(fragment_src, GL_FRAGMENT_SHADER))
shader = compileProgram(compileShader(vertex_shader_fancy, GL_VERTEX_SHADER), compileShader(fragment_shader_fancy, GL_FRAGMENT_SHADER))

# Position
glEnableVertexAttribArray(0) # 0 is the layout location for the vertex shader
glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, 36, ctypes.c_void_p(0))

# Color
glEnableVertexAttribArray(1) # 1 is the layout location for the vertex shader
glVertexAttribPointer(1, 3, GL_FLOAT, GL_FALSE, 36, ctypes.c_void_p(12))

# Normal
glEnableVertexAttribArray(2) # 1 is the layout location for the vertex shader
glVertexAttribPointer(2, 3, GL_FLOAT, GL_FALSE, 36, ctypes.c_void_p(24))


glUseProgram(shader)
glClearColor(0, 0.1, 0, 1)
glEnable(GL_DEPTH_TEST)

project = pyrr.matrix44.create_perspective_projection(45, window_w / window_h, 0.1, 100)
translate = pyrr.matrix44.create_from_translation(pyrr.Vector3([0, 0, 0]))
#eye position, target position, up vector
view = pyrr.matrix44.create_look_at(pyrr.Vector3([0, 3, 0]), pyrr.Vector3([0, 0, 0]), pyrr.Vector3([0, 0, 1]))


model_loc = glGetUniformLocation(shader, "model")
project_loc = glGetUniformLocation(shader, "project")
view_loc = glGetUniformLocation(shader, "view")

object_color_loc = glGetUniformLocation(shader, "object_color")
light_color_loc = glGetUniformLocation(shader, "light_color")
light_position_loc = glGetUniformLocation(shader, "light_position")
view_position_loc = glGetUniformLocation(shader, "view_position")

# Only change when the window size changes
glUniformMatrix4fv(project_loc, 1, GL_FALSE, project)
glUniformMatrix4fv(model_loc, 1, GL_FALSE, translate)
glUniformMatrix4fv(view_loc, 1, GL_FALSE, view) 

glUniform3f(object_color_loc, 1.0, 0.5, 0.31)
glUniform3f(light_color_loc, 1.0, 1.0, 1.0)
glUniform3f(light_position_loc, 1.0, 1.0, 1.0)


# Main application loop
while not glfw.window_should_close(window):
    glfw.poll_events()
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    
    # Varying ligth source position
    light_x = 4.0 #math.sin(glfw.get_time()) * 4.0
    light_y = 4.0 #math.cos(glfw.get_time()) * 4.0
    light_z = 4.0
    glUniform3f(light_position_loc, light_x, light_y, light_z)
    

    # Varying campera position
    cam_x = math.sin(glfw.get_time()) * 4.0
    cam_y = math.cos(glfw.get_time()) * 4.0 
    cam_z = 2.0
    view = pyrr.matrix44.create_look_at(pyrr.Vector3([cam_x, cam_y, cam_z]), pyrr.Vector3([0.0, 0.0, 0.0]), pyrr.Vector3([0.0, 0.0, 1.0]))
    glUniform3f(view_position_loc, cam_x, cam_y, cam_z)

    # Varying light color
    light_r = 1.0 #math.sin(glfw.get_time())
    light_g = 1.0 #math.cos(glfw.get_time())
    light_b = 1.0
    glUniform3f(light_color_loc, light_r, light_g, light_b)


    glUniformMatrix4fv(view_loc, 1, GL_FALSE, view)

    glDrawElements(GL_TRIANGLES, len(indices), GL_UNSIGNED_INT, None)
    glfw.swap_buffers(window)


glfw.terminate()    