import numpy as np
from dtcc_model import Mesh
from pprint import pp
from dtcc_viewer.logging import info, warning


class Submeshes:
    face_start_indices: np.ndarray
    face_end_indices: np.ndarray
    face_count_per_submesh: np.ndarray
    ids: np.ndarray
    selected: np.ndarray
    meta_data: dict
    ids_2_uuids: dict  # Mapping between id (int) and uuid (str)
    id_offset: int
    count: int  # Number of submeshes
    f_count: int  # Total number of faces

    def __init__(self, meshes: list[Mesh], uuids: list[str]):
        self.count = len(meshes)
        self._process_data(meshes, uuids)
        self.id_offset = 0

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

        self.face_count_per_submesh = np.array(face_count_per_submesh)
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

    def set_id_offset(self, offset):
        self.id_offset = offset

    def toogle_selected(self, id):
        self.selected[id] = not self.selected[id]

    def get_face_ids(self, id, mesh: Mesh):
        len(mesh.faces)
