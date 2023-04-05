import folium
import tempfile
import dtcc_io as io
from pathlib import Path
import tempfile
from dtcc_io.bounds import bounds_center

from .notebook_functions import is_notebook

def show_folium_in_browser(m):
    map_file = tempfile.NamedTemporaryFile(suffix=".html",delete=False)
    map_file = Path(map_file.name)
    m.save(map_file)
    import webbrowser
    webbrowser.open(f"file:///{map_file}")

def view(citymodel_pb, return_html=False, show_in_browser=False):
    tmp_geojson = tempfile.NamedTemporaryFile(suffix=".geojson",delete=False)
    outpath = Path(tmp_geojson.name)
    io.save_citymodel(citymodel_pb, outpath)
    bounds = io.citymodel.building_bounds(outpath)
    data_mid = bounds_center(bounds)
    data_mid = [data_mid[1],data_mid[0]]
    print(bounds)
    print(data_mid)
    m = folium.Map(location = data_mid, min_zoom=5, max_zoom=22, zoom_start=13)
    
    
    with open(outpath, "r") as f:
        cm_geojson = f.read()
    cm_layers =  folium.GeoJson(cm_geojson).add_child(folium.GeoJsonPopup(fields=['id','height','error'],aliases=['UUID','Height','Error']))  
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
        show_folium_in_browser(m)
        
    else:
        if is_notebook():
            return m
        else:
            show_folium_in_browser(m)
        



