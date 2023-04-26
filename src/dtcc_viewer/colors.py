import numpy as np
from typing import List, Iterable


def get_min_max(values: Iterable[float], min:float, max:float):
    if(min == None):    
        min_value = np.min(values)
    else:
        min_value = min

    if(max == None):    
        max_value = np.max(values)
    else:
        max_value = max

    return min_value, max_value    

def calc_colors_rainbow(values:Iterable[float], min:float, max:float) -> List[List[float]]:
    colors = []
    [min_value, max_value] = get_min_max(values, min, max)     
    for i in range(0, len(values)):
        c = _get_blended_color(min_value, max_value, values[i]) 
        colors.append(c)
    return colors    

def calc_colors_fire(values:Iterable[float], min:float, max:float) -> List[List[float]]:
    colors = []    
    [min_value, max_value] = get_min_max(values, min, max)
    for i in range(0, len(values)):
        c = _get_blended_color_yellow_red(min_value, max_value, values[i]) 
        colors.append(c)
    return colors    

def calc_colors_cold(values:Iterable[float], min:float, max:float) -> List[List[float]]:
    colors = []    
    [min_value, max_value] = get_min_max(values, min, max)
    for i in range(0, len(values)):
        c = _get_blended_color_cyan_blue(min_value, max_value, values[i]) 
        colors.append(c)
    return colors 

# Calculate bleded color in a monochrome scale
def calc_colors_mono(values:Iterable[float], min:float, max:float) -> List[List[float]]:
    colors = []    
    [min_value, max_value] = get_min_max(values, min, max)
    for i in range(0, len(values)):
        fColor = _get_blended_color_mono(min_value, max_value, values[i]) 
        colors.append(fColor)
    return colors    

# Calculate color blend for a range of values where some are excluded using a True-False mask
def calc_colors_with_mask(values, mask) -> List[List[float]]:    
    colors = []
    min = np.min(values[mask])
    max = np.max(values[mask])
    for i in range(0, len(values)):
        if mask[i]:
            c = _get_blended_color(min, max, values[i])
        else:
            c = [0.2,0.2,0.2,1] 
        colors.append(c)
    return colors    



def _get_blended_color(min, max, value):
    diff = max - min
    newMax = diff
    newValue = value - min
    percentage = 100.0 * (newValue / newMax)

    if (percentage >= 0.0 and percentage <= 25.0):
        #Blue fading to Cyan [0,x,1], where x is increasing from 0 to 1
        frac = percentage / 25.0
        return [0.0, (frac * 1.0), 1.0 , 1.0]

    elif (percentage > 25.0 and percentage <= 50.0):
        #Cyan fading to Green [0,1,x], where x is decreasing from 1 to 0
        frac = 1.0 - abs(percentage - 25.0) / 25.0
        return [0.0, 1.0, (frac * 1.0), 1.0]

    elif (percentage > 50.0 and percentage <= 75.0):
        #Green fading to Yellow [x,1,0], where x is increasing from 0 to 1
        frac = abs(percentage - 50.0) / 25.0
        return [(frac * 1.0), 1.0, 0.0, 1.0 ]

    elif (percentage > 75.0 and percentage <= 100.0):
        #Yellow fading to red [1,x,0], where x is decreasing from 1 to 0
        frac = 1.0 - abs(percentage - 75.0) / 25.0
        return [1.0, (frac * 1.0), 0.0, 1.0]

    elif (percentage > 100.0):
        #Returning red if the value overshoot the limit.
        return [1.0, 0.0, 0.0, 1.0 ]

    return [0.5, 0.5, 0.5, 1.0 ]

def _get_blended_color_mono(min, max, value):
    diff = max - min
    newMax = diff
    newValue = value - min
    frac = 0
    if newMax > 0:
        frac = newValue / newMax
    return [frac, frac, frac, 1.0]

def _get_blended_color_red_blue(max, value):
    frac = 0
    if(max > 0):
        frac = value / max
    return [frac, 0.0, 1 - frac, 1.0]

def _get_blended_color_yellow_red(min, max, value):
    diff = max - min
    newMax = diff
    newValue = value - min
    frac = 0
    if newMax > 0:
        # Yellow [1, 1, 0] fading to red [1, 0, 0] 
        frac = newValue / newMax
        return [1.0, (frac * 1.0), 0.0, 1.0]
    else:
        return [1.0, 1.0, 1.0, 1.0]
        

def _get_blended_color_cyan_blue(min, max, value):
    diff = max - min
    newMax = diff
    newValue = value - min
    frac = 0
    if newMax > 0:
        # Yellow [1, 1, 0] fading to red [1, 0, 0] 
        frac = newValue / newMax
        return [0.0, (frac * 1.0), 1.0, 1.0]
    else:
        return [1.0, 1.0, 1.0, 1.0]


color_maps = {
        "mono" : calc_colors_mono,
        "rainbow" : calc_colors_rainbow,
        "fire" : calc_colors_fire,
        "cold" : calc_colors_cold,
}

