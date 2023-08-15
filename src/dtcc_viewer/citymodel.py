import folium
import logging
import tempfile
import dtcc_io as io
from pathlib import Path
import tempfile
from dtcc_model.geometry import Bounds
from dtcc_model.city import City
from .notebook_functions import is_notebook
from .random_colors import get_random_colors
from .colors import color_maps


def _rgb_to_hexstring(rgb: list[int]) -> str:
    return "#%02x%02x%02x" % (rgb[0], rgb[1], rgb[2])


def _show_folium_in_browser(m):
    map_file = tempfile.NamedTemporaryFile(suffix=".html", delete=False)
    map_file = Path(map_file.name)
    m.save(map_file)
    import webbrowser

    webbrowser.open(f"file:///{map_file}")


def create_style_function(cm: City, color_field: str, color_map: str):
    if color_map == "random":
        try:
            unique_attributes = set([b[color_field] for b in cm.buildings])
            num_unique_attrs = len(unique_attributes)
        except KeyError:
            logging.warning(f"buildings don't have {color_field} attribute")
        colors = get_random_colors(num_unique_attrs)
        color_map = {
            attr: _rgb_to_hexstring(colors[i])
            for i, attr in enumerate(unique_attributes)
        }
        return lambda x: {"fill_color": color_map[x["properties"][color_field]]}
    elif color_map in color_maps:
        pass


def view(
    cm: City,
    color_field=None,
    color_map="",
    return_html=False,
    show_in_browser=False,
):
    tmp_geojson = tempfile.NamedTemporaryFile(suffix=".geojson", delete=False)
    outpath = Path(tmp_geojson.name)
    cm.save(outpath)
    bounds = io.city.building_bounds(outpath)
    data_mid = bounds.center()
    data_mid = [data_mid[1], data_mid[0]]
    m = folium.Map(location=data_mid, min_zoom=5, max_zoom=22, zoom_start=13)

    if color_field is not None:
        style_function = lambda x: {"fill_color": x["properties"][color_field]}

    with open(outpath, "r") as f:
        cm_geojson = f.read()
    cm_layers = folium.GeoJson(cm_geojson).add_child(
        folium.GeoJsonPopup(
            fields=["id", "height", "error"], aliases=["UUID", "Height", "Error"]
        )
    )
    m.add_child(cm_layers)
    tmp_geojson.close()
    outpath_dir = outpath.parent
    outpath.unlink()
    try:
        outpath_dir.rmdir()
    except OSError:
        pass

    if return_html:
        return m._repr_html_()
    if show_in_browser:
        _show_folium_in_browser(m)

    else:
        if is_notebook():
            return m
        else:
            _show_folium_in_browser(m)
