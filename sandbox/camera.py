from pyrr import Vector3, vector, vector3, matrix44
from math import sin, cos, radians



class Camera:

    def __init__(self, aspect_ratio):        
        self.camera_pos = Vector3([0.0, 10.0, 3.0])
        self.camera_front = Vector3([0.0, 0.0, -1.0])
        self.camera_up = Vector3([0.0, 0.0, 1.0])
        self.camera_right = Vector3([1.0, 0.0, 0.0])
        self.camera_target = Vector3([0.0, 0.0, 0.0]) 
        self.camera_direction = Vector3([0.0, 0.0, 0.0])
        self.distance_to_target = 10.0

        self.aspect_ratio = aspect_ratio
        self.near_plane = 0.1
        self.far_plane = 10000
        self.fov = 25
        self.mouse_sensitivity = -0.25
        self.scroll_sensitivity = -3.5
        self.jaw = -90
        self.pitch = 0
    

    def get_view_matrix(self):
        return matrix44.create_look_at(self.camera_pos, self.camera_target, self.camera_up)

    def get_perspective_matrix(self):
        return matrix44.create_perspective_projection(self.fov, self.aspect_ratio, self.near_plane, self.far_plane)

    def process_mouse_movement(self, xoffset, yoffset, constrain_pitch = True):
        xoffset *= self.mouse_sensitivity
        yoffset *= self.mouse_sensitivity

        self.jaw += xoffset
        self.pitch += yoffset

        if constrain_pitch:
            if self.pitch > 89.99:
                self.pitch = 89.99
            if self.pitch < -89.99:
                self.pitch = -89.99    

        self.update_camera_vectors()

    def process_scroll_movement(self, xoffset, yoffset, constrain_pitch = True):
        
        self.distance_to_target += self.scroll_sensitivity * yoffset
        
        #xoffset *= self.scroll_sensitivity
        #yoffset *= self.scroll_sensitivity
        
        self.update_camera_vectors()


    def update_camera_vectors(self):
        new_direction = Vector3([0.0, 0.0, 0.0])
        new_direction.x = cos(radians(self.jaw)) * cos(radians(self.pitch))
        new_direction.z = sin(radians(self.pitch))
        new_direction.y = sin(radians(self.jaw)) * cos(radians(self.pitch))

        self.camera_pos = self.distance_to_target * vector.normalise(new_direction)

        self.camera_direction = vector.normalise(self.camera_target - self.camera_pos)
        self.camera_right = vector.normalise(vector3.cross(self.camera_direction, Vector3([0.0, 0.0, 1.0])))
        self.camera_up = vector.normalise(vector3.cross(self.camera_right, self.camera_direction))

    


        
        

        