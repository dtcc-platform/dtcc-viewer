import pyrr
import numpy as np
from enum import IntEnum

class MeshShading(IntEnum):
    wireframe = 1
    shaded_basic = 2
    shaded_fancy = 3
    shaded_shadows = 4

class MeshColor(IntEnum):
    color = 1
    white = 2

class ParticleColor(IntEnum):
    color = 1        
    white = 2
    

def calc_blended_color(min, max, value):
    diff = max - min
    if(diff) <= 0:
        print("Error: Given MAX-MIN range is zero or the MAX value is smaller than given MIN value!")
        return [1,0,1]    # Error, returning magenta
    
    new_min = 0
    new_max = diff
    new_value = value - min
    percentage = 100.0 * (new_value / new_max)

    if(new_value <= new_min or new_value >= new_max):
        #Returning red [1,0,0]
        return [1.0, 0.0, 0.0]
    else:
        if (percentage >= 0.0 and percentage <= 10.0):
            #Red fading to Magenta [1,0,x], where x is increasing from 0 to 1
            frac = percentage / 10.0
            return [1.0, 0.0, (frac * 1.0)]

        elif (percentage > 10.0 and percentage <= 30.0):
            #Magenta fading to blue [x,0,1], where x is decreasing from 1 to 0
            frac = 1.0 - abs(percentage - 10.0) / 20.0
            return [(frac * 1.0), 0.0, 1.0]

        elif (percentage > 30.0 and percentage <= 50.0):
            #Blue fading to cyan [0,1,x], where x is increasing from 0 to 1
            frac = abs(percentage - 30.0) / 20.0
            return [0.0, (frac * 1.0), 1.0]

        elif (percentage > 50.0 and percentage <= 70.0):
            #Cyan fading to green [0,1,x], where x is decreasing from 1 to 0
            frac = 1.0 - abs(percentage - 50.0) / 20.0
            return [0.0, 1.0, (frac * 1.0)]

        elif (percentage > 70.0 and percentage <= 90.0):
            #Green fading to yellow [x,1,0], where x is increasing from 0 to 1
            frac = abs(percentage - 70.0) / 20.0
            return [(frac * 1.0), 1.0, 0.0]
        
        elif (percentage > 90.0 and percentage <= 100.0):
            #Yellow fading to red [1,x,0], where x is decreasing from 1 to 0
            frac = 1.0 - abs(percentage - 90.0) / 10.0
            return [1.0, (frac * 1.0), 0.0]

        elif (percentage > 100.0):
            #Returning red if the value overshoots the limit.
            return [1.0, 0.0, 0.0]

