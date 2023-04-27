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

def calc_colors_warm(values:Iterable[float], min:float, max:float) -> List[List[float]]:
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

# Calculate bleded color in a monochrome scale
def calc_colors_arctic(values:Iterable[float], min:float, max:float) -> List[List[float]]:
    colors = []
    for i in range(0, len(values)):
        fColor = [0.95,0.95,0.95,1] 
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
    if(diff) <= 0:
        print("Error: Given MAX-MIN range is zero or the MAX value is smaller than given MIN value!")
        return [1,0,1,1]    # Error, returning magenta
    
    new_min = 0
    new_max = diff
    new_value = value - min
    percentage = 100.0 * (new_value / new_max)

    if(new_value <= new_min):
        #Returning blue [0,0,1]
        return [0.0, 0.0, 1.0 , 1.0]
    elif (new_value >= new_max):
        #Returning red [1,0,0]
        return [1.0, 0.0, 0.0 , 1.0]
    else:
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

def _get_blended_color_mono(min, max, value):
    frac = _get_normalised_value_with_cap(min, max, value)
    return [frac, frac, frac, 1.0]

def _get_blended_color_yellow_red(min, max, value):    
    frac = _get_normalised_value_with_cap(min, max, value)
    return [1.0, (frac * 1.0), 0.0, 1.0]

def _get_blended_color_cyan_blue(min, max, value):
    frac = _get_normalised_value_with_cap(min, max, value)
    return [0.0, (frac * 1.0), 1.0, 1.0]

def _get_normalised_value_with_cap(min, max, value):
    diff = max - min
    if(diff) <= 0:
        print("Error: Given MAX-MIN range is zero or the MAX value is smaller than given MIN value!")
        return [1,0,1,1]    # Error returning magenta

    new_value = value - min
    new_min = 0
    new_max = diff
    frac = 0
    if new_value < new_min:
        frac = 0.0                                          #frac = 0 => Red 
    elif (new_value >= new_min) and (new_value <= new_max):    
        frac = new_value / new_max                          #frac = 1 => Yellow
    elif new_value >= new_max:
        frac = 1.0

    return frac    

color_maps = {
        "arctic" : calc_colors_arctic,
        "mono" : calc_colors_mono,
        "rainbow" : calc_colors_rainbow,
        "warm" : calc_colors_warm,
        "cold" : calc_colors_cold,
}

