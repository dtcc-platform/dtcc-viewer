from dtcc_viewer.opengl.utils import BoundingBox
import numpy as np
import math


class Environment:
    """Object that has the environment properties and methods.

    This class defines an environment with various attributes and methods for
    controlling position and color for the light sources and scale of the model.
    """

    light_col: np.ndarray  # Light color
    light_pos: np.ndarray  # Light position
    bb_global: BoundingBox

    diameter_xy: float
    radius_xy: float

    loop_counter: int

    def __init__(self, bounding_box: BoundingBox):
        """Initialize the Enivornment object with the provided width and height."""

        self.light_col = np.array([1.0, 1.0, 1.0], dtype=np.float32)
        self.light_pos = np.array([500.0, 500.0, 400.0], dtype=np.float32)
        self.loop_counter = 120
        self.bb_global = bounding_box
        self._calc_scale()
        self._calc_light_position()

    def _calc_scale(self):
        """Calculate the model scale from vertex positions."""
        xdom = self.bb_global.xdom
        ydom = self.bb_global.ydom

        self.diameter_xy = math.sqrt(xdom * xdom + ydom * ydom)
        self.radius_xy = self.diameter_xy / 2.0

    def _calc_light_position(self) -> np.ndarray:
        """Calculate position animated position of light source which casts shadows."""

        rot_step = self.loop_counter / 120.0
        x = math.sin(rot_step) * self.radius_xy
        y = math.cos(rot_step) * self.radius_xy
        z = abs(math.sin(rot_step / 2.0)) * 0.7 * self.radius_xy
        self.light_pos = np.array([x, y, z], dtype=np.float32)

        self.loop_counter += 1
