import math
import glfw
import numpy as np
from OpenGL.GL import *
from OpenGL.GL.shaders import compileProgram, compileShader
import pyrr
from interaction import Interaction
from utils import create_instance_transforms_from_file, calc_blended_color
from utils import create_instance_transforms_cube
from shaders import vertex_shader_particle, fragment_shader_particle


class Particle:

    def __init__(self, disc_size:float, n_sides:int):
        self._create_single_instance(disc_size, n_sides)
        self._create_multiple_instances()    
        self._create_shader()    

    def render(self, interaction: Interaction):

        self._bind_vao()
        self._bind_shader()

        proj = interaction.camera.get_perspective_matrix()
        glUniformMatrix4fv(self.project_loc, 1, GL_FALSE, proj)
        
        view = interaction.camera.get_view_matrix()
        glUniformMatrix4fv(self.view_loc, 1, GL_FALSE, view)

        tans = self._get_billborad_transform(interaction.camera.camera_pos)
        glUniformMatrix4fv(self.model_loc, 1, GL_FALSE, tans)

        color_by = interaction.coloring
        glUniform1i(self.color_by_loc, color_by)
    
        glDrawElementsInstanced(GL_TRIANGLES, len(self.face_indices), GL_UNSIGNED_INT, None, self.n_instances)

        self._unbind_vao()
        self._unbind_shader()

    def _create_single_instance(self, disc_size, n_sides):
        
        [self.vertices, self.face_indices] = self._create_circular_disc(disc_size, n_sides)
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

    def _create_multiple_instances(self):
        
        #[instance_transforms, n_instances] = create_instance_transforms_cube(100)
        [self.instance_transforms, self.n_instances] = create_instance_transforms_from_file()
        print("Number of instances created: " +str(self.n_instances))           

        self.transforms_VBO = glGenBuffers(1)
        glBindBuffer(GL_ARRAY_BUFFER, self.transforms_VBO)
        glBufferData(GL_ARRAY_BUFFER, self.instance_transforms.nbytes, self.instance_transforms, GL_STATIC_DRAW)

        glEnableVertexAttribArray(2)
        glVertexAttribPointer(2,3,GL_FLOAT, GL_FALSE, 0, ctypes.c_void_p(0))
        glVertexAttribDivisor(2,1) # 2 is layout location, 1 means every instance will have it's own attribute (translation in this case).  

        max_coord_x = np.max(self.instance_transforms)
        min_coord_x = np.min(self.instance_transforms)
        norm_max_x = max_coord_x - min_coord_x
        
        max_coord_z = np.max(self.instance_transforms[2::3])
        min_coord_z = np.min(self.instance_transforms[2::3])
        norm_max_z = max_coord_z - min_coord_z

        color_array = []
        for i in range(0, len(self.instance_transforms), 3):
            x = self.instance_transforms[i]
            y = self.instance_transforms[i+1]
            z = self.instance_transforms[i+2]
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

    def _bind_vao(self):
        glBindVertexArray(self.VAO)

    def _unbind_vao(self):
        glBindVertexArray(0)

    def _create_shader(self):
        self.shader = compileProgram(compileShader(vertex_shader_particle, GL_VERTEX_SHADER), compileShader(fragment_shader_particle, GL_FRAGMENT_SHADER))
        glUseProgram(self.shader)

        self.model_loc = glGetUniformLocation(self.shader, "model")
        self.project_loc = glGetUniformLocation(self.shader, "project")
        self.view_loc = glGetUniformLocation(self.shader, "view")
        self.color_by_loc = glGetUniformLocation(self.shader, "color_by")

    def _bind_shader(self):
        glUseProgram(self.shader)

    def _unbind_shader(self):
        glUseProgram(0)

    def _get_billborad_transform(self, camera_position):

        dir_from_camera = pyrr.Vector3([0,0,0]) - camera_position
        angle1 = np.arctan2(-dir_from_camera[1], dir_from_camera[0])        # arctan(dy/dx)
        dist2d = math.sqrt(dir_from_camera[0]**2 + dir_from_camera[1]**2)   # sqrt(dx^2 + dy^2)
        angle2 = np.arctan2(dir_from_camera[2], dist2d)                     # angle around vertical axis

        model_transform = pyrr.matrix44.create_identity(dtype=np.float32)
        model_transform = pyrr.matrix44.multiply(model_transform, pyrr.matrix44.create_from_y_rotation(theta=angle2, dtype=np.float32))
        model_transform = pyrr.matrix44.multiply(model_transform, pyrr.matrix44.create_from_z_rotation(theta=angle1, dtype=np.float32))

        return model_transform

    def _create_circular_disc(self, radius, n):
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