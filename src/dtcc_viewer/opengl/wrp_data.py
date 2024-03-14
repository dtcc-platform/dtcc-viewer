import numpy as np
import math
from dtcc_viewer.logging import info, warning
from dtcc_model import Mesh
from dtcc_model import PointCloud
from abc import ABC, abstractmethod


class DataWrapper(ABC):

    data_mat_dict: dict  # Dictionary of data matrices
    data_value_caps: dict  # Dictionary of data value caps
    texel_x: np.ndarray  # Texel indices for x
    texel_y: np.ndarray  # Texel indices for y
    row_count: int  # Number of rows in the data
    col_count: int  # Number of columns in the data
    max_tex_size: int  # Max texture size

    @abstractmethod
    def add_data(self, name: str, data: np.ndarray):
        pass

    @abstractmethod
    def _process_data(self, name: str, data: np.ndarray):
        pass

    def _calc_matrix_format(self, d_count: int):
        self.row_count = math.ceil(d_count / self.max_tex_size)
        self.col_count = self.max_tex_size

    def get_keys(self) -> list[str]:
        return list(self.data_mat_dict.keys())

    def _reformat_data_for_texture(self, data: np.ndarray):
        new_data = np.zeros((self.row_count, self.col_count))
        new_data = new_data.flatten()
        new_data[0 : len(data)] = data
        new_data = np.reshape(new_data, (self.row_count, self.col_count))
        new_data = np.array(new_data, dtype="float32")
        info(f"New data shape: {new_data.shape}.")
        return new_data

    def _calc_texel_indices(self, d_count: int):
        # Set texture coordinates
        if d_count < self.max_tex_size:
            texel_indices_x = np.arange(0, d_count)
            texel_indices_y = np.zeros(d_count)
        else:
            texel_indices_x = np.arange(0, self.max_tex_size)
            texel_indices_x = np.tile(texel_indices_x, self.row_count)[:d_count]
            texel_indices_y = np.arange(0, self.row_count)
            texel_indices_y = np.repeat(texel_indices_y, self.max_tex_size)[:d_count]

        self.texel_x = texel_indices_x
        self.texel_y = texel_indices_y

        info(f"Texel indices for DataWrapper computed.")


class MeshDataWrapper(DataWrapper):
    """Wrapper class for mesh data to be used in OpenGL.

    Takes an 1d array of data and transforms it into a 2d array where the width is
    the max_texture_size. This is necessary for OpenGL to handle large data sets
    as 2d textures.
    """

    v_count: int  # Number of vertices in the mesh
    f_count: int  # Number of faces in the mesh
    new_v_count: int  # Number of vertices in the restructured mesh

    def __init__(self, mesh: Mesh, mts: int) -> None:

        self.data_mat_dict = {}
        self.data_value_caps = {}
        self.max_tex_size = mts
        self.v_count = len(mesh.vertices)
        self.f_count = len(mesh.faces)
        self.mesh = mesh

        # new vertex count for restructured mesh
        nv_count = self.f_count * 3
        d_count = nv_count
        self._calc_matrix_format(d_count)
        self._calc_texel_indices(d_count)

    def add_data(self, name: str, data: np.ndarray):
        (data_mat, val_caps) = self._process_data(data)

        if (data_mat is not None) and (val_caps is not None):
            self.data_mat_dict[name] = data_mat
            self.data_value_caps[name] = val_caps
            info(f"Data called {name} was added to data dictionary.")
        else:
            warning(f"Data called {name} was not added to data dictionary.")

    def _process_data(self, data: np.ndarray):
        """Check so the data count matches the vertex or face count."""

        if len(data) != self.v_count:  # TODO: Allow data to be associated with faces
            warning(f"Data count does not match vertex or face count.")
            return None, None
        else:
            data_res = data[self.mesh.faces.flatten()]  # Restructure the data
            data_mat = self._reformat_data_for_texture(data_res)
            val_caps = (np.min(data_res), np.max(data_res))
            return data_mat, val_caps


class PCDataWrapper(DataWrapper):
    """Wrapper class for point cloud data to be used in OpenGL."""

    p_count: int  # Number of points in the point cloud

    def __init__(self, pc: PointCloud, mts: int) -> None:

        self.data_mat_dict = {}
        self.data_value_caps = {}
        self.max_tex_size = mts
        self.p_count = len(pc.points)

        d_count = self.p_count
        self._calc_matrix_format(d_count)
        self._calc_texel_indices(d_count)

    def add_data(self, name: str, data: np.ndarray):
        (data_mat, val_caps) = self._process_data(data)

        if (data_mat is not None) and (val_caps is not None):
            self.data_mat_dict[name] = data_mat
            self.data_value_caps[name] = val_caps
            info(f"Data called {name} was added to data dictionary.")
        else:
            warning(f"Data called {name} was not added to data dictionary.")

    def _process_data(self, data: np.ndarray):
        """Check so the data count matches the vertex or face count."""
        if len(data) != self.p_count:  # TODO: Allow data to be associated with faces
            warning(f"Data count does not match point count.")
            return None, None
        else:
            data_mat = self._reformat_data_for_texture(data)
            val_caps = (np.min(data), np.max(data))
            return data_mat, val_caps
