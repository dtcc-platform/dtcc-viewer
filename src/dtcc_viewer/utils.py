from pprint import pp
from dtcc_viewer import *
from dtcc_model import Mesh, PointCloud, Bounds
from dtcc_viewer.colors import *
from typing import List, Iterable
import trimesh
import numpy as np
import copy
from enum import Enum
from enum import IntEnum


class ColorBy(Enum):
    vertex = 1
    face = 2
    dict = 3


class Direction(IntEnum):
    x = 0
    y = 1
    z = 2


# ------------------------------- Mesh Conversion functions ----------------------------------#


# -------------------------------- Mesh Conversion Ended -------------------------------------#

# ------------------------- PointCloude Conversion functions ---------------------------------#


# --------------------------- PointCloude Conversion Ended ---------------------------------#


def calc_face_mid_points(mesh):
    faceVertexIndex1 = mesh.faces[:, 0]
    faceVertexIndex2 = mesh.faces[:, 1]
    faceVertexIndex3 = mesh.faces[:, 2]
    vertex1 = np.array(mesh.vertices[faceVertexIndex1])
    vertex2 = np.array(mesh.vertices[faceVertexIndex2])
    vertex3 = np.array(mesh.vertices[faceVertexIndex3])
    face_mid_points = (vertex1 + vertex2 + vertex3) / 3.0
    return face_mid_points


def split_mesh_in_quadrants(mesh: trimesh, face_mid_pts: Iterable):
    meshes = []
    masks = []
    values = []

    masks.append([pt[0] < 0 and pt[1] < 0 for pt in face_mid_pts])
    masks.append([pt[0] > 0 and pt[1] < 0 for pt in face_mid_pts])
    masks.append([pt[0] > 0 and pt[1] > 0 for pt in face_mid_pts])
    masks.append([pt[0] < 0 and pt[1] > 0 for pt in face_mid_pts])

    for i in np.arange(4):
        mesh_q = copy.deepcopy(mesh)
        mesh_q.update_faces(masks[i])
        mesh_q.remove_unreferenced_vertices()

        face_mid_pts = calc_face_mid_points(mesh_q)
        face_mid_pt_z = face_mid_pts[:, 2]
        values.append(face_mid_pt_z)
        meshes.append(mesh_q)

    return meshes, values


def get_sub_mesh(xdom: list, ydom: list, mesh: Mesh) -> Mesh:
    face_mid_pts = calc_face_mid_points(mesh)

    if len(xdom) == 2 and len(ydom) == 2 and xdom[0] < xdom[1] and ydom[0] < ydom[1]:
        x_range = face_mid_pts[:, 0].max() - face_mid_pts[:, 0].min()
        y_range = face_mid_pts[:, 1].max() - face_mid_pts[:, 1].min()
        face_mask = []

        for pt in face_mid_pts:
            xnrm = pt[0] / x_range
            ynrm = pt[1] / y_range
            if (xnrm > xdom[0] and xnrm < xdom[1]) and (
                ynrm > ydom[0] and ynrm < ydom[1]
            ):
                face_mask.append(True)
            else:
                face_mask.append(False)

        mesh_tri = trimesh.Trimesh(mesh.vertices, mesh.faces)
        mesh_tri.update_faces(face_mask)
        mesh_tri.remove_unreferenced_vertices()
        mesh_dtcc = Mesh(vertices=mesh_tri.vertices, faces=mesh_tri.faces)

        return mesh_dtcc
    else:
        print(f"Invalid domain.")
        return mesh


def split_mesh_in_stripes(
    n: int, mesh: trimesh, face_mid_pts: Iterable, direction: Direction
) -> list[Mesh]:
    meshes = []
    xmin = face_mid_pts[:, int(direction)].min()
    xmax = face_mid_pts[:, int(direction)].max()
    dx = (xmax - xmin) / n
    x_low = xmin

    for i in range(n):
        masks = [
            pt[int(direction)] < (x_low + dx) and pt[int(direction)] > x_low
            for pt in face_mid_pts
        ]
        mesh_tri = copy.deepcopy(mesh)
        mesh_tri.update_faces(masks)
        mesh_tri.remove_unreferenced_vertices()
        mesh_dtcc = Mesh(vertices=mesh_tri.vertices, faces=mesh_tri.faces)
        meshes.append(mesh_dtcc)
        x_low = x_low + dx

    return meshes


def split_pc_in_stripes(
    n: int, pc: PointCloud, direction: Direction
) -> list[PointCloud]:
    pcs = []
    min = pc.points[:, int(direction)].min()
    max = pc.points[:, int(direction)].max()
    d = (max - min) / n
    low_lim = min

    for i in range(n):
        new_pc = PointCloud()
        pts_indices = np.where(
            (pc.points[:, int(direction)] > low_lim)
            & (pc.points[:, int(direction)] < (low_lim + d))
        )
        new_pts = pc.points[pts_indices]
        new_pc.points = new_pts
        pcs.append(new_pc)
        low_lim = low_lim + d

    return pcs


def calc_distance_to_centre(face_mid_pts: Iterable):
    n = len(face_mid_pts)
    average_x = np.sum(face_mid_pts[:, 0]) / n
    average_y = np.sum(face_mid_pts[:, 1]) / n
    average_z = np.sum(face_mid_pts[:, 2]) / n
    mesh_mid_pt = np.array([average_x, average_y, average_z])
    dist = np.sqrt(np.sum((face_mid_pts - mesh_mid_pt) ** 2, axis=1))
    return dist
