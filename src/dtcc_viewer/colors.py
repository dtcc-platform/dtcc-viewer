import numpy as np
from typing import List, Iterable, Any
from .random_colors import get_random_colors


def calc_colors_rainbow(
    values: Iterable[float], min: float = None, max: float = None
) -> List[List[float]]:
    """Calculate colors using a rainbow color map.

    Parameters
    ----------
    values : iterable of float
        The values to determine colors for.
    min : float, optional
        The minimum value for scaling, if not provided, the minimum value from `values` is used.
    max : float, optional
        The maximum value for scaling, if not provided, the maximum value from `values` is used.

    Returns
    -------
    List[List[float]]
        List of color values for each input value in RGB format.
    """
    colors = []
    [min_value, max_value] = _get_min_max(values, min, max)
    for i in range(0, len(values)):
        c = _get_blended_color(min_value, max_value, values[i])
        colors.append(c)
    return colors


def calc_colors_warm(
    values: Iterable[float], min: float, max: float
) -> List[List[float]]:
    """Calculate colors using a warm color map.

    Parameters
    ----------
    values : iterable of float
        The values to determine colors for.
    min : float
        The minimum value for scaling.
    max : float
        The maximum value for scaling.

    Returns
    -------
    List[List[float]]
        List of color values for each input value in RGB format.
    """
    colors = []
    [min_value, max_value] = _get_min_max(values, min, max)
    for i in range(0, len(values)):
        c = _get_blended_color_yellow_red(min_value, max_value, values[i])
        colors.append(c)
    return colors


def calc_colors_cold(
    values: Iterable[float], min: float, max: float
) -> List[List[float]]:
    """Calculate colors using a cold color map.

    Parameters
    ----------
    values : iterable of float
        The values to determine colors for.
    min : float
        The minimum value for scaling.
    max : float
        The maximum value for scaling.

    Returns
    -------
    List[List[float]]
        List of color values for each input value in RGB format.
    """
    colors = []
    [min_value, max_value] = _get_min_max(values, min, max)
    for i in range(0, len(values)):
        c = _get_blended_color_cyan_blue(min_value, max_value, values[i])
        colors.append(c)
    return colors


def calc_colors_mono(
    values: Iterable[float], min: float, max: float
) -> List[List[float]]:
    """Calculate colors using a monochromatic color map.

    Parameters
    ----------
    values : iterable of float
        The values to determine colors for.
    min : float
        The minimum value for scaling.
    max : float
        The maximum value for scaling.

    Returns
    -------
    List[List[float]]
        List of color values for each input value in RGB format.
    """
    colors = []
    [min_value, max_value] = _get_min_max(values, min, max)
    for i in range(0, len(values)):
        fColor = _get_blended_color_mono(min_value, max_value, values[i])
        colors.append(fColor)
    return colors


def calc_colors_arctic(
    values: Iterable[float], min: float, max: float
) -> List[List[float]]:
    """Calculate colors using an arctic color map.

    Parameters
    ----------
    values : iterable of float
        The values to determine colors for.
    min : float
        The minimum value for scaling.
    max : float
        The maximum value for scaling.

    Returns
    -------
    List[List[float]]
        List of color values for each input value in RGB format.
    """
    colors = []
    for i in range(0, len(values)):
        fColor = [0.95, 0.95, 0.95, 1]
        colors.append(fColor)
    return colors


# Calculate color blend for a range of values where some are excluded using a True-False mask
def calc_colors_with_mask(values, mask) -> List[List[float]]:
    """Calculate colors for a range of values with a mask indicating exclusion.

    Parameters
    ----------
    values : iterable of any
        The values to determine colors for.
    mask : iterable of bool
        A mask indicating whether each value should be included in the coloring.

    Returns
    -------
    List[List[float]]
        List of color values for each input value in RGB format.
    """
    colors = []
    min = np.min(values[mask])
    max = np.max(values[mask])
    for i in range(0, len(values)):
        if mask[i]:
            c = _get_blended_color(min, max, values[i])
        else:
            c = [0.2, 0.2, 0.2, 1]
        colors.append(c)
    return colors


# assign each distict value a random color
def calc_colors_random(values: Iterable[Any]) -> List[List[float]]:
    """Assign random colors to distinct values.

    Parameters
    ----------
    values : iterable of any
        The values to determine colors for.

    Returns
    -------
    List[List[float]]
        List of color values for each input value in RGB format.
    """
    unique_values = len(set(values))
    colors = get_random_colors(unique_values, return_int=False)
    colors = [c.append(1.0) for c in colors]
    color_map = {}
    for v, c in zip(set(values), colors):
        color_map[v] = c
    return colors


def _get_blended_color(min, max, value):
    """Calculate a blended color based on a value within a range.

    Parameters
    ----------
    min : float
        The minimum value of the range.
    max : float
        The maximum value of the range.
    value : float
        The value for which to calculate the color.

    Returns
    -------
    List[float]
        The calculated color value in RGB format.
    """
    diff = max - min
    if (diff) <= 0:
        print(
            "Error in _get_blended_color: Given MAX-MIN range is zero or the MAX value is smaller than given MIN value!"
        )
        return [1, 0, 1, 1]  # Error, returning magenta

    new_min = 0
    new_max = diff
    new_value = value - min
    percentage = 100.0 * (new_value / new_max)

    if new_value <= new_min:
        # Returning blue [0,0,1]
        return [0.0, 0.0, 1.0, 1.0]
    elif new_value >= new_max:
        # Returning red [1,0,0]
        return [1.0, 0.0, 0.0, 1.0]
    else:
        if percentage >= 0.0 and percentage <= 25.0:
            # Blue fading to Cyan [0,x,1], where x is increasing from 0 to 1
            frac = percentage / 25.0
            return [0.0, (frac * 1.0), 1.0, 1.0]

        elif percentage > 25.0 and percentage <= 50.0:
            # Cyan fading to Green [0,1,x], where x is decreasing from 1 to 0
            frac = 1.0 - abs(percentage - 25.0) / 25.0
            return [0.0, 1.0, (frac * 1.0), 1.0]

        elif percentage > 50.0 and percentage <= 75.0:
            # Green fading to Yellow [x,1,0], where x is increasing from 0 to 1
            frac = abs(percentage - 50.0) / 25.0
            return [(frac * 1.0), 1.0, 0.0, 1.0]

        elif percentage > 75.0 and percentage <= 100.0:
            # Yellow fading to red [1,x,0], where x is decreasing from 1 to 0
            frac = 1.0 - abs(percentage - 75.0) / 25.0
            return [1.0, (frac * 1.0), 0.0, 1.0]

        elif percentage > 100.0:
            # Returning red if the value overshoot the limit.
            return [1.0, 0.0, 0.0, 1.0]


def _get_blended_color_mono(min, max, value):
    """Calculate a monochromatic color based on a value within a range.

    Parameters
    ----------
    min : float
        The minimum value of the range.
    max : float
        The maximum value of the range.
    value : float
        The value for which to calculate the color.

    Returns
    -------
    List[float]
        The calculated color value in RGB format.
    """
    frac = _get_normalised_value_with_cap(min, max, value)
    return [frac, frac, frac, 1.0]


def _get_blended_color_yellow_red(min, max, value):
    """Calculate a yellow-to-red color based on a value within a range.

    Parameters
    ----------
    min : float
        The minimum value of the range.
    max : float
        The maximum value of the range.
    value : float
        The value for which to calculate the color.

    Returns
    -------
    List[float]
        The calculated color value in RGB format.
    """
    frac = _get_normalised_value_with_cap(min, max, value)
    return [1.0, (frac * 1.0), 0.0, 1.0]


def _get_blended_color_cyan_blue(min, max, value):
    """Calculate a cyan-to-blue color based on a value within a range.

    Parameters
    ----------
    min : float
        The minimum value of the range.
    max : float
        The maximum value of the range.
    value : float
        The value for which to calculate the color.

    Returns
    -------
    List[float]
        The calculated color value in RGB format.
    """
    frac = _get_normalised_value_with_cap(min, max, value)
    return [0.0, (frac * 1.0), 1.0, 1.0]


def _get_min_max(values: Iterable[float], min: float = None, max: float = None):
    """Get the minimum and maximum values considering optional bounds.

    Parameters
    ----------
    values : iterable of float
        The values to determine the minimum and maximum from.
    min : float, optional
        The optional minimum value.
    max : float, optional
        The optional maximum value.

    Returns
    -------
    Tuple[float, float]
        The calculated minimum and maximum values.
    """
    if min == None:
        min_value = np.min(values)
    else:
        min_value = min

    if max == None:
        max_value = np.max(values)
    else:
        max_value = max

    return min_value, max_value


def _get_normalised_value_with_cap(min, max, value):
    """Calculate a normalized value within a range with a cap.

    Parameters
    ----------
    min : float
        The minimum value of the range.
    max : float
        The maximum value of the range.
    value : float
        The value for which to calculate the normalized value.

    Returns
    -------
    float
        The calculated normalized value.
    """
    diff = max - min
    if (diff) <= 0:
        print(
            "Error: Given MAX-MIN range is zero or the MAX value is smaller than given MIN value!"
        )
        return [1, 0, 1, 1]  # Error returning magenta

    new_value = value - min
    new_min = 0
    new_max = diff
    frac = 0
    if new_value < new_min:
        frac = 0.0  # frac = 0 => Red
    elif (new_value >= new_min) and (new_value <= new_max):
        frac = new_value / new_max  # frac = 1 => Yellow
    elif new_value >= new_max:
        frac = 1.0

    return frac


color_maps = {
    "arctic": calc_colors_arctic,
    "mono": calc_colors_mono,
    "rainbow": calc_colors_rainbow,
    "warm": calc_colors_warm,
    "cold": calc_colors_cold,
    "random": calc_colors_random,
}
