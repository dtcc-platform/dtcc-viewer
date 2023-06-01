
import math
import glfw
import numpy as np
from OpenGL.GL import *
from OpenGL.GL.shaders import compileProgram, compileShader
import pyrr
from dtcc_viewer.opengl_viewer.interaction import Interaction

from dtcc_viewer.opengl_viewer.shaders_mesh_fancy_shadows import vertex_shader_fancy_shadow, fragment_shader_fancy_shadow
from dtcc_viewer.opengl_viewer.shaders_mesh_fancy_shadows import vertex_shader_shadow_map, fragment_shader_shadow_map
from dtcc_viewer.opengl_viewer.shaders_mesh_fancy import vertex_shader_fancy, fragment_shader_fancy
from dtcc_viewer.opengl_viewer.shaders_mesh_basic import vertex_shader_basic, fragment_shader_basic
from dtcc_viewer.opengl_viewer.shaders_lines import vertex_shader_lines, fragment_shader_lines


class MeshShadow:
    
    def __init__(self, vertices:np.ndarray, faces:np.ndarray, edges:np.ndarray):
        
        self.vertices = vertices
        self.face_indices = faces
        self.edge_indices = edges

        self._calc_model_scale()
        self._create_lines()
        self._create_triangels()
        self._create_shadow_map()
        self._create_shader_lines()
        self._create_shader_basic()
        self._create_shader_fancy()
        self._create_shader_fancy_shadow()
        self._create_shader_shadow_map()
        self._set_constats()

    # Utility functions
    def _calc_model_scale(self):
        xmin = self.vertices[0::3].min()
        xmax = self.vertices[0::3].max()
        ymin = self.vertices[1::3].min()
        ymax = self.vertices[1::3].max()

        xdom = xmax - xmin
        ydom = ymax - ymin
        
        self.diameter_xy = math.sqrt(xdom * xdom + ydom * ydom)
        self.radius_xy = self.diameter_xy / 2.0

    def _set_constats(self):
        self.light_position = np.array([500.0, 500.0, 400.0], dtype=np.float32)
        self.light_color = np.array([1.0, 1.0, 1.0], dtype=np.float32)
        self.loop_counter = 120

    # Setup geometry
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
    
    def _create_lines(self):    
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
        glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, 36, ctypes.c_void_p(0))

        # Color
        glEnableVertexAttribArray(1) # 1 is the layout location for the vertex shader
        glVertexAttribPointer(1, 3, GL_FLOAT, GL_FALSE, 36, ctypes.c_void_p(12))

        glBindVertexArray(0)

    # Setup frambuffer for shadow map    
    def _create_shadow_map(self):
        # Frambuffer for the shadow map
        self.FBO = glGenFramebuffers(1)
        glGenTextures(1, self.FBO)

        # Creating a texture which will be used as the framebuffers depth buffer
        self.depth_map = glGenTextures(1)
        glBindTexture(GL_TEXTURE_2D, self.depth_map)
        self.shadow_map_resolution = 1024 * 8
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

    # Setup shaders
    def _create_shader_lines(self):
        self._bind_vao_lines()
        self.shader_lines = compileProgram(compileShader(vertex_shader_lines, GL_VERTEX_SHADER), 
                                           compileShader(fragment_shader_lines, GL_FRAGMENT_SHADER))
        glUseProgram(self.shader_lines)

        self.mloc_lines = glGetUniformLocation(self.shader_lines, "model")
        self.ploc_lines = glGetUniformLocation(self.shader_lines, "project")
        self.vloc_lines = glGetUniformLocation(self.shader_lines, "view")
        self.cb_loc_lines = glGetUniformLocation(self.shader_lines, "color_by")
        
    def _create_shader_basic(self):
        self._bind_vao_triangels()
        self.shader_basic = compileProgram(compileShader(vertex_shader_basic, GL_VERTEX_SHADER), 
                                               compileShader(fragment_shader_basic, GL_FRAGMENT_SHADER))

        glUseProgram(self.shader_basic)

        self.mloc_basic = glGetUniformLocation(self.shader_basic, "model")
        self.ploc_basic = glGetUniformLocation(self.shader_basic, "project")
        self.vloc_basic = glGetUniformLocation(self.shader_basic, "view")
        self.cb_loc_basic = glGetUniformLocation(self.shader_basic, "color_by")

    def _create_shader_fancy(self):
        self._bind_vao_triangels()
        self.shader_fancy = compileProgram(compileShader(vertex_shader_fancy, GL_VERTEX_SHADER), 
                                               compileShader(fragment_shader_fancy, GL_FRAGMENT_SHADER))

        glUseProgram(self.shader_fancy)

        self.mloc_fancy = glGetUniformLocation(self.shader_fancy, "model")
        self.ploc_fancy = glGetUniformLocation(self.shader_fancy, "project")
        self.vloc_fancy = glGetUniformLocation(self.shader_fancy, "view")
        self.cb_loc_fancy = glGetUniformLocation(self.shader_fancy, "color_by")

        self.oc_loc_fancy = glGetUniformLocation(self.shader_fancy, "object_color")
        self.lc_loc_fancy = glGetUniformLocation(self.shader_fancy, "light_color")
        self.lp_loc_fancy = glGetUniformLocation(self.shader_fancy, "light_position")
        self.vp_loc_fancy = glGetUniformLocation(self.shader_fancy, "view_position")

    def _create_shader_fancy_shadow(self):
        self._bind_vao_triangels()
        self.shader_fancy_shadows = compileProgram(compileShader(vertex_shader_fancy_shadow, GL_VERTEX_SHADER), 
                                               compileShader(fragment_shader_fancy_shadow, GL_FRAGMENT_SHADER))

        glUseProgram(self.shader_fancy_shadows)

        self.mloc_fancy_shadows = glGetUniformLocation(self.shader_fancy_shadows, "model")
        self.ploc_fancy_shadows = glGetUniformLocation(self.shader_fancy_shadows, "project")
        self.vloc_fancy_shadows = glGetUniformLocation(self.shader_fancy_shadows, "view")
        self.cb_loc_fancy_shadows = glGetUniformLocation(self.shader_fancy_shadows, "color_by")

        self.oc_loc_fancy_shadows = glGetUniformLocation(self.shader_fancy_shadows, "object_color")
        self.lc_loc_fancy_shadows = glGetUniformLocation(self.shader_fancy_shadows, "light_color")
        self.lp_loc_fancy_shadows = glGetUniformLocation(self.shader_fancy_shadows, "light_position")
        self.vp_loc_fancy_shadows = glGetUniformLocation(self.shader_fancy_shadows, "view_position")
        self.lsm_loc_fancy_shadows = glGetUniformLocation(self.shader_fancy_shadows, "light_space_matrix")

    def _create_shader_shadow_map(self):
        self.shader_shadow_map = compileProgram(compileShader(vertex_shader_shadow_map, GL_VERTEX_SHADER), 
                                            compileShader(fragment_shader_shadow_map, GL_FRAGMENT_SHADER))
        
        glUseProgram(self.shader_shadow_map)
        
        self.mloc_shadow_map = glGetUniformLocation(self.shader_shadow_map, "model")
        self.lsm_loc_shadow_map = glGetUniformLocation(self.shader_shadow_map, "light_space_matrix")
        
    # Private render functions    
    def _render_shadow_map(self, interaction:Interaction):    
        #first pass: Capture shadow map
        rad = self.radius_xy
        if interaction.rotate:
            self.loop_counter += 1
            
        rot_step = self.loop_counter / 120.0    
        self.light_position = np.array([math.sin(rot_step) * rad, math.cos(rot_step) * rad, abs(math.sin(rot_step/2.0)) * 0.7 * rad], dtype=np.float32)
        
        light_projection = pyrr.matrix44.create_orthogonal_projection(-rad, rad, -rad, rad, 0.1, 1.25 * self.diameter_xy, dtype=np.float32)   
        look_target = np.array([0, 0, 0], dtype=np.float32)
        global_up = np.array([0, 0, 1], dtype= np.float32)
        light_view = pyrr.matrix44.create_look_at(self.light_position, look_target, global_up, dtype= np.float32)
        self.light_space_matrix = pyrr.matrix44.multiply(light_view, light_projection) # Other order? 
        glUseProgram(self.shader_shadow_map)
        glUniformMatrix4fv(self.lsm_loc_shadow_map, 1, GL_FALSE, self.light_space_matrix)

        translation = pyrr.matrix44.create_from_translation(pyrr.Vector3([0, 0, 0]))
        glUniformMatrix4fv(self.mloc_shadow_map, 1, GL_FALSE, translation)

        glViewport(0,0,self.shadow_map_resolution, self.shadow_map_resolution)
        glBindFramebuffer(GL_FRAMEBUFFER, self.FBO)
        glClear(GL_DEPTH_BUFFER_BIT)                # Only clearing depth buffer since there is no color attachement
        
        #Drawcall
        self._bind_vao_triangels()
        glDrawElements(GL_TRIANGLES, len(self.face_indices), GL_UNSIGNED_INT, None)
        self._unbind_vao()
            
    def _render_model_with_shadows(self, interaction:Interaction):

        glBindFramebuffer(GL_FRAMEBUFFER, 0)        #Setting default buffer
        glViewport(0,0, interaction.width, interaction.height)
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        glUseProgram(self.shader_fancy_shadows)
        
        translation = pyrr.matrix44.create_from_translation(pyrr.Vector3([0, 0, 0]))
        glUniformMatrix4fv(self.mloc_fancy_shadows, 1, GL_FALSE, translation)

        #Camera input
        view = interaction.camera.get_view_matrix()
        proj = interaction.camera.get_perspective_matrix()
        glUniformMatrix4fv(self.ploc_fancy_shadows, 1, GL_FALSE, proj)
        glUniformMatrix4fv(self.vloc_fancy_shadows, 1, GL_FALSE, view)

        color_by = int(interaction.coloring)
        glUniform1i(self.cb_loc_fancy, color_by)

        #Set light uniforms
        glUniform3fv(self.lc_loc_fancy_shadows, 1, self.light_color)
        glUniform3fv(self.vp_loc_fancy_shadows, 1, interaction.camera.camera_pos)
        glUniform3fv(self.lp_loc_fancy_shadows, 1, self.light_position)
        
        glUniformMatrix4fv(self.lsm_loc_fancy_shadows, 1, GL_FALSE, self.light_space_matrix)

        glActiveTexture(GL_TEXTURE0)
        glBindTexture(GL_TEXTURE_2D, self.depth_map)    
        
        #Drawcall
        self._bind_vao_triangels()
        glDrawElements(GL_TRIANGLES, len(self.face_indices), GL_UNSIGNED_INT, None)
        self._unbind_vao()

    # Render mesh fancy shadows
    def render_fancy_shadows(self, interaction:Interaction):
        self._render_shadow_map(interaction)
        self._render_model_with_shadows(interaction) 

    # Render mesh fancy
    def render_fancy(self, interaction:Interaction):
        self._bind_vao_triangels()
        self._bind_shader_fancy()

        rad = self.radius_xy
        
        if interaction.rotate:
            self.loop_counter += 1
            
        rot_step = self.loop_counter / 120.0    
        self.light_position = np.array([math.sin(rot_step) * rad, math.cos(rot_step) * rad, abs(math.sin(rot_step/2.0)) * 0.7 * rad], dtype=np.float32)
        
        move = pyrr.matrix44.create_from_translation(pyrr.Vector3([0, 0, 0]))
        glUniformMatrix4fv(self.mloc_fancy, 1, GL_FALSE, move)

        view = interaction.camera.get_view_matrix()
        glUniformMatrix4fv(self.vloc_fancy, 1, GL_FALSE, view)

        projection = interaction.camera.get_perspective_matrix()
        glUniformMatrix4fv(self.ploc_fancy, 1, GL_FALSE, projection)

        color_by = int(interaction.coloring)
        glUniform1i(self.cb_loc_fancy, color_by)

        view_pos = interaction.camera.camera_pos
        glUniform3fv(self.vp_loc_fancy_shadows, 1, view_pos)

        #Set light uniforms
        glUniform3fv(self.lc_loc_fancy, 1, self.light_color)
        glUniform3fv(self.lp_loc_fancy, 1, self.light_position)
        
        glDrawElements(GL_TRIANGLES, len(self.face_indices), GL_UNSIGNED_INT, None)

        self._unbind_vao()
        self._unbind_shader()

    # Render mesh basic
    def render_basic(self, interaction:Interaction):
        self._bind_vao_triangels()
        self._bind_shader_basic()

        move = pyrr.matrix44.create_from_translation(pyrr.Vector3([0, 0, 0]))
        glUniformMatrix4fv(self.mloc_basic, 1, GL_FALSE, move)
                
        view = interaction.camera.get_view_matrix()
        glUniformMatrix4fv(self.vloc_basic, 1, GL_FALSE, view)

        projection = interaction.camera.get_perspective_matrix()
        glUniformMatrix4fv(self.ploc_basic, 1, GL_FALSE, projection)

        color_by = int(interaction.coloring)
        glUniform1i(self.cb_loc_basic, color_by)

        glDrawElements(GL_TRIANGLES, len(self.face_indices), GL_UNSIGNED_INT, None)

        self._unbind_vao()
        self._unbind_shader()

    # Render mesh lines    
    def render_lines(self, interaction:Interaction):
        self._bind_vao_lines()
        self._bind_shader_lines()

        projection = interaction.camera.get_perspective_matrix()
        glUniformMatrix4fv(self.ploc_lines, 1, GL_FALSE, projection)
        
        view = interaction.camera.get_view_matrix()
        glUniformMatrix4fv(self.vloc_lines, 1, GL_FALSE, view)

        color_by = int(interaction.coloring)
        glUniform1i(self.cb_loc_lines, color_by)

        glDrawElements(GL_LINES, len(self.edge_indices), GL_UNSIGNED_INT, None)

        self._unbind_vao()
        self._unbind_shader()

    def _bind_vao_triangels(self):
        glBindVertexArray(self.VAO_triangels)

    def _bind_vao_lines(self):
        glBindVertexArray(self.VAO_edge)

    def _unbind_vao(self):
        glBindVertexArray(0)

    def _bind_shader_lines(self):
        glUseProgram(self.shader_lines)

    def _bind_shader_fancy_shadows(self):
        glUseProgram(self.shader_fancy_shadows)

    def _bind_shader_fancy(self):
        glUseProgram(self.shader_fancy)

    def _bind_shader_basic(self):
        glUseProgram(self.shader_basic)

    def _bind_shader_shadow_map(self):
        glUseProgram(self.shader_shadow_map)

    def _unbind_shader(self):
        glUseProgram(0)
