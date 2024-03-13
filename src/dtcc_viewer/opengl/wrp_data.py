import numpy as np
import math
from dtcc_viewer.logging import info, warning
from dtcc_model import Mesh


class DataWrapper:
    """Wrapper class for data to be used in OpenGL.

    Takes an 1d array of data and transforms it into a 2d array where the width is
    the max_texture_size. This is necessary for OpenGL to handle large data sets
    as 2d textures.
    """

    data_as_mat: list[np.ndarray]  # Data in a 2d array to be mapped to a texture
    data_mat_dict: dict  # Dictionary of data matrices
    texel_x: np.ndarray  # Texel indices for x
    texel_y: np.ndarray  # Texel indices for y
    row_count: int  # Number of rows in the data
    col_count: int  # Number of columns in the data
    v_count: int  # Number of vertices in the mesh
    f_count: int  # Number of faces in the mesh
    new_v_count: int  # Number of vertices in the restructured mesh
    max_tex_size: int  # Max texture size

    def __init__(
        self,
        mesh: Mesh,
        mts: int,
    ) -> None:

        self.data_mat_dict = {}
        self.max_tex_size = mts
        self.v_count = len(mesh.vertices)
        self.f_count = len(mesh.faces)
        self.mesh = mesh
        (self.row_count, self.col_count) = self._calc_matrix_format()

        self._calc_texel_indices()

    def add_data(self, name: str, data: np.ndarray):
        data_mat = self._process_data(data)

        if data_mat is not None:
            self.data_mat_dict[name] = data_mat
            info(f"Data called {name} was added to data dictionary.")
        else:
            warning(f"Data called {name} was not added to data dictionary.")

    def get_keys(self) -> list[str]:
        return list(self.data_mat_dict.keys())

    def _calc_matrix_format(self):
        nv_count = self.f_count * 3
        row_count = math.ceil(nv_count / self.max_tex_size)
        col_count = self.max_tex_size
        return (row_count, col_count)

    def _process_data(self, data: np.ndarray):
        """Check so the data count matches the vertex or face count."""

        if len(data) != self.v_count:  # TODO: Allow data to be associated with faces
            warning(f"Data count does not match vertex or face count.")
            return None
        else:
            data_res = data[self.mesh.faces.flatten()]  # Restructure the data
            data_mat = self._reformat_data_for_texture(data_res)
            return data_mat

    def _reformat_data_for_texture(self, data: np.ndarray):
        mts = self.max_tex_size
        new_data = np.zeros((self.row_count, self.col_count))
        new_data = new_data.flatten()
        new_data[0 : len(data)] = data
        new_data = np.reshape(new_data, (self.row_count, self.col_count))
        new_data = np.array(new_data, dtype="float32")
        info(f"New data shape: {new_data.shape} for max texture size: {mts}")
        return new_data

    def _calc_texel_indices(self):
        # Set texture coordinates
        nv_count = self.f_count * 3
        print(nv_count)
        if nv_count < self.max_tex_size:
            texel_indices_x = np.arange(0, nv_count)
            texel_indices_y = np.zeros(nv_count)
        else:
            texel_indices_x = np.arange(0, self.max_tex_size)
            texel_indices_x = np.tile(texel_indices_x, self.row_count)[:nv_count]
            texel_indices_y = np.arange(0, self.row_count)
            texel_indices_y = np.repeat(texel_indices_y, self.max_tex_size)[:nv_count]

        self.texel_x = texel_indices_x
        self.texel_y = texel_indices_y
