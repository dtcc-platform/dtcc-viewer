import numpy as np
import math
from dtcc_viewer.logging import info, warning


class DataWrapper:
    """Wrapper class for data to be used in OpenGL.

    Takes an 1d array of data and transforms it into a 2d array where the width is
    the max_texture_size. This is necessary for OpenGL to handle large data sets
    as 2d textures.
    """

    data: np.ndarray  # Data in a 2d array to be mapped to a texture
    texel_ix: np.ndarray  # Texel indices for x
    texel_iy: np.ndarray  # Texel indices for y

    def __init__(
        self,
        data: np.ndarray,
        max_tex_size: int,
        v_count: int,
        f_count: int,
    ) -> None:

        # The number of vertices in the restructured mesh
        new_v_count = f_count * 3

        if not self._data_is_matching(data, v_count, f_count):
            return

        self._reformat_texture_data(data, max_tex_size)
        self.get_texel_indices(max_tex_size, new_v_count)

    def _data_is_matching(self, data: np.ndarray, v_count: int, f_count: int):
        """Check so the data count matches the vertex or face count."""

        if len(data) != v_count and len(data) != f_count:
            warning(f"Data count does not match vertex or face count")
            return False
        return True

    def _reformat_texture_data(self, data: np.ndarray, max_tex_size: int):

        d_count = len(data)

        if d_count < max_tex_size:
            data = np.reshape(data, (1, d_count))
        else:
            row_count = math.ceil(len(data) / max_tex_size)
            new_data = np.zeros((row_count, max_tex_size))
            new_data = new_data.flatten()
            new_data[0:d_count] = data
            data = np.reshape(new_data, (row_count, max_tex_size))
            info(f"New data shape: {data.shape} for max texture size: {max_tex_size}")

        self.data = data

    def get_texel_indices(self, max_texture_size: int, new_v_count: int):
        # Set texture coordinates

        if new_v_count < max_texture_size:
            texel_indices_x = np.arange(0, new_v_count)
            texel_indices_y = np.zeros(new_v_count)
        else:
            row_count = math.ceil(new_v_count / max_texture_size)
            texel_indices_x = np.arange(0, max_texture_size)
            texel_indices_x = np.tile(texel_indices_x, row_count)[:new_v_count]
            texel_indices_y = np.arange(0, row_count)
            texel_indices_y = np.repeat(texel_indices_y, max_texture_size)[:new_v_count]

        self.texel_ix = texel_indices_x
        self.texel_iy = texel_indices_y
