import numpy as np
from dtcc_core.model import Mesh, PointCloud
from dtcc_viewer.opengl.utils import surface_2_mesh, concatenate_meshes
import json
import pprint
import os


def depth(g, count=0):
    return count if not isinstance(g, list) else max([depth(x, count + 1) for x in g])


def points_on_plane(origin, vector1, vector2, size, num_points):
    u = np.linspace(0, 1, num_points)
    v = np.linspace(0, 1, num_points)

    # Generate a grid of points in the uv-parameter space
    u_grid, v_grid = np.meshgrid(u, v)

    # Parametric representation of the plane
    points = (
        origin
        + u_grid.flatten()[:, np.newaxis] * vector1 * size
        + v_grid.flatten()[:, np.newaxis] * vector2 * size
    )

    return points


def load_city(objmax):
    city = "../data/models/rotterdam.city.json"
    f = open(city, "r")
    data = json.load(f)

    meta_data = data["metadata"]
    city_objects = data["CityObjects"]
    keys = list(data["CityObjects"].keys())
    vertices = np.array(data["vertices"]) * 0.001  # Convert to meters
    counter = 0

    # pprint.pprint(city_objects, depth=4)
    all_face_idx = []

    srf_count = 0
    msrf_count = 0
    solid_count = 0

    for key in keys:
        boundaries = city_objects[key]["geometry"][0]["boundaries"]
        # pprint.pprint(city_objects[key], depth=3)
        if counter < objmax:
            levels = depth(boundaries)
            if levels == 3:  # Multi surface
                msrf_count += 1
                for surface in boundaries:
                    face_idx = np.array(surface[0])
                    all_face_idx.append(face_idx.tolist())
            elif levels == 2:  # Surface
                srf_count += 1
            else:  # Solid?
                solid_count += 1

        counter += 1

    meshes = []
    normals = []

    for face_idx in all_face_idx:
        srf_vertices = vertices[face_idx, :]
        (mesh, surface_normal) = surface_2_mesh(srf_vertices)
        if mesh is not None:
            meshes.append(mesh)
            normals.append(surface_normal)
        else:
            print("Mesh is None")
            pprint.pprint(srf_vertices)

    print("Surface count: " + str(srf_count))
    print("Multi surface count: " + str(msrf_count))
    print("Solid count: " + str(solid_count))

    # pprint.pprint(meshes)
    # pprint.pprint(normals)

    print("Mesh count: " + str(len(meshes)))
    print("Normals count: " + str(len(normals)))

    city_mesh = concatenate_meshes(meshes)

    return city_mesh


if __name__ == "__main__":
    os.system("clear")

    city_mesh = load_city(3)

    pass
