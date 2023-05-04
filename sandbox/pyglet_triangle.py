from pyglet.gl import *
import OpenGL.GL.shaders
import ctypes 

class Triangle:
    def __init__(self):

        self.triangle = [-0.5, -0.5, 0.0, 1.0, 0.0, 0.0,
                          0.5, -0.5, 0.0, 0.0, 1.0, 0.0,
                          0.0,  0.5, 0.0, 0.0, 0.0, 1.0]

        self.vertex_shader_source = """
        #version 330
        in layout(location = 0) vec3 position;
        in layout(location = 1) vec3 color;
        
        out vec3 newColor;
        void main()
        {
            gl_Position = vec4(position, 1.0f);
            newColor = color;
        } 
        """ 

        self.fragment_shader_source = """
        #version 330
        in vec3 newColor;    
        
        out vec4 outColor;
        void main()
        {
            outColor = vec4(newColor, 1.0f);
        }
        """

        # Attaching the chaders

        shader = OpenGL.GL.shaders.compileProgram(OpenGL.GL.shaders.compileShader(self.vertex_shader_source, GL_VERTEX_SHADER),
                                                  OpenGL.GL.shaders.compileShader(self.fragment_shader_source, GL_FRAGMENT_SHADER))
        

        glUseProgram(shader)

        vbo = GLuint(0)
        glGenBuffers(1, vbo)

        glBindBuffer(GL_ARRAY_BUFFER, vbo)      #Bind data
        glBufferData(GL_ARRAY_BUFFER, (6*3)*4, (GLfloat * len(self.triangle))(*self.triangle), GL_STATIC_DRAW)                          #Send data to GPU

        #positions
        glVertexAttribPointer(0 , 3, GL_FLOAT, GL_FALSE, 24, ctypes.c_void_p(0))    # 6 * (4 bytes)
        glEnableVertexAttribArray(0)

        #colors
        glVertexAttribPointer(1 , 3, GL_FLOAT, GL_FALSE, 24, ctypes.c_void_p(12))    # Color startes at an offset of 3 * 4 bytes
        glEnableVertexAttribArray(0)





