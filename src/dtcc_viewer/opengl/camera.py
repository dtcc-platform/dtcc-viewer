import numpy as np
from pyrr import Vector3, vector, vector3, matrix44
from math import sin, cos, radians
from dtcc_viewer.opengl.parameters import GuiParametersGlobal
from dtcc_viewer.opengl.utils import CameraProjection, CameraView, BoundingBox
from dtcc_viewer.logging import info, warning


class Camera:
    """Camera used for viewing geometry and navigation in a GLFW window.

    This class defines a camera with various attributes and methods for controlling
    its position, orientation, and view matrix.

    Attributes
    ----------
    position : Vector3
        The position of the camera.
    front : Vector3
        The front direction vector of the camera.
    up : Vector3
        The up direction vector of the camera.
    right : Vector3
        The right direction vector of the camera.
    target : Vector3
        The target point the camera is looking at.
    direction : Vector3
        The direction from the camera to the target.
    distance_to_target : float
        The distance from the camera to the target.
    aspect_ratio : float
        The aspect ratio of the camera's viewport.
    near_plane : float
        The near clipping plane distance.
    far_plane : float
        The far clipping plane distance.
    fov : float
        The field of view of the camera in degrees.
    mouse_sensitivity : float
        The sensitivity of the camera to mouse movements.
    scroll_sensitivity : float
        The sensitivity of the camera to scroll movements.
    yaw : float
        The yaw angle of the camera.
    pitch : float
        The pitch angle of the camera.
    init_camera : dict
        The initial camera settings saved for reset.
    rotation_lock : bool
        Whether the camera's rotation is locked.
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
    yaw: float
    pitch: float
    init_camera: dict

    rotation_lock: bool

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
        self.near_plane = 10.0
        self.far_plane = 1000000
        self.fov = 25
        self.mouse_sensitivity = -0.25
        self.scroll_sensitivity = -0.1

        # Set initial view properties
        self.distance_to_target = 500.0
        self.yaw = -90
        self.pitch = 30
        self.init_camera = None
        self.rotation_lock = False

        self.update_camera_vectors()

    def calc_near_far_planes(self, bb_global: BoundingBox):
        """Calculate the near and far clipping plane distances based on the bounding box.

        Parameters
        ----------
        bb_global : list
            The global bounding box of the geometry.
        """

        # Near and far plane scale factor are determined by testing
        self.near_plane = 0.0002 * bb_global.size
        self.far_plane = 20.0 * bb_global.size
        info(f"Near plane: {self.near_plane:.5f} m, Far plane: {self.far_plane:.0f} m.")

    def save_init_camera(self):
        self.init_camera = {}
        self.init_camera["dtt"] = self.distance_to_target
        self.init_camera["target"] = self.target
        self.init_camera["position"] = self.position
        self.init_camera["front"] = self.front
        self.init_camera["up"] = self.up
        self.init_camera["right"] = self.right
        self.init_camera["yaw"] = self.yaw
        self.init_camera["pitch"] = self.pitch
        self.init_camera["fov"] = self.fov

    def reset_init_camera(self):
        if self.init_camera is not None:
            self.rotation_lock = False
            self.distance_to_target = self.init_camera["dtt"]
            self.target = self.init_camera["target"]
            self.position = self.init_camera["position"]
            self.front = self.init_camera["front"]
            self.up = self.init_camera["up"]
            self.right = self.init_camera["right"]
            self.yaw = self.init_camera["yaw"]
            self.pitch = self.init_camera["pitch"]
            self.fov = self.init_camera["fov"]
            self.update_camera_vectors()

    def toggle_rotation_lock(self):
        self.rotation_lock = not self.rotation_lock

    def _set_top_view(self):
        """Set the camera to a top-down view."""
        self.rotation_lock = True
        self.yaw = -90
        self.pitch = 89.99
        self.update_camera_vectors()

    def _set_front_view(self):
        """Set the camera to a front view."""
        self.rotation_lock = True
        self.target[2] = 0.0
        self.yaw = -90
        self.pitch = 0
        self.update_camera_vectors()

    def _set_back_view(self):
        """Set the camera to a back view."""
        self.rotation_lock = True
        self.target[2] = 0.0
        self.yaw = 90
        self.pitch = 0
        self.update_camera_vectors()

    def _set_left_view(self):
        """Set the camera to a left-side view."""
        self.rotation_lock = True
        self.target[2] = 0.0
        self.yaw = 180
        self.pitch = 0
        self.update_camera_vectors()

    def _set_right_view(self):
        """Set the camera to a right-side view."""
        self.rotation_lock = True
        self.target[2] = 0.0
        self.yaw = 0
        self.pitch = 0
        self.update_camera_vectors()

    def _set_persepective_view(self):
        """Set the camera to a perspective view."""
        self.rotation_lock = False
        self.yaw = -90
        self.pitch = 30
        self.update_camera_vectors()

    def update_view(self, camera_view: CameraView):
        """Update the camera view based on the specified view type.

        Parameters
        ----------
        camera_view : CameraView
            The desired camera view type.
        """
        if camera_view == CameraView.PERSPECTIVE:
            self._set_persepective_view()
        elif camera_view == CameraView.TOP:
            self._set_top_view()
        elif camera_view == CameraView.FRONT:
            self._set_front_view()
        elif camera_view == CameraView.BACK:
            self._set_back_view()
        elif camera_view == CameraView.LEFT:
            self._set_left_view()
        elif camera_view == CameraView.RIGHT:
            self._set_right_view()

    def zoom_selected(self, dtt: float, new_target: Vector3):
        """Zoom in on the selected target.

        Parameters
        ----------
        dtt : float
            The distance to the target.
        new_target : Vector3
            The new target position.
        """
        self.target = new_target
        self.distance_to_target = dtt
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
        print(f"Camera jaw angle: {self.yaw}")
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

    def _get_perspective_view_matrix(self) -> None:
        """Get the view matrix of the camera.

        Returns
        -------
        matrix44
            The view matrix of the camera.
        """
        return matrix44.create_look_at(self.position, self.target, self.up)

    def _get_orthographic_view_matrix(self) -> None:
        """Get the view matrix of the camera.

        Returns
        -------
        matrix44
            The view matrix of the camera.
        """
        # return matrix44.inverse(matrix44.create_from_translation(-self.position))
        return matrix44.create_look_at(self.position, self.target, self.up)

    def get_view_matrix(self, guip: GuiParametersGlobal):
        if guip.camera_projection == CameraProjection.PERSPECTIVE:
            return self._get_perspective_view_matrix()
        elif guip.camera_projection == CameraProjection.ORTHOGRAPHIC:
            return self._get_orthographic_view_matrix()
        else:
            return None

    def _get_perspective_matrix(self) -> np.ndarray[any]:
        """Get the perspective projection matrix of the camera.

        Returns
        -------
        matrix44
            The perspective projection matrix of the camera.
        """
        return matrix44.create_perspective_projection(
            self.fov,
            self.aspect_ratio,
            self.near_plane,
            self.far_plane,
        )

    def _get_orthographic_matrix(self) -> np.ndarray[any]:
        """Get the orthographic projection matrix of the camera.

        Returns
        -------
        matrix44
            The orthographic projection matrix of the camera.
        """
        size = self.distance_to_target / 5.0

        return matrix44.create_orthogonal_projection(
            -self.aspect_ratio * size,
            self.aspect_ratio * size,
            -1.0 * size,
            1.0 * size,
            -self.far_plane,
            self.far_plane,
        )

    def get_projection_matrix(self, guip: GuiParametersGlobal) -> np.ndarray[any]:
        """Get the projection matrix of the camera.

        Returns
        -------
        matrix44
            The projection matrix of the camera.
        """
        if guip.camera_projection == CameraProjection.PERSPECTIVE:
            return self._get_perspective_matrix()
        elif guip.camera_projection == CameraProjection.ORTHOGRAPHIC:
            return self._get_orthographic_matrix()
        else:
            return None

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

        if self.rotation_lock:
            return

        xoffset *= self.mouse_sensitivity
        yoffset *= self.mouse_sensitivity

        self.yaw += xoffset
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
        new_direction.x = cos(radians(self.yaw)) * cos(radians(self.pitch))
        new_direction.z = sin(radians(self.pitch))
        new_direction.y = sin(radians(self.yaw)) * cos(radians(self.pitch))

        self.position = dtt * vector.normalise(new_direction) + self.target
        self.direction = vector.normalise(self.target - self.position)
        self.right = vector.normalise(vector3.cross(self.direction, z_vec))
        self.up = vector.normalise(vector3.cross(self.right, self.direction))
