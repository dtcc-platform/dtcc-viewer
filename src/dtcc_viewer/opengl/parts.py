import numpy as np
from dtcc_core.model import Mesh
from pprint import pp
from dtcc_viewer.logging import info, warning


class Parts:
    """Class for storing sub sets "parts" of a mesh.

    Each part is a subset of a mesh with its own face indices. The class also stores
    meta data and ids for each part. The ids are used to identify clickable objects
    in the scene and to retrieve meta data for display.


    Attributes
    ----------
    face_start_indices : np.ndarray[int]
        Array of face indices for the start of each part.
    face_end_indices : np.ndarray[int]
        Array of face indices for the end of each part.
    face_count_per_part : np.ndarray[int]
        Number of faces for each part.
    ids : np.ndarray[int]
        Array of ids for each part.
    selected : np.ndarray[bool]
        Array of boolean values for each part.
    attributes : dict
        Dictionary of attributes for each part.
    ids_2_uuids : dict
        Mapping between id (int) and uuid (str).
    count : int
        Number of parts.
    f_count : int
        Total number of faces.
    """

    face_start_indices: np.ndarray
    face_end_indices: np.ndarray
    face_count_per_part: np.ndarray
    ids: np.ndarray
    selected: np.ndarray
    attributes: dict
    ids_2_uuids: dict
    count: int
    f_count: int

    def __init__(
        self,
        meshes: list[Mesh],
        uuids: list[str] = None,
        attributes: list[dict] = None,
    ):
        self.count = len(meshes)
        self._process_data(meshes, uuids, attributes)

    def _process_data(
        self, meshes: list[Mesh], uuids: list[str], attributes: list[dict]
    ):
        face_count_per_part = []
        face_start_indices = []
        face_end_indices = []
        tot_f_count = 0
        ids = []
        self.attributes = {}

        if uuids is not None:
            if len(meshes) != len(uuids):
                warning("Number of meshes and uuids do not match")
                return

        if attributes is not None:
            if len(meshes) != len(attributes):
                warning("Number of meshes and attributes do not match")
                return

        for i, mesh in enumerate(meshes):
            # Store face indices for this submesh to be used for picking
            mesh_f_count = len(mesh.faces)
            face_start_indices.append(tot_f_count)
            face_end_indices.append(tot_f_count + mesh_f_count - 1)
            tot_f_count += mesh_f_count
            face_count_per_part.append(mesh_f_count)
            ids.append(i)

        self.face_count_per_part = np.array(face_count_per_part)
        self.f_count = tot_f_count
        self.face_start_indices = np.array(face_start_indices)
        self.face_end_indices = np.array(face_end_indices)
        self.ids = np.array(ids)

        if attributes is not None:
            self.attributes = {key: value for key, value in zip(ids, attributes)}
        else:
            self.attributes = None

    def offset_ids(self, id_offset):
        self.ids = self.ids + id_offset

    def id_exists(self, id):
        return id in self.ids

    def print(self):
        print("Parts data: ")
        print(self.face_start_indices)
        print(self.face_end_indices)
        print(self.ids)

    def toogle_selected(self, id):
        self.selected[id] = not self.selected[id]

    def get_face_ids(self):
        face_ids = np.repeat(self.ids, self.face_count_per_part)
        return face_ids

    def get_attributes(self, id):
        if self.attributes is None:
            return None

        if id in self.attributes:
            return self.attributes[id]
        else:
            return None

    def get_unique_attribute_keys(self):
        unique_keys = set()

        for attributes in self.attributes.values():
            if isinstance(attributes, dict):
                unique_keys.update(attributes.keys())

        return unique_keys

    def get_attribute_data(self, key):
        data = []
        for part_attribute in self.attributes.values():
            if key in part_attribute:
                data.append(part_attribute[key])
            else:
                data.append(None)
        return data
