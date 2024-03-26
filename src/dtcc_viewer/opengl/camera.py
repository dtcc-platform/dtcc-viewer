import numpy as np
from pyrr import Vector3, vector, vector3, matrix44
from math import sin, cos, radians


class Camera:
    """Camera used for viewing geometry and nagivation in a GLFW window.

    This class defines a camera with various attributes and methods for controlling
    its position, orientation, and view matrix.

    Attributes
    ----------
    camera_pos : Vector3
        The position of the camera.
    camera_front : Vector3
        The front direction of the camera.
    camera_up : Vector3
        The up direction of the camera.
    camera_right : Vector3
        The right direction of the camera.
    camera_target : Vector3
        The target point that the camera is looking at.
    camera_direction : Vector3
        The direction vector from the camera position to the target.
    distance_to_target : float
        The distance from the camera position to the target.
    width : int
        The width of the camera's viewport.
    heigh : int
        The height of the camera's viewport.
    aspect_ratio : float
        The aspect ratio of the camera's viewport.
    near_plane : float
        The near clipping plane distance.
    far_plane : float
        The far clipping plane distance.
    fov : int
        The field of view angle.
    mouse_sensitivity : float
        The sensitivity of mouse movement for rotation.
    scroll_sensitivity : float
        The sensitivity of mouse scroll for zooming.
    jaw : int
        The yaw rotation angle.
    pitch : int
        The pitch rotation angle.
    """

    postion: Vector3
    front: Vector3
    up: Vector3
    right: Vector3
    target: Vector3
    direction: Vector3

    distance_to_target: float
    aspect_ratio: float
    near_plane: float
    far_plane: float
    fov: float
    mouse_sensitivity: float
    scroll_sensitivity: float
    jaw: float
    pitch: float

    def __init__(self, width, height):
        """Initialize the Camera object with the provided width and height.

        Parameters
        ----------
        width : int
            The width of the viewport.
        height : int
            The height of the viewport.
        """

        self.position = Vector3([0.0, 10.0, 10.0])
        self.front = Vector3([0.0, 0.0, -1.0])
        self.up = Vector3([0.0, 0.0, 1.0])
        self.right = Vector3([1.0, 0.0, 0.0])
        self.target = Vector3([0.0, 0.0, 0.0])
        self.direction = Vector3([0.0, 0.0, 0.0])

        self.aspect_ratio = float(width) / float(height)
        self.near_plane = 0.1
        self.far_plane = 1000000
        self.fov = 25
        self.mouse_sensitivity = -0.25
        self.scroll_sensitivity = -0.1

        # Set initial view properties
        self.distance_to_target = 500.0
        self.jaw = -90
        self.pitch = 30

        self.update_camera_vectors()

    def print(self):
        print("Camera settings:")
        print(f"Camera position: {self.position}")
        print(f"Camera front vector: {self.front}")
        print(f"Camera up vector: {self.up}")
        print(f"Camera right vector: {self.front}")
        print(f"Camera target: {self.target}")
        print(f"Camera direction vector: {self.direction}")
        print(f"Camera distance to target: {self.distance_to_target}")
        print(f"Camera jaw angle: {self.jaw}")
        print(f"Camera pitch angle: {self.pitch}")

    def update_window_aspect_ratio(self, width, height) -> None:
        """Update the camera's viewport dimensions.

        Parameters
        ----------
        width : int
            The new width of the viewport.
        height : int
            The new height of the viewport.
        """
        self.aspect_ratio = float(width) / float(height)

    def set_aspect_ratio(self, aspect_ratio) -> None:
        """Set the camera's aspect ratio.

        Parameters
        ----------
        aspect_ratio : float
            The new aspect ratio value.
        """
        self.aspect_ratio = aspect_ratio

    def get_view_matrix(self) -> None:
        """Get the view matrix of the camera.

        Returns
        -------
        matrix44
            The view matrix of the camera.
        """
        return matrix44.create_look_at(self.position, self.target, self.up)

    def get_perspective_matrix(self) -> np.ndarray[any]:
        """Get the perspective projection matrix of the camera.

        Returns
        -------
        matrix44
            The perspective projection matrix of the camera.
        """
        return matrix44.create_perspective_projection(
            self.fov, self.aspect_ratio, self.near_plane, self.far_plane
        )

    def get_move_matrix(self):
        """Get the move matrix which positions the object around the origin.

        Returns
        -------
        matrix44
            The move matrix.
        """
        return matrix44.create_from_translation(Vector3([0, 0, 0]))

    def process_mouse_rotation(
        self, xoffset: float, yoffset: float, constrain_pitch=True
    ) -> None:
        """Process mouse movement for camera rotation.

        Parameters
        ----------
        xoffset : float
            The horizontal mouse movement offset.
        yoffset : float
            The vertical mouse movement offset.
        constrain_pitch : bool, optional
            Whether to constrain the pitch rotation, by default True.
        """
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

    def process_mouse_panning(self, xoffset: float, yoffset: float) -> None:
        """Process mouse movement for camera panning.

        Parameters
        ----------
        xoffset : float
            The horizontal mouse movement offset.
        yoffset : float
            The vertical mouse movement offset.
        """
        panning_sensitivity = self.distance_to_target / 2400
        pan_vector_right = (xoffset * panning_sensitivity) * self.right
        pan_vector_up = (yoffset * panning_sensitivity) * self.up

        self.position += pan_vector_right + pan_vector_up
        self.target += pan_vector_right + pan_vector_up

        self.direction = vector.normalise(self.target - self.position)
        self.right = vector.normalise(
            vector3.cross(self.direction, Vector3([0.0, 0.0, 1.0]))
        )
        self.up = vector.normalise(vector3.cross(self.right, self.direction))

    def process_scroll_movement(
        self, xoffset: float, yoffset: float, constrain_pitch: bool = True
    ) -> None:
        """Process mouse scroll for adjusting camera distance.

        Parameters
        ----------
        xoffset : float
            The horizontal mouse scroll offset.
        yoffset : float
            The vertical mouse scroll offset.
        constrain_pitch : bool, optional
            Whether to constrain the pitch rotation, by default True.
        """
        self.distance_to_target += self.scroll_sensitivity * yoffset
        self.scroll_sensitivity = -0.1 - 0.02 * self.distance_to_target
        self.update_camera_vectors()

    def update_camera_vectors(self) -> None:
        """Update the camera's direction and orientation based on angles.

        Returns
        -------
        None
        """
        z_vec = Vector3([0.0, 0.0, 1.0])
        dtt = self.distance_to_target

        new_direction = Vector3([0.0, 0.0, 0.0])
        new_direction.x = cos(radians(self.jaw)) * cos(radians(self.pitch))
        new_direction.z = sin(radians(self.pitch))
        new_direction.y = sin(radians(self.jaw)) * cos(radians(self.pitch))

        self.position = dtt * vector.normalise(new_direction) + self.target
        self.direction = vector.normalise(self.target - self.position)
        self.right = vector.normalise(vector3.cross(self.direction, z_vec))
        self.up = vector.normalise(vector3.cross(self.right, self.direction))
