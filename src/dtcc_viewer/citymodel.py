import folium
import logging
import tempfile
import dtcc_core.io as io
from pathlib import Path
import tempfile
from dtcc_core.model.geometry import Bounds
from dtcc_core.model import City
from .notebook_functions import is_notebook
from .utils import get_random_colors
from .logging import info


def _rgb_to_hexstring(rgb: list[int]) -> str:
    return "#%02x%02x%02x" % (rgb[0], rgb[1], rgb[2])


def _show_folium_in_browser(m):
    map_file = tempfile.NamedTemporaryFile(suffix=".html", delete=False)
    map_file = Path(map_file.name)
    m.save(map_file)
    import webbrowser

    info(
        f"Opening city model for viewing in your browser. If nothing happens, check your open browser windows."
    )
    webbrowser.open(f"file:///{map_file}")


def create_style_function(cm: City, color_field: str, color_map: str):
    if not color_field or not color_map:
        return lambda x: {"fillColor": "#aa0000"}
    if color_map == "random":
        try:
            unique_attributes = set([b[color_field] for b in cm.buildings])
            num_unique_attrs = len(unique_attributes)
            info(f"num_unique_attrs: {num_unique_attrs}")
        except KeyError:
            logging.warning(f"buildings don't have {color_field} attribute")
        colors = get_random_colors(num_unique_attrs)
        color_map = {
            attr: _rgb_to_hexstring(colors[i])
            for i, attr in enumerate(unique_attributes)
        }
        print(color_map)
        return lambda x: {"fillColor": color_map[x["properties"][color_field]]}
    else:
        lambda x: {"fillColor": "#0000aa"}


def view(
    cm: City,
    color_field=None,
    color_map="",
    return_html=False,
    show_in_browser=False,
    view_fields=["id", "height", "ground_height", "error"],
    view_aliases=None,
):
    tmp_geojson = tempfile.NamedTemporaryFile(suffix=".geojson", delete=False)
    outpath = Path(tmp_geojson.name)
    tmp_geojson.close()
    cm.save(outpath)
    bounds = io.city.building_bounds(outpath)
    data_mid = bounds.center()
    data_mid = [data_mid[1], data_mid[0]]
    m = folium.Map(location=data_mid, min_zoom=5, max_zoom=22, zoom_start=13)

    if color_field is not None:
        style_function = create_style_function(cm, color_field, "random")
    else:
        style_function = lambda x: {"fillColor": "#0000aa"}

    with open(outpath, "r") as f:
        cm_geojson = f.read()

    if view_aliases is None or len(view_aliases) != len(view_fields):
        view_aliases = view_fields

    cm_layers = folium.GeoJson(cm_geojson, style_function=style_function).add_child(
        folium.GeoJsonPopup(fields=view_fields, aliases=view_aliases)
    )
    m.add_child(cm_layers)

    # Zoom to the added layer
    m.fit_bounds(cm_layers.get_bounds())

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
