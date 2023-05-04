from pyrr import Vector3, vector, vector3, matrix44
from math import sin, cos, radians



class camera:


    def __inint__(self):
        
        self.camera_pos = Vector3([0, 4, 3])
        self.camera_front = Vector3([0,0,-1])
        self.camera_up = Vector3([0,1,0])
        self.camera_right = Vector3([1,0,0]) 
        