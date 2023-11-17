import numpy as np
from typing import List, Iterable, Any
from .random_colors import get_random_colors


def calc_colors_rainbow(values: Iterable[float], min: float = None, max: float = None):
    """Calculate colors using a rainbow color map."""
    colors = np.zeros((len(values), 3))
    [min_value, max_value] = _get_min_max(values, min, max)
    for i in range(0, len(values)):
        colors[i, :] = _get_blended_color(min_value, max_value, values[i])
    return colors


def calc_colors_multi(values: Iterable[float], min: float = None, max: float = None):
    """Calculate colors using a rainbow color map."""
    colors = np.zeros((len(values), 3))
    [min_value, max_value] = _get_min_max(values, min, max)
    for i in range(0, len(values)):
        colors[i, :] = _get_blended_color_multi(min_value, max_value, values[i])
    return colors


def calc_colors_warm(values: Iterable[float], min: float, max: float):
    """Calculate colors using a warm color map."""
    colors = np.zeros((len(values), 3))
    [min_value, max_value] = _get_min_max(values, min, max)
    for i in range(0, len(values)):
        colors[i, :] = _get_blended_color_yellow_red(min_value, max_value, values[i])
    return colors


def calc_colors_cold(values: Iterable[float], min: float, max: float):
    """Calculate colors using a cold color map."""
    colors = np.zeros((len(values), 3))
    [min_value, max_value] = _get_min_max(values, min, max)
    for i in range(0, len(values)):
        colors[i, :] = _get_blended_color_cyan_blue(min_value, max_value, values[i])
    return colors


def calc_colors_xray(values: Iterable[float], min: float, max: float):
    """Calculate colors using a monochromatic color map."""
    colors = np.zeros((len(values), 3))
    [min_value, max_value] = _get_min_max(values, min, max)
    for i in range(0, len(values)):
        colors[i, :] = _get_blended_color_mono(min_value, max_value, values[i])
    return colors


def calc_colors_blackbody(values: Iterable[float], min: float, max: float):
    """Calculate colors using a black bodies radiation color map."""
    colors = np.zeros((len(values), 3))
    [min_value, max_value] = _get_min_max(values, min, max)
    for i in range(0, len(values)):
        colors[i, :] = _get_blended_color_blackbody(min_value, max_value, values[i])
    return colors


def calc_colors_temperature(values: Iterable[float], min: float, max: float):
    """Calculate colors using a termperature color map."""
    colors = np.zeros((len(values), 3))
    [min_value, max_value] = _get_min_max(values, min, max)
    for i in range(0, len(values)):
        colors[i, :] = _get_blended_color_temperature(min_value, max_value, values[i])
    return colors


def calc_colors_inferno(values: Iterable[float], min: float, max: float):
    """Calculate colors using a inferno color map."""
    colors = np.zeros((len(values), 3))
    [min_value, max_value] = _get_min_max(values, min, max)
    for i in range(0, len(values)):
        colors[i, :] = _get_blended_color_inferno(min_value, max_value, values[i])
    return colors


# assign each distict value a random color
def calc_colors_random(values: Iterable[Any]) -> List[List[float]]:
    """Assign random colors to distinct values."""
    unique_values = len(set(values))
    colors = get_random_colors(unique_values, return_int=False)
    colors = [c.append(1.0) for c in colors]
    color_map = {}
    for v, c in zip(set(values), colors):
        color_map[v] = c
    return colors


def _get_blended_color(min, max, value):
    """Calculate a blended color based on a value within a range."""
    range = max - min
    if range <= 0:
        print("Error: MAX value is smaller than given MIN value!")
        return [1, 0, 1]  # Error, returning magenta

    new_min = 0
    new_max = range
    new_value = value - min
    percentage = 100.0 * (new_value / new_max)

    if new_value <= new_min:
        # Returning blue [0,0,1]
        return np.array([0.0, 0.0, 1.0])
    elif new_value >= new_max:
        # Returning red [1,0,0]
        return np.array([1.0, 0.0, 0.0])
    else:
        if percentage >= 0.0 and percentage <= 25.0:
            # Blue fading to Cyan [0,x,1], where x is increasing from 0 to 1
            frac = percentage / 25.0
            return np.array([0.0, (frac * 1.0), 1.0])

        elif percentage > 25.0 and percentage <= 50.0:
            # Cyan fading to Green [0,1,x], where x is decreasing from 1 to 0
            frac = 1.0 - abs(percentage - 25.0) / 25.0
            return np.array([0.0, 1.0, (frac * 1.0)])

        elif percentage > 50.0 and percentage <= 75.0:
            # Green fading to Yellow [x,1,0], where x is increasing from 0 to 1
            frac = abs(percentage - 50.0) / 25.0
            return np.array([(frac * 1.0), 1.0, 0.0])

        elif percentage > 75.0 and percentage <= 100.0:
            # Yellow fading to red [1,x,0], where x is decreasing from 1 to 0
            frac = 1.0 - abs(percentage - 75.0) / 25.0
            return np.array([1.0, (frac * 1.0), 0.0])

        elif percentage > 100.0:
            # Returning red if the value overshoot the limit.
            return np.array([1.0, 0.0, 0.0])


def _get_blended_color_multi(min, max, value):
    """Calculate a blended color based on input range and value."""
    diff = max - min
    if (diff) <= 0:
        print("Error: MAX value is smaller than given MIN value!")
        return [1, 0, 1]  # Error, returning magenta

    new_min = 0
    new_max = diff
    new_value = value - min
    percentage = 100.0 * (new_value / new_max)

    if new_value <= new_min or new_value >= new_max:
        # Returning red [1,0,0]
        return [1.0, 0.0, 0.0]
    else:
        if percentage >= 0.0 and percentage <= 16.7:
            # Red fading to Magenta [1,0,x], where x is increasing from 0 to 1
            frac = percentage / 16.7
            return [1.0, 0.0, (frac * 1.0)]

        elif percentage > 16.7 and percentage <= 33.4:
            # Magenta fading to blue [x,0,1], where x is decreasing from 1 to 0
            frac = 1.0 - abs(percentage - 16.7) / 16.7
            return [(frac * 1.0), 0.0, 1.0]

        elif percentage > 33.4 and percentage <= 50.0:
            # Blue fading to cyan [0,1,x], where x is increasing from 0 to 1
            frac = abs(percentage - 33.4) / 16.6
            return [0.0, (frac * 1.0), 1.0]

        elif percentage > 50.0 and percentage <= 66.7:
            # Cyan fading to green [0,1,x], where x is decreasing from 1 to 0
            frac = 1.0 - abs(percentage - 50.0) / 16.7
            return [0.0, 1.0, (frac * 1.0)]

        elif percentage > 66.7 and percentage <= 83.4:
            # Green fading to yellow [x,1,0], where x is increasing from 0 to 1
            frac = abs(percentage - 66.7) / 16.7
            return [(frac * 1.0), 1.0, 0.0]

        elif percentage > 83.4 and percentage <= 100.0:
            # Yellow fading to red [1,x,0], where x is decreasing from 1 to 0
            frac = 1.0 - abs(percentage - 83.4) / 16.6
            return [1.0, (frac * 1.0), 0.0]

        elif percentage > 100.0:
            # Returning red if the value overshoots the limit.
            return [1.0, 0.0, 0.0]


def _get_blended_color_blackbody(min, max, value):
    """Calculate a blended color based on input range and value."""
    diff = max - min
    if (diff) <= 0:
        print("Error: MAX value is smaller than given MIN value!")
        return [1, 0, 1]  # Error, returning magenta

    new_min = 0
    new_max = diff
    new_value = value - min
    percentage = 100.0 * (new_value / new_max)

    if new_value <= new_min:
        return [1.0, 1.0, 1.0]
    else:
        if percentage >= 0.0 and percentage <= 25.0:
            # White fading to Yellow [1,1,x], where x is decreasing from 1 to 0
            frac = 1.0 - percentage / 25.0
            return [1.0, 1.0, (frac * 1.0)]

        elif percentage > 25.0 and percentage <= 50.0:
            # Yellow fading to red [1,x,0], where x is decreasing from 1 to 0
            frac = 1.0 - abs(percentage - 25.0) / 25.0
            return [1.0, (frac * 1.0), 0.0]

        elif percentage > 50.0 and percentage <= 100.0:
            # Red fading to dark red [0,x,0], where x is decreasing from 1 to 0.5
            frac = 1.0 - abs(percentage - 50.0) / 50.0
            return [(frac * 1.0), 0.0, 0.0]
        elif percentage > 100.0:
            # Returning red if the value overshoots the limit.
            return [0.0, 0.0, 0.0]


def _get_blended_color_temperature(min, max, value):
    """Calculate a blended color based on input range and value."""
    diff = max - min
    if (diff) <= 0:
        print("Error: MAX value is smaller than given MIN value!")
        return [1, 0, 1]  # Error, returning magenta

    new_min = 0
    new_max = diff
    new_value = value - min
    percentage = 100.0 * (new_value / new_max)

    if new_value <= new_min:
        return [0.0, 0.0, 1.0]
    else:
        if percentage >= 0.0 and percentage <= 50.0:
            # Blue fading to white [x,x,1], where x is increasing from 0 to 1
            frac = percentage / 50.0
            return [(frac * 1.0), (frac * 1.0), 1.0]
        elif percentage > 50.0 and percentage <= 100.0:
            # White fading to red [1,x,x], where x is decreasing from 1 to 0
            frac = 1.0 - abs(percentage - 50.0) / 50.0
            return [1.0, (frac * 1.0), (frac * 1.0)]
        elif percentage > 100.0:
            # Returning red if the value overshoots the limit.
            return [1.0, 0.0, 0.0]


def _get_blended_color_inferno(min, max, value):
    """Calculate a blended color based on input range and value."""
    diff = max - min
    if (diff) <= 0:
        print("Error: MAX value is smaller than given MIN value!")
        return [1, 0, 1]  # Error, returning magenta

    new_min = 0
    new_max = diff
    new_value = value - min
    percentage = 100.0 * (new_value / new_max)

    if new_value <= new_min:
        return [1.0, 1.0, 1.0]
    else:
        if percentage >= 0.0 and percentage <= 33.3:
            # White fading to Orange [1,x,y], where x is decreasing from 1 to 0.5
            # and y is decreasing from 1 to 0
            frac = 1.0 - percentage / 33.3
            return [1.0, 0.5 + (frac * 0.5), (frac * 1.0)]

        elif percentage > 33.3 and percentage <= 66.6:
            # Orange fading to Magenta [1,x,y], where x is decreasing from 0.5 to 0
            # and y is increasing from 0 to 1
            frac = abs(percentage - 33.3) / 33.3
            return [1.0, ((1 - frac) * 0.5), (frac * 1.0)]

        elif percentage > 66.6 and percentage <= 100.0:
            # Magenta fading to black [1,x,1], where x is increasing from 0 to 1
            frac = 1.0 - abs(percentage - 66.6) / 33.4
            return [(frac * 1.0), 0.0, (frac * 1.0)]
        elif percentage > 100.0:
            # Returning red if the value overshoots the limit.
            return [0.0, 0.0, 0.0]


def _get_blended_color_mono(min, max, value):
    """Calculate a monochromatic color based on a value within a range."""
    frac = _get_normalised_value_with_cap(min, max, value)
    return [frac, frac, frac]


def _get_blended_color_yellow_red(min, max, value):
    """Calculate a yellow-to-red color based on a value within a range."""
    frac = 1.0 - _get_normalised_value_with_cap(min, max, value)
    return [1.0, (frac * 1.0), 0.0]


def _get_blended_color_cyan_blue(min, max, value):
    """Calculate a cyan-to-blue color based on a value within a range."""
    frac = _get_normalised_value_with_cap(min, max, value)
    return [0.0, (frac * 1.0), 1.0]


def _get_min_max(values: Iterable[float], min: float = None, max: float = None):
    """Get the minimum and maximum values considering optional bounds."""
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
    """Calculate a normalized value within a range with a cap."""
    range = max - min
    if range <= 0:
        print("Error: MAX value is smaller than given MIN value!")
        return [1, 0, 1]  # Error returning magenta

    new_value = value - min
    new_min = 0
    new_max = range
    frac = 0
    if new_value < new_min:
        frac = 0.0
    elif (new_value >= new_min) and (new_value <= new_max):
        frac = new_value / new_max
    elif new_value >= new_max:
        frac = 1.0

    return frac


color_maps = {
    "rainbow": calc_colors_rainbow,
    "blackbody": calc_colors_blackbody,
    "temperature": calc_colors_temperature,
    "inferno": calc_colors_inferno,
    "multi": calc_colors_multi,
    "xray": calc_colors_xray,
    "warm": calc_colors_warm,
    "cold": calc_colors_cold,
}
