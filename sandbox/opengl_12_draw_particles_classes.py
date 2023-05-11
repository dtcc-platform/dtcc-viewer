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

from shaders import vertex_shader_particle, fragment_shader_particle 
from shaders import vertex_shader_mesh, fragment_shader_mesh
from shaders import vertex_shader_edge, fragment_shader_edge

def create_instance_transforms_cube(n):
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

def create_instance_transforms_from_file():
    #filename = 'data/city_point_cloud_69k.txt'
    filename = 'data/city_point_cloud_1109k.txt'
    point_cloud = import_point_cloud_from_txt(filename)
    n_instances = len(point_cloud)
    instance_array = np.array(point_cloud, np.float32).flatten()

    return instance_array, n_instances 

def calc_blended_color(min, max, value):
    diff = max - min
    if(diff) <= 0:
        print("Error: Given MAX-MIN range is zero or the MAX value is smaller than given MIN value!")
        return [1,0,1]    # Error, returning magenta
    
    new_min = 0
    new_max = diff
    new_value = value - min
    percentage = 100.0 * (new_value / new_max)

    if(new_value <= new_min or new_value >= new_max):
        #Returning red [1,0,0]
        return [1.0, 0.0, 0.0]
    else:
        if (percentage >= 0.0 and percentage <= 10.0):
            #Red fading to Magenta [1,0,x], where x is increasing from 0 to 1
            frac = percentage / 10.0
            return [1.0, 0.0, (frac * 1.0)]

        elif (percentage > 10.0 and percentage <= 30.0):
            #Magenta fading to blue [x,0,1], where x is decreasing from 1 to 0
            frac = 1.0 - abs(percentage - 10.0) / 20.0
            return [(frac * 1.0), 0.0, 1.0]

        elif (percentage > 30.0 and percentage <= 50.0):
            #Blue fading to cyan [0,1,x], where x is increasing from 0 to 1
            frac = abs(percentage - 30.0) / 20.0
            return [0.0, (frac * 1.0), 1.0]

        elif (percentage > 50.0 and percentage <= 70.0):
            #Cyan fading to green [0,1,x], where x is decreasing from 1 to 0
            frac = 1.0 - abs(percentage - 50.0) / 20.0
            return [0.0, 1.0, (frac * 1.0)]

        elif (percentage > 70.0 and percentage <= 90.0):
            #Green fading to yellow [x,1,0], where x is increasing from 0 to 1
            frac = abs(percentage - 70.0) / 20.0
            return [(frac * 1.0), 1.0, 0.0]
        
        elif (percentage > 90.0 and percentage <= 100.0):
            #Yellow fading to red [1,x,0], where x is decreasing from 1 to 0
            frac = 1.0 - abs(percentage - 90.0) / 10.0
            return [1.0, (frac * 1.0), 0.0]

        elif (percentage > 100.0):
            #Returning red if the value overshoots the limit.
            return [1.0, 0.0, 0.0]


class Interaction:

    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.last_x = self.width/2.0 
        self.last_y = self.height/2.0
        self.first_mouse = True
        self.camera = Camera(float(self.width)/float(self.height))
        self.left_mbtn_pressed = False
        self.color_edge_by = 0
        self.color_particle_by = 0
        self.color_mesh_by = 0

    def key_input_callback(self, window, key, scancode, action, mode):
        if key == glfw.KEY_ESCAPE and action == glfw.PRESS:
            glfw.set_window_should_close(window, True)

        if key == glfw.KEY_W and action == glfw.PRESS:
            if(self.color_edge_by == 0):
                self.color_edge_by = 1
            elif(self.color_edge_by == 1):
                self.color_edge_by = 0

        if key == glfw.KEY_E and action == glfw.PRESS:
            if(self.color_particle_by == 0):
                self.color_particle_by = 1
            elif(self.color_particle_by == 1):
                self.color_particle_by = 0 

        if key == glfw.KEY_R and action == glfw.PRESS:
            if(self.color_mesh_by == 0):
                self.color_mesh_by = 1
            elif(self.color_mesh_by == 1):
                self.color_mesh_by = 0                
        

    def scroll_input_callback(self, window, xoffset, yoffset):
        self.camera.process_scroll_movement(xoffset, yoffset) 
        
    def mouse_input_callback(self, window, button, action, mod):  
        if button == glfw.MOUSE_BUTTON_LEFT and action == glfw.PRESS:
            self.left_mbtn_pressed = True
        elif button == glfw.MOUSE_BUTTON_LEFT and action == glfw.RELEASE:
            self.left_mbtn_pressed = False
            self.first_mouse = True
    
    def mouse_look_callback(self, window, xpos, ypos):        
        if(self.left_mbtn_pressed):
            if self.first_mouse:
                self.last_x = xpos
                self.last_y = ypos
                self.first_mouse = False

            xoffset = xpos - self.last_x
            yoffset = self.last_y - ypos
            self.last_x = xpos
            self.last_y = ypos
            self.camera.process_mouse_movement(xoffset, yoffset)


class Window:

    def __init__(self, width:int, height:int):
        self.width = width
        self.height = height
        self.interaction = Interaction(width, height)

        if not glfw.init():
            raise Exception("glfw can not be initialised!")
            
        glfw.window_hint(glfw.CONTEXT_VERSION_MAJOR, 3)
        glfw.window_hint(glfw.CONTEXT_VERSION_MINOR, 3)
        glfw.window_hint(glfw.OPENGL_FORWARD_COMPAT, True)
        glfw.window_hint(glfw.OPENGL_PROFILE, glfw.OPENGL_CORE_PROFILE)
        self.window = glfw.create_window(self.width, self.height, "OpenGL Window", None, None)      # Create window

        if not self.window:
            glfw.terminate()
            raise Exception("glfw window can not be created!")

        glfw.set_window_pos(self.window, 400, 200)
        glfw.set_window_size_callback(self.window, self.window_resize_callback)
        glfw.set_cursor_pos_callback(self.window, self.interaction.mouse_look_callback)
        glfw.set_key_callback(self.window, self.interaction.key_input_callback)
        glfw.set_mouse_button_callback(self.window, self.interaction.mouse_input_callback)
        glfw.set_scroll_callback(self.window, self.interaction.scroll_input_callback)

        # Calls can be made after the contex is made current
        glfw.make_context_current(self.window)

    # Particles
    def create_particles(self, disc_size:float, n_sides:int):
        self.particle = Particle(disc_size, n_sides)
        [self.vertices, self.face_indices] = self.particle.create_single_instance()
        [self.instance_transforms, self.n_instances] = self.particle.create_multiple_instances()    
        [self.model_loc, self.project_loc, self.view_loc, self.color_by_loc] = self.particle.create_shader()
        
        self.time, self.time_acum, self.fps = 0.0, 0.0, 0

    def render_particles(self):

        while not glfw.window_should_close(self.window):
            glfw.poll_events()
            glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

            proj = self.interaction.camera.get_perspective_matrix()
            glUniformMatrix4fv(self.project_loc, 1, GL_FALSE, proj)
            
            view = self.interaction.camera.get_view_matrix()
            glUniformMatrix4fv(self.view_loc, 1, GL_FALSE, view)

            tans = self.particle.get_billborad_transform(self.interaction.camera.camera_pos)
            glUniformMatrix4fv(self.model_loc, 1, GL_FALSE, tans)

            color_by = self.interaction.color_particle_by
            glUniform1i(self.color_by_loc, color_by)
        
            glDrawElementsInstanced(GL_TRIANGLES, len(self.face_indices), GL_UNSIGNED_INT, None, self.n_instances)

            [self.time, self.time_acum, self.fps] = self.fps_calculations(self.time, self.time_acum, self.fps, print_results=True)
            
            glfw.swap_buffers(self.window)

        glfw.terminate()       
    
    # Meshes
    def create_mesh(self):
        self.mesh = Mesh()
        [self.vertices, self.face_indices, self.edge_indices] = self.mesh.create_mesh()
        [self.model_loc_mesh, self.project_loc_mesh, self.view_loc_mesh, self.color_by_loc_mesh] = self.mesh.create_shader_mesh()
        [self.model_loc_edge, self.project_loc_edge, self.view_loc_edge, self.color_by_loc_edge] = self.mesh.create_shader_edge()
        self.time, self.time_acum, self.fps = 0.0, 0.0, 0
    
    def render_mesh(self):
        
        glClearColor(0.0, 0.0, 0.0, 1.0)
        glEnable(GL_DEPTH_TEST)

        # The same shader is used for lines and triangles so it can be bound before the loop.
        self.mesh.bind_shader_mesh()
        self.mesh.bind_vao_mesh()
        
        while not glfw.window_should_close(self.window):
            glfw.poll_events()
            glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
            
            projection = self.interaction.camera.get_perspective_matrix()
            glUniformMatrix4fv(self.project_loc_mesh, 1, GL_FALSE, projection)
            
            view = self.interaction.camera.get_view_matrix()
            glUniformMatrix4fv(self.view_loc_mesh, 1, GL_FALSE, view)

            color_by = self.interaction.color_mesh_by
            glUniform1i(self.color_by_loc_mesh, color_by)

            glDrawElements(GL_TRIANGLES, len(self.face_indices), GL_UNSIGNED_INT, None)

            [self.time, self.time_acum, self.fps] = self.fps_calculations(self.time, self.time_acum, self.fps, print_results=True)

            glfw.swap_buffers(self.window)
    
    def render_edge(self):
        
        glClearColor(0.0, 0.0, 0.0, 1.0)
        glEnable(GL_DEPTH_TEST)

        # The same shader is used for lines and triangles so it can be bound before the loop.
        self.mesh.bind_shader_edge()
        self.mesh.bind_vao_edge()
        
        while not glfw.window_should_close(self.window):
            glfw.poll_events()
            glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
            
            projection = self.interaction.camera.get_perspective_matrix()
            glUniformMatrix4fv(self.project_loc_edge, 1, GL_FALSE, projection)
            
            view = self.interaction.camera.get_view_matrix()
            glUniformMatrix4fv(self.view_loc_edge, 1, GL_FALSE, view)

            color_by = self.interaction.color_edge_by
            glUniform1i(self.color_by_loc_edge, color_by)

            glDrawElements(GL_LINES, len(self.edge_indices), GL_UNSIGNED_INT, None)

            [self.time, self.time_acum, self.fps] = self.fps_calculations(self.time, self.time_acum, self.fps, print_results=True)

            glfw.swap_buffers(self.window)
    
    # Utils
    def fps_calculations(self, prev_time, time_acum, fps, print_results = True):
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

    def window_resize_callback(self, window, width, height):
        glViewport(0, 0, width, height)
        self.interaction.width = width
        self.interaction.height = height
        self.interaction.camera.aspect_ratio = width / height 


class Particle:

    def __init__(self, disc_size:float, n_sides:int):
        self.disc_size = disc_size
        self.n_sides = n_sides

    def create_single_instance(self):
        
        [self.vertices, self.face_indices] = self.create_circular_disc(self.disc_size, self.n_sides)
        self.vertices = np.array(self.vertices, dtype=np.float32)
        self.face_indices = np.array(self.face_indices, dtype=np.uint32)

        # Generating VAO. Any subsequent vertex attribute calls will be stored in the VAO if it is bound.
        self.VAO = glGenVertexArrays(1)
        glBindVertexArray(self.VAO)

        # Vertex buffer
        self.VBO = glGenBuffers(1)
        glBindBuffer(GL_ARRAY_BUFFER, self.VBO)
        glBufferData(GL_ARRAY_BUFFER, len(self.vertices) * 4, self.vertices, GL_STATIC_DRAW) # Second argument is nr of bytes

        # Element buffer
        self.EBO = glGenBuffers(1)
        glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, self.EBO)
        glBufferData(GL_ELEMENT_ARRAY_BUFFER, len(self.face_indices)* 4, self.face_indices, GL_STATIC_DRAW)

        glEnableVertexAttribArray(0) # 0 is the layout location for the vertex shader
        glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, 24, ctypes.c_void_p(0))

        glEnableVertexAttribArray(1) # 1 is the layout location for the vertex shader
        glVertexAttribPointer(1, 3, GL_FLOAT, GL_FALSE, 24, ctypes.c_void_p(12))

        return self.vertices, self.face_indices 

    def create_multiple_instances(self):
        
        #[instance_transforms, n_instances] = create_instance_transforms_cube(3)
        [instance_transforms, n_instances] = create_instance_transforms_from_file()
        print("Number of instances created: " +str(n_instances))           

        self.transforms_VBO = glGenBuffers(1)
        glBindBuffer(GL_ARRAY_BUFFER, self.transforms_VBO)
        glBufferData(GL_ARRAY_BUFFER, instance_transforms.nbytes, instance_transforms, GL_STATIC_DRAW)

        glEnableVertexAttribArray(2)
        glVertexAttribPointer(2,3,GL_FLOAT, GL_FALSE, 0, ctypes.c_void_p(0))
        glVertexAttribDivisor(2,1) # 2 is layout location, 1 means every instance will have it's own attribute (translation in this case).  

        max_coord_x = np.max(instance_transforms)
        min_coord_x = np.min(instance_transforms)
        norm_max_x = max_coord_x - min_coord_x
        print(norm_max_x)
        
        max_coord_z = np.max(instance_transforms[2::3])
        min_coord_z = np.min(instance_transforms[2::3])
        norm_max_z = max_coord_z - min_coord_z
        print(norm_max_z)

        color_array = []
        for i in range(0, len(instance_transforms), 3):
            x = instance_transforms[i]
            y = instance_transforms[i+1]
            z = instance_transforms[i+2]
            z_norm = z - min_coord_z
            color_blend = calc_blended_color(0.0, norm_max_z, z_norm)
            color = pyrr.Vector3(color_blend)
            color_array.append(color)
            
        color_array = np.array(color_array, np.float32).flatten()

        self.color_VBO = glGenBuffers(1)
        glBindBuffer(GL_ARRAY_BUFFER, self.color_VBO)
        glBufferData(GL_ARRAY_BUFFER, color_array.nbytes, color_array, GL_STATIC_DRAW)

        glEnableVertexAttribArray(3)
        glVertexAttribPointer(3,3,GL_FLOAT, GL_FALSE, 0, ctypes.c_void_p(0))
        glVertexAttribDivisor(3,1) # 3 is layout location, 1 means every instance will have it's own attribute (translation in this case).

        return instance_transforms, n_instances

    def bind_vao(self):
        glBindVertexArray(self.VAO)

    def unbind_vao(self):
        glBindVertexArray(0)

    def create_shader(self):
        self.shader = compileProgram(compileShader(vertex_shader_particle, GL_VERTEX_SHADER), compileShader(fragment_shader_particle, GL_FRAGMENT_SHADER))
        glUseProgram(self.shader)
        glClearColor(0.0, 0.0, 0.0, 1)
        glEnable(GL_DEPTH_TEST)

        model_loc = glGetUniformLocation(self.shader, "model")
        project_loc = glGetUniformLocation(self.shader, "project")
        view_loc = glGetUniformLocation(self.shader, "view")
        color_by_loc = glGetUniformLocation(self.shader, "color_by")

        return model_loc, project_loc, view_loc, color_by_loc

    def bind_shader(self):
        glUseProgram(self.shader)

    def unbind_shader(self):
        glUseProgram(0)

    def get_billborad_transform(self, camera_position):

        dir_from_camera = pyrr.Vector3([0,0,0]) - camera_position
        angle1 = np.arctan2(-dir_from_camera[1], dir_from_camera[0])        # arctan(dy/dx)
        dist2d = math.sqrt(dir_from_camera[0]**2 + dir_from_camera[1]**2)   # sqrt(dx^2 + dy^2)
        angle2 = np.arctan2(dir_from_camera[2], dist2d)                     # angle around vertical axis

        model_transform = pyrr.matrix44.create_identity(dtype=np.float32)
        model_transform = pyrr.matrix44.multiply(model_transform, pyrr.matrix44.create_from_y_rotation(theta=angle2, dtype=np.float32))
        model_transform = pyrr.matrix44.multiply(model_transform, pyrr.matrix44.create_from_z_rotation(theta=angle1, dtype=np.float32))

        return model_transform

    def create_circular_disc(self, radius, n):
        center = [0.0, 0.0, 0.0]
        center_color = [1.0, 1.0, 1.0]          # White
        edge_color = [0.5, 0.5, 0.5]          # Magenta
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


class Mesh:
    
    def __init__(self):
        pass

    def create_mesh(self):
        #[face_indices, vert_coord, vert_color, vertices] = ObjLoader.load_model("./data/simple_city_2_color.obj")
        #[self.face_indices, vert_coord, vert_color, self.vertices] = ObjLoader.load_model("./data/simple_city_dense.obj")
        [self.face_indices, vert_coord, vert_color, self.vertices, self.edge_indices] = ObjLoader.load_model("../data/models/CitySurface.obj")

        # Generating VAO. Any subsequent vertex attribute calls will be stored in the VAO if it is bound.
        self.VAO_mesh = glGenVertexArrays(1)
        glBindVertexArray(self.VAO_mesh)

        # Vertex buffer
        self.VBO_mesh = glGenBuffers(1)
        glBindBuffer(GL_ARRAY_BUFFER, self.VBO_mesh)
        glBufferData(GL_ARRAY_BUFFER, len(self.vertices) * 4, self.vertices, GL_STATIC_DRAW) # Second argument is nr of bytes

        # Element buffer
        self.EBO_mesh = glGenBuffers(1)
        glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, self.EBO_mesh)
        glBufferData(GL_ELEMENT_ARRAY_BUFFER, len(self.face_indices)* 4, self.face_indices, GL_STATIC_DRAW)

        # Position
        glEnableVertexAttribArray(0) # 0 is the layout location for the vertex shader
        glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, 24, ctypes.c_void_p(0))

        # Color
        glEnableVertexAttribArray(1) # 1 is the layout location for the vertex shader
        glVertexAttribPointer(1, 3, GL_FLOAT, GL_FALSE, 24, ctypes.c_void_p(12))


        # -------------- EDGES for wireframe display ---------------- #

        self.VAO_edge = glGenVertexArrays(1)
        glBindVertexArray(self.VAO_edge)

        # Vertex buffer
        self.VBO_edge = glGenBuffers(1)
        glBindBuffer(GL_ARRAY_BUFFER, self.VBO_edge)
        glBufferData(GL_ARRAY_BUFFER, len(self.vertices) * 4, self.vertices, GL_STATIC_DRAW) # Second argument is nr of bytes


        self.EBO_edge = glGenBuffers(1)
        glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, self.EBO_edge)
        glBufferData(GL_ELEMENT_ARRAY_BUFFER, len(self.edge_indices)* 4, self.edge_indices, GL_STATIC_DRAW)

        # Position
        glEnableVertexAttribArray(0) # 0 is the layout location for the vertex shader
        glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, 24, ctypes.c_void_p(0))

        # Color
        glEnableVertexAttribArray(1) # 1 is the layout location for the vertex shader
        glVertexAttribPointer(1, 3, GL_FLOAT, GL_FALSE, 24, ctypes.c_void_p(12))

        glBindVertexArray(0)

        return self.vertices, self.face_indices, self.edge_indices 

    def create_shader_mesh(self):
        self.bind_vao_mesh()
        self.shader_mesh = compileProgram(compileShader(vertex_shader_mesh, GL_VERTEX_SHADER), compileShader(fragment_shader_mesh, GL_FRAGMENT_SHADER))
        glUseProgram(self.shader_mesh)

        model_loc = glGetUniformLocation(self.shader_mesh, "model")
        project_loc = glGetUniformLocation(self.shader_mesh, "project")
        view_loc = glGetUniformLocation(self.shader_mesh, "view")
        color_by_loc = glGetUniformLocation(self.shader_mesh, "color_by")

        return model_loc, project_loc, view_loc, color_by_loc
    
    def create_shader_edge(self):
        self.bind_vao_edge()
        self.shader_edge = compileProgram(compileShader(vertex_shader_edge, GL_VERTEX_SHADER), compileShader(fragment_shader_edge, GL_FRAGMENT_SHADER))
        glUseProgram(self.shader_edge)

        model_loc = glGetUniformLocation(self.shader_edge, "model")
        project_loc = glGetUniformLocation(self.shader_edge, "project")
        view_loc = glGetUniformLocation(self.shader_edge, "view")
        color_by_loc = glGetUniformLocation(self.shader_edge, "color_by")

        return model_loc, project_loc, view_loc, color_by_loc

    def render_mesh():
        pass

    def render_edge():
        pass

    def bind_vao_mesh(self):
        glBindVertexArray(self.VAO_mesh)

    def bind_vao_edge(self):
        glBindVertexArray(self.VAO_edge)

    def unbind_vao(self):
        glBindVertexArray(0)

    def bind_shader_mesh(self):
        glUseProgram(self.shader_mesh)

    def bind_shader_edge(self):
        glUseProgram(self.shader_edge)

    def unbind_shader(self):
        glUseProgram(0)



if __name__ == "__main__":

    #window = Window(1600, 1400)
    #window.create_particles(0.3, 12)
    #window.render_particles()

    window = Window(1600, 1400)
    window.create_mesh()
    window.render_mesh()


    pass