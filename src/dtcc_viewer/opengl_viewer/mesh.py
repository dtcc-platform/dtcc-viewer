
import math
import glfw
import numpy as np
from OpenGL.GL import *
from OpenGL.GL.shaders import compileProgram, compileShader
import pyrr
from interaction import Interaction
from shaders import vertex_shader_lines, vertex_shader_triangels, fragment_shader_lines, fragment_shader_triangels
from loader import ObjLoader

class Mesh:
    
    def __init__(self, filename:str):
        self._load_mesh(filename)
        self._create_triangels()
        self._create_lines()
        self._create_shader_triangels()
        self._create_shader_lines()

    def _load_mesh(self, filename:str):
        [self.face_indices, vert_coord, vert_color, self.vertices, self.edge_indices] = ObjLoader.load_model(filename)


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
        glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, 24, ctypes.c_void_p(0))

        # Color
        glEnableVertexAttribArray(1) # 1 is the layout location for the vertex shader
        glVertexAttribPointer(1, 3, GL_FLOAT, GL_FALSE, 24, ctypes.c_void_p(12))

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
        glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, 24, ctypes.c_void_p(0))

        # Color
        glEnableVertexAttribArray(1) # 1 is the layout location for the vertex shader
        glVertexAttribPointer(1, 3, GL_FLOAT, GL_FALSE, 24, ctypes.c_void_p(12))

        glBindVertexArray(0)
    
    def _create_shader_triangels(self):
        self._bind_vao_triangels()
        self.shader_triangels = compileProgram(compileShader(vertex_shader_triangels, GL_VERTEX_SHADER), compileShader(fragment_shader_triangels, GL_FRAGMENT_SHADER))
        glUseProgram(self.shader_triangels)

        self.model_loc_triangels = glGetUniformLocation(self.shader_triangels, "model")
        self.project_loc_triangels = glGetUniformLocation(self.shader_triangels, "project")
        self.view_loc_triangels = glGetUniformLocation(self.shader_triangels, "view")
        self.color_by_loc_triangels = glGetUniformLocation(self.shader_triangels, "color_by")
    
    def _create_shader_lines(self):
        self._bind_vao_lines()
        self.shader_lines = compileProgram(compileShader(vertex_shader_lines, GL_VERTEX_SHADER), compileShader(fragment_shader_lines, GL_FRAGMENT_SHADER))
        glUseProgram(self.shader_lines)

        self.model_loc_lines = glGetUniformLocation(self.shader_lines, "model")
        self.project_loc_lines = glGetUniformLocation(self.shader_lines, "project")
        self.view_loc_lines = glGetUniformLocation(self.shader_lines, "view")
        self.color_by_loc_lines = glGetUniformLocation(self.shader_lines, "color_by")

    def render_triangels(self, interaction:Interaction):
        self._bind_vao_triangels()
        self._bind_shader_triangels()

        projection = interaction.camera.get_perspective_matrix()
        glUniformMatrix4fv(self.project_loc_triangels, 1, GL_FALSE, projection)
        
        view = interaction.camera.get_view_matrix()
        glUniformMatrix4fv(self.view_loc_triangels, 1, GL_FALSE, view)

        color_by = int(interaction.coloring)
        glUniform1i(self.color_by_loc_triangels, color_by)

        glDrawElements(GL_TRIANGLES, len(self.face_indices), GL_UNSIGNED_INT, None)

        self._unbind_vao()
        self._unbind_shader()
        
    def render_lines(self, interaction:Interaction):
        self._bind_vao_lines()
        self._bind_shader_lines()

        projection = interaction.camera.get_perspective_matrix()
        glUniformMatrix4fv(self.project_loc_lines, 1, GL_FALSE, projection)
        
        view = interaction.camera.get_view_matrix()
        glUniformMatrix4fv(self.view_loc_lines, 1, GL_FALSE, view)

        color_by = int(interaction.coloring)
        glUniform1i(self.color_by_loc_lines, color_by)

        glDrawElements(GL_LINES, len(self.edge_indices), GL_UNSIGNED_INT, None)

        self._unbind_vao()
        self._unbind_shader()

    def _bind_vao_triangels(self):
        glBindVertexArray(self.VAO_triangels)

    def _bind_vao_lines(self):
        glBindVertexArray(self.VAO_edge)

    def _unbind_vao(self):
        glBindVertexArray(0)

    def _bind_shader_triangels(self):
        glUseProgram(self.shader_triangels)

    def _bind_shader_lines(self):
        glUseProgram(self.shader_lines)

    def _unbind_shader(self):
        glUseProgram(0)