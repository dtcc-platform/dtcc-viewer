# https://geopandas.org/en/stable/docs/user_guide/io.html
import geopandas as gpd
import matplotlib.pyplot as plt
import numpy as np
import plotly.graph_objects as go
from shapely.geometry import LineString
from dtcc_viewer import Window, Scene


def create_sphere_lss(center, radius, latitude_segments=20, longitude_segments=20):
    lss_long = []
    lss_lati = []

    for lat in range(latitude_segments + 1):
        theta = lat * np.pi / latitude_segments
        sin_theta = np.sin(theta)
        cos_theta = np.cos(theta)
        ring_long = []

        for lon in range(longitude_segments + 1):
            phi = lon * 2 * np.pi / longitude_segments
            sin_phi = np.sin(phi)
            cos_phi = np.cos(phi)

            x = center[0] + radius * sin_theta * cos_phi
            y = center[1] + radius * sin_theta * sin_phi
            z = center[2] + radius * cos_theta

            ring_long.append(np.array([x, y, z]))

        ls_long = LineString(ring_long)
        lss_long.append(ls_long)

    for lon in range(longitude_segments + 1):
        phi = lon * 2 * np.pi / longitude_segments
        sin_phi = np.sin(phi)
        cos_phi = np.cos(phi)
        ring_lati = []

        for lat in range(latitude_segments + 1):
            theta = lat * np.pi / latitude_segments
            sin_theta = np.sin(theta)
            cos_theta = np.cos(theta)

            x = center[0] + radius * sin_theta * cos_phi
            y = center[1] + radius * sin_theta * sin_phi
            z = center[2] + radius * cos_theta

            ring_lati.append(np.array([x, y, z]))

        ls_lati = LineString(ring_lati)
        lss_lati.append(ls_lati)

    return lss_long, lss_lati


def polygon_2_line_string(poly):
    xy_coords = poly.exterior.coords.xy
    lon = np.array(xy_coords[0])
    lat = np.array(xy_coords[1])

    lon = lon * np.pi / 180
    lat = lat * np.pi / 180

    R = 6878.134
    x = R * np.cos(lat) * np.cos(lon)
    y = R * np.cos(lat) * np.sin(lon)
    z = R * np.sin(lat)

    coords = np.array([x, y, z]).T

    ls = LineString(coords)
    return ls


def plot_orbit():
    angle = np.linspace(0, 2.0 * np.pi, 144)
    R = 6878.134
    x = R * np.cos(angle)
    y = R * np.sin(angle)
    z = np.zeros(144)
    return x, y, z


# Read the shapefile.  Creates a DataFrame object
gdf = gpd.read_file("data/ne_110m_admin_0_countries.shp")
polygons = []
lss = []

for i in gdf.index:
    # print(gdf.loc[i].NAME)  # Call a specific attribute
    geometry = gdf.loc[i].geometry  # Polygons or MultiPolygons
    if geometry.geom_type == "Polygon":
        polygons.append(geometry)

    elif geometry.geom_type == "MultiPolygon":
        for poly in geometry.geoms:
            polygons.append(poly)


for poly in polygons:
    ls = polygon_2_line_string(poly)
    lss.append(ls)

cp = np.array([0, 0, 0])
R = 6878.134

lss_long, lss_lati = create_sphere_lss(cp, R, 100, 100)

window = Window(1200, 800)
scene = Scene()

scene.add_linestring("Countries", lss)
scene.add_linestring("Longitude", lss_long)
scene.add_linestring("Latitude", lss_lati)

window.render(scene)
