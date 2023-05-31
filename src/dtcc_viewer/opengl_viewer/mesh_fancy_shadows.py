
import math
import glfw
import numpy as np
from OpenGL.GL import *
from OpenGL.GL.shaders import compileProgram, compileShader
import pyrr
from dtcc_viewer.opengl_viewer.interaction import Interaction

from dtcc_viewer.opengl_viewer.shaders_mesh_fancy_shadows import vertex_shader_fancy_shadow, fragment_shader_fancy_shadow
from dtcc_viewer.opengl_viewer.shaders_mesh_fancy_shadows import vertex_shader_shadow_map, fragment_shader_shadow_map
from dtcc_viewer.opengl_viewer.shaders_mesh_fancy_shadows import vertex_shader_debug, fragment_shader_debug

class MeshShadow:
    
    def __init__(self, vertices:np.ndarray, faces:np.ndarray, edges:np.ndarray):
        
        self.vertices = vertices
        self.face_indices = faces
        self.edge_indices = edges

        self._calc_model_scale()
        self._create_triangels()
        self._create_shadow_map()
        self._create_shader_fancy_shadow()
        self._create_shader_shadow()
        self._set_constats()

    def _calc_model_scale(self):
        xmin = self.vertices[0::3].min()
        xmax = self.vertices[0::3].max()
        ymin = self.vertices[1::3].min()
        ymax = self.vertices[1::3].max()

        xdom = xmax - xmin
        ydom = ymax - ymin
        
        self.diameter_xy = math.sqrt(xdom * xdom + ydom * ydom)
        self.radius_xy = self.diameter_xy / 2.0

    def _create_triangels(self):
        
        #----------------- TRIANGLES for shaded display ------------------#

        # Generating VAO. Any subsequent vertex attribute calls will be stored in the VAO if it is bound.
        self.VAO_triangels = glGenVertexArrays(1)
        glBindVertexArray(self.VAO_triangels)

        # Vertex buffer
        self.VBO_triangels = glGenBuffers(1)
        glBindBuffer(GL_ARRAY_BUFFER, self.VBO_triangels)
        glBufferData(GL_ARRAY_BUFFER, len(self.vertices) * 4, self.vertices, GL_STATIC_DRAW) # Second argument is nr of bytes

        # Element buffer
        self.EBO_triangels = glGenBuffers(1)
        glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, self.EBO_triangels)
        glBufferData(GL_ELEMENT_ARRAY_BUFFER, len(self.face_indices)* 4, self.face_indices, GL_STATIC_DRAW)

        # Position
        glEnableVertexAttribArray(0) # 0 is the layout location for the vertex shader
        glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, 36, ctypes.c_void_p(0))

        # Color
        glEnableVertexAttribArray(1) # 1 is the layout location for the vertex shader
        glVertexAttribPointer(1, 3, GL_FLOAT, GL_FALSE, 36, ctypes.c_void_p(12))

        # Normals
        glEnableVertexAttribArray(2) # 1 is the layout location for the vertex shader
        glVertexAttribPointer(2, 3, GL_FLOAT, GL_FALSE, 36, ctypes.c_void_p(24))

        glBindVertexArray(0)
    
    def _create_shadow_map(self):
        # Frambuffer for the shadow map
        self.FBO = glGenFramebuffers(1)
        glGenTextures(1, self.FBO)

        # Creating a texture which will be used as the framebuffers depth buffer
        self.depth_map = glGenTextures(1)
        glBindTexture(GL_TEXTURE_2D, self.depth_map)
        self.shadow_map_resolution = 1024 * 6
        glTexImage2D(GL_TEXTURE_2D, 0, GL_DEPTH_COMPONENT, self.shadow_map_resolution, self.shadow_map_resolution, 0, GL_DEPTH_COMPONENT, GL_FLOAT, None)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_BORDER) 
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_BORDER) 
        border_color = np.array([1.0, 1.0, 1.0, 1.0], dtype=np.float32)
        glTexParameterfv(GL_TEXTURE_2D, GL_TEXTURE_BORDER_COLOR, border_color)

        glBindFramebuffer(GL_FRAMEBUFFER, self.FBO)
        glFramebufferTexture2D(GL_FRAMEBUFFER, GL_DEPTH_ATTACHMENT, GL_TEXTURE_2D, self.depth_map, 0)
        glDrawBuffer(GL_NONE)   #Disable drawing to the color attachements since we only care about the depth
        glReadBuffer(GL_NONE)   #We don't want to read color attachements either
        glBindFramebuffer(GL_FRAMEBUFFER, 0) 

    def _create_shader_fancy_shadow(self):
        self._bind_vao_triangels()
        self.shader_fancy = compileProgram(compileShader(vertex_shader_fancy_shadow, GL_VERTEX_SHADER), 
                                               compileShader(fragment_shader_fancy_shadow, GL_FRAGMENT_SHADER))

        glUseProgram(self.shader_fancy)

        self.model_loc = glGetUniformLocation(self.shader_fancy, "model")
        self.project_loc = glGetUniformLocation(self.shader_fancy, "project")
        self.view_loc = glGetUniformLocation(self.shader_fancy, "view")

        self.light_color_loc = glGetUniformLocation(self.shader_fancy, "light_color")
        self.light_position_loc = glGetUniformLocation(self.shader_fancy, "light_position")
        self.view_position_loc = glGetUniformLocation(self.shader_fancy, "view_position")
        self.light_space_matrix_loc = glGetUniformLocation(self.shader_fancy, "light_space_matrix")

    def _create_shader_shadow(self):
        self.shader_shadow = compileProgram(compileShader(vertex_shader_shadow_map, GL_VERTEX_SHADER), 
                                            compileShader(fragment_shader_shadow_map, GL_FRAGMENT_SHADER))
        
        glUseProgram(self.shader_shadow)
        
        self.light_space_matrix_loc = glGetUniformLocation(self.shader_shadow, "light_space_matrix")
        self.model_loc_shadow = glGetUniformLocation(self.shader_shadow, "model")

    def _set_constats(self):
        self.light_position = np.array([500.0, 500.0, 400.0], dtype=np.float32)
        self.light_color = np.array([1.0, 1.0, 1.0], dtype=np.float32)


    def _render_first_pass(self):
        self._bind_vao_triangels()
        glDrawElements(GL_TRIANGLES, len(self.face_indices), GL_UNSIGNED_INT, None)
        self._unbind_vao()

    def _render_second_pass(self):
        self._bind_vao_triangels()
        glDrawElements(GL_TRIANGLES, len(self.face_indices), GL_UNSIGNED_INT, None)
        self._unbind_vao()    
        
    def render_shadow_map(self, time):    
        #first pass: Capture shadow map
        rad = self.radius_xy
        self.light_position = np.array([math.sin(time) * rad, math.cos(time) * rad, abs(math.sin(time/2.0)) * 0.7 * rad], dtype=np.float32)
        
        light_projection = pyrr.matrix44.create_orthogonal_projection(-rad, rad, -rad, rad, 0.1, self.diameter_xy, dtype=np.float32)   
        look_target = np.array([0, 0, 0], dtype=np.float32)
        global_up = np.array([0, 0, 1], dtype= np.float32)
        light_view = pyrr.matrix44.create_look_at(self.light_position, look_target, global_up, dtype= np.float32)
        self.light_space_matrix = pyrr.matrix44.multiply(light_view, light_projection) # Other order? 
        glUseProgram(self.shader_shadow)
        light_space_matrix_loc = glGetUniformLocation(self.shader_shadow, "light_space_matrix")
        glUniformMatrix4fv(light_space_matrix_loc, 1, GL_FALSE, self.light_space_matrix)

        self.model_loc_shadow = glGetUniformLocation(self.shader_shadow, "model")        
        translation = pyrr.matrix44.create_from_translation(pyrr.Vector3([0, 0, 0]))
        glUniformMatrix4fv(self.model_loc_shadow, 1, GL_FALSE, translation)

        glViewport(0,0,self.shadow_map_resolution, self.shadow_map_resolution)
        glBindFramebuffer(GL_FRAMEBUFFER, self.FBO)
        glClear(GL_DEPTH_BUFFER_BIT)                # Only clearing depth buffer since there is no color attachement
        self._render_first_pass()
            
    
    def render_model_with_shadows(self, interaction:Interaction):

        glBindFramebuffer(GL_FRAMEBUFFER, 0)        #Setting default buffer
        glViewport(0,0, interaction.width, interaction.height)
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        glUseProgram(self.shader_fancy)
        light_space_matrix_loc = glGetUniformLocation(self.shader_fancy, "light_space_matrix")
        self.model_loc = glGetUniformLocation(self.shader_fancy, "model")

        translation = pyrr.matrix44.create_from_translation(pyrr.Vector3([0, 0, 0]))
        glUniformMatrix4fv(self.model_loc, 1, GL_FALSE, translation)

        #Camera input
        view = interaction.camera.get_view_matrix()
        proj = interaction.camera.get_perspective_matrix()
        glUniformMatrix4fv(self.project_loc, 1, GL_FALSE, proj)
        glUniformMatrix4fv(self.view_loc, 1, GL_FALSE, view)

        #Set light uniforms
        glUniform3f(self.light_color_loc, self.light_color[0], self.light_color[1], self.light_color[2])
        glUniform3f(self.view_position_loc, interaction.camera.camera_pos[0], interaction.camera.camera_pos[1], interaction.camera.camera_pos[2])
        glUniform3f(self.light_position_loc, self.light_position[0], self.light_position[1], self.light_position[2])
        glUniformMatrix4fv(light_space_matrix_loc, 1, GL_FALSE, self.light_space_matrix)

        glActiveTexture(GL_TEXTURE0)
        glBindTexture(GL_TEXTURE_2D, self.depth_map)    
        
        self._render_second_pass()


    def _bind_vao_triangels(self):
        glBindVertexArray(self.VAO_triangels)

    def _bind_vao_lines(self):
        glBindVertexArray(self.VAO_edge)

    def _unbind_vao(self):
        glBindVertexArray(0)

    def _bind_shader_triangels(self):
        glUseProgram(self.shader_triangels)

    def _bind_shader_fancy(self):
        glUseProgram(self.shader_fancy)

    def _bind_shader_shadow(self):
        glUseProgram(self.shader_shadow)

    def _bind_shader_lines(self):
        glUseProgram(self.shader_lines)

    def _unbind_shader(self):
        glUseProgram(0)
