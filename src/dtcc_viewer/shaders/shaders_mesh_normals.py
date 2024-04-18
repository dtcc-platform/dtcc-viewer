vertex_shader_normals = """
#version 330 core

layout(location=0) in vec3 a_position;
layout(location=1) in vec2 a_texels;
layout(location=2) in vec3 a_normal;
layout(location=2) in float a_id;

uniform float clip_x;
uniform float clip_y;
uniform float clip_z;

out vec3 normal;

void main() 
{
    vec4 clippingPlane1 = vec4(-1, 0, 0, clip_x);
	vec4 clippingPlane2 = vec4(0, -1, 0, clip_y);
	vec4 clippingPlane3 = vec4(0, 0, -1, clip_z);
    
    vec4 world_pos = vec4(a_position, 1.0);
    
    gl_ClipDistance[0] = dot(world_pos, clippingPlane1);
    gl_ClipDistance[1] = dot(world_pos, clippingPlane2);
    gl_ClipDistance[2] = dot(world_pos, clippingPlane3);

    gl_Position = world_pos;
    normal = a_normal;
}
"""

geometry_shader_vertexnormals = """ 
#version 330 core

layout(triangles) in;
layout(line_strip, max_vertices = 6) out;

uniform mat4 model;
uniform mat4 view;
uniform mat4 project;

in vec3 normal[];

void main() 
{

    mat4 mvp = project * view * model;

    for (int i = 0; i < 3; i++) {
        
        // Only draw the normal if the vertex is not clipped
        if (gl_in[i].gl_ClipDistance[0] > 0.0 && 
            gl_in[i].gl_ClipDistance[1] > 0.0 && 
            gl_in[i].gl_ClipDistance[2] > 0.0) 
        {        
            // Draw a line from the vertex to represent the normal
            vec4 startPos = mvp * gl_in[i].gl_Position;
            gl_Position = startPos; 
            EmitVertex();

            vec3 vertexNormal = normal[i];
            vec3 vertexPosition = gl_in[i].gl_Position.xyz;

            vec4 endPos = mvp * vec4((vertexPosition + vertexNormal * 5.0), 1.0);
            gl_Position = endPos;
            EmitVertex();

            EndPrimitive();
        }
    }
}
"""

geometry_shader_facenormals = """ 
#version 330 core

layout(triangles) in;
layout(line_strip, max_vertices = 2) out;

uniform mat4 model;
uniform mat4 view;
uniform mat4 project;

in vec3 normal[];

void main() 
{   
    // Only draw the normal if all the vertices are in front of the camera
    for (int i = 0; i < 3; ++i) {
        if (gl_in[i].gl_ClipDistance[0] < 0.0 || 
            gl_in[i].gl_ClipDistance[1] < 0.0 || 
            gl_in[i].gl_ClipDistance[2] < 0.0) {
            return;
        }
    }

    mat4 mvp = project * view * model;

    vec3 faceCenter = (gl_in[0].gl_Position.xyz + gl_in[1].gl_Position.xyz + gl_in[2].gl_Position.xyz) / 3.0;
    vec4 lineStart = mvp *  vec4(faceCenter, 1.0);
    gl_Position = lineStart;
    EmitVertex();

    vec3 faceNormal = (normal[0] + normal[1] + normal[2]) / 3.0; 
    vec4 lineEnd = mvp * vec4((faceCenter + faceNormal * 5.0), 1.0);
    gl_Position = lineEnd;
    EmitVertex();

    EndPrimitive();
}
"""

fragment_shader_normals = """ 
#version 330 core

layout(location=0) out vec4 FragColor;

void main() 
{
    FragColor = vec4(1,0,1,1);
}
"""
