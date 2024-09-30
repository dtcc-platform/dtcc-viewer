from pprint import pp

# from dtcc_viewer import *
from dtcc_core.model import Mesh, PointCloud, Bounds, VolumeMesh

# from dtcc_viewer.colors import *
from typing import Iterable
import trimesh
import numpy as np
import copy
from enum import Enum
from enum import IntEnum
from colorsys import hsv_to_rgb
from math import exp, sqrt
import random


class ColorBy(Enum):
    vertex = 1
    face = 2
    dict = 3


class Direction(IntEnum):
    x = 0
    y = 1
    z = 2


def get_random_colors(
    n, h_range=(0.0, 1.0), s_range=(0.2, 1.0), v_range=(0.6, 1.0), return_int=True
):
    """
    get random, visually distinct colors, for use in for example qualitative choropleth map.
    Colors are generated in the HSV space and converted to RGB values.

    Parameters:
    n: Number of colors to generate
    h_range: Tuple of min and max value of the Hue parameter in the range 0.0-1.0
    s_range: Tuple of min and max value of the Saturation parameter in the range 0.0-1.0.
             The min value should be a least 0.2 for good results
    v_range: Tuple of min and max value of the Value parameter in the range 0.0-1.0
             The min value should be a least 0.4 for good results

    Returns:
    rbg_int: a list of integer value RGB tuples
    """

    assert (
        h_range[0] >= 0 and h_range[1] <= 1
    ), "h_range min and max must be between 0-1"
    assert (
        s_range[0] >= 0 and s_range[1] <= 1
    ), "s_range min and max must be between 0-1"
    assert (
        v_range[0] >= 0 and v_range[1] <= 1
    ), "v_range min and max must be between 0-1"

    assert h_range[0] < h_range[1], "h_range min must be less than h_range max"
    assert s_range[0] < s_range[1], "s_range min must be less than s_range max"
    assert v_range[0] < v_range[1], "v_range min must be less than v_range max"

    sample_space = [
        (random.uniform(*h_range), random.uniform(*s_range), random.uniform(*v_range))
        for r in range(10 * n)
    ]
    selected_colors = []
    selected_colors.append(sample_space.pop())
    # find the color in our sample space that maximizes the minimum
    # distance too all the already select colors.
    for i in range(n - 1):
        min_dist = [_min_dist_to_selected(selected_colors, c) for c in sample_space]
        next_color_idx = min_dist.index(max(min_dist))
        selected_colors.append(sample_space.pop(next_color_idx))
    rgb_float = (hsv_to_rgb(*s) for s in selected_colors)
    if return_int:
        rgb_int = [
            (int(round(r * 255)), int(round(g * 255)), int(round(b * 255)))
            for r, g, b in rgb_float
        ]
        return rgb_int
    else:
        return list(rgb_float)


def _min_dist_to_selected(selected, c):
    return min([_dvr(c, s) for s in selected])


def _dh(h1, h2):
    return min(abs(h1 - h2), 1 - abs(h1 - h2)) * 2


def _Dc(c1, c2):
    h1, s1, v1 = c1
    h2, s2, v2 = c2
    return sqrt(_dh(h1, h2) ** 2 + (s1 - s2) ** 2 + (v1 - v2) ** 2)


def _dvr(c1, c2):
    h1, s1, v1 = c1
    h2, s2, v2 = c2
    color_diff = max(_dh(h1, h2), abs(s1 - s2)) ** 2 + _Dc(c1, c2) ** 2
    return min(sqrt(color_diff / 2), 1)


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


def get_sub_volume_mesh_from_mask(cell_mask: np.ndarray, vmesh: VolumeMesh) -> Mesh:

    cells = vmesh.cells[cell_mask, :]
    cells_flat = cells.flatten()
    unique_vertex_indices = np.unique(cells_flat)
    old_vertex_indices = unique_vertex_indices

    old_2_new = {}
    for i, old_vi in enumerate(old_vertex_indices):
        old_2_new[old_vi] = i

    new_vertices = vmesh.vertices[unique_vertex_indices, :]
    new_cells = np.zeros(cells.shape, dtype=int)

    for i in range(cells.shape[0]):
        new_cells[i, :] = [old_2_new[old_vi] for old_vi in cells[i, :]]

    sub_vmesh = VolumeMesh(vertices=new_vertices, cells=new_cells)

    return sub_vmesh


def get_sub_mesh_from_mask(face_mask: np.ndarray, mesh: Mesh) -> Mesh:

    faces = mesh.faces[face_mask, :]
    faces_flat = faces.flatten()
    unique_vertex_indices = np.unique(faces_flat)
    old_vertex_indices = unique_vertex_indices

    old_2_new = {}
    for i, old_vi in enumerate(old_vertex_indices):
        old_2_new[old_vi] = i

    new_vertices = mesh.vertices[unique_vertex_indices, :]
    new_faces = np.zeros(faces.shape, dtype=int)

    for i in range(faces.shape[0]):
        new_faces[i, :] = [old_2_new[old_vi] for old_vi in faces[i, :]]

    return Mesh(vertices=new_vertices, faces=new_faces)
