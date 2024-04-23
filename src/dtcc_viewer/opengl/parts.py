import numpy as np
from dtcc_model import Mesh
from pprint import pp
from dtcc_viewer.logging import info, warning


class Parts:
    """Class for storing sub sets "parts" of a mesh.

    Each part is a submesh with its own face indices. The class also stores meta data
    and ids for each part. The ids are used to identify clickable objects in the scene.


    Attributes
    ----------
    face_start_indices : np.ndarray[int]
        Array of face indices for the start of each part.
    face_end_indices : np.ndarray[int]
        Array of face indices for the end of each part.

    bb : BoundingBox
        Bounding box for the entire collection of objects in the scene.
    max_tex_size : int
        Maximum texture size allowed by the graphics card.
    """

    face_start_indices: np.ndarray
    face_end_indices: np.ndarray
    face_count_per_part: np.ndarray
    ids: np.ndarray
    selected: np.ndarray
    meta_data: dict
    ids_2_uuids: dict  # Mapping between id (int) and uuid (str)
    count: int  # Number of parts
    f_count: int  # Total number of faces

    def __init__(self, meshes: list[Mesh], uuids: list[str]):
        self.count = len(meshes)
        self._process_data(meshes, uuids)

    def _process_data(self, meshes: list[Mesh], uuids: list[str]):
        face_count_per_submesh = []
        face_start_indices = []
        face_end_indices = []
        tot_f_count = 0
        counter = 0
        ids = []

        if len(meshes) != len(uuids):
            warning("Number of meshes and uuids do not match")
            return

        for mesh in meshes:
            # Store face indices for this submesh to be used for picking
            mesh_f_count = len(mesh.faces)
            face_start_indices.append(tot_f_count)
            face_end_indices.append(tot_f_count + mesh_f_count - 1)
            tot_f_count += mesh_f_count

            face_count_per_submesh.append(mesh_f_count)
            ids.append(counter)
            counter += 1

        self.face_count_per_part = np.array(face_count_per_submesh)
        self.f_count = tot_f_count
        self.ids_2_uuids = {key: value for key, value in zip(ids, uuids)}
        self.face_start_indices = np.array(face_start_indices)
        self.face_end_indices = np.array(face_end_indices)
        self.ids = np.array(ids)

    def offset_ids(self, id_offset):
        self.ids = self.ids + id_offset
        self.ids_2_uuids = {
            key + id_offset: value for key, value in self.ids_2_uuids.items()
        }

    def id_exists(self, id):
        return id in self.ids

    def add_meta_data(self, id, newdata_dict):
        self.meta_data[id] = newdata_dict

    def print(self):
        print("Submeshes data: ")
        print(self.face_start_indices)
        print(self.face_end_indices)
        print(self.ids)

    def toogle_selected(self, id):
        self.selected[id] = not self.selected[id]

    def get_face_ids(self):
        face_ids = np.repeat(self.ids, self.face_count_per_part)
        return face_ids
