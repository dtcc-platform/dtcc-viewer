from .citymodel import view as view_citymodel

from dtcc_model import CityModel

CityModel.add_processors(view_citymodel, "view")
