from pvlib import solarposition
import pandas as pd
import numpy as np


class Situation:

    lat: float
    lon: float
    start: pd.Timestamp
    end: pd.Timestamp
    timezone: str
    sun_pos: np.ndarray
    include_night: bool

    def __init__(
        self,
        lon: float,
        lat: float,
        start: pd.Timestamp,
        end: pd.Timestamp,
        include_night: bool = True,
    ) -> None:
        """
        Initialize an instance of the Situation class.
        """
        self.lon: float = lon
        self.lat: float = lat
        self.start: pd.Timestamp = start
        self.end: pd.Timestamp = end
        self.timezone: str = "UTC"
        self.include_night: bool = include_night

    def calc_solar_pos(self, radius=1.0, origin=np.zeros(3)) -> pd.DataFrame:
        df = pd.date_range(start=self.start, end=self.end, freq="1min")
        solpos = solarposition.get_solarposition(df, self.lat, self.lon)
        elev = np.radians(solpos.apparent_elevation.to_list())
        azim = np.radians(solpos.azimuth.to_list())
        zeni = np.radians(solpos.apparent_zenith.to_list())
        x_sun = radius * np.cos(elev) * np.sin(azim) + origin[0]
        y_sun = radius * np.cos(elev) * np.cos(azim) + origin[1]
        z_sun = radius * np.sin(elev) + origin[2]
        self.sun_pos = np.column_stack((x_sun, y_sun, z_sun))

        if not self.include_night:
            mask = solpos.apparent_elevation > 0
            self.sun_pos = self.sun_pos[mask]
