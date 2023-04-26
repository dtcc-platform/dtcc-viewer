# Copyright (C) 2023 Anders Logg
# Licensed under the MIT License

import sys
import numpy as np
from pprint import pp
import dtcc_viewer.colors as colors 

#from dtcc_viewer.colors import color_maps

def main():

    print("Hello world!")
    pp(sys.path)

    a = np.arange(10)

    c1 = colors.calc_colors_fire(a, 0, 10)    
    c2 = colors.calc_colors_rainbow(a, 0, 10)    
    c3 = colors.calc_colors_mono(a, 0, 10)    

    print(c1)
    print(c2)
    print(c3)




if __name__ == '__main__':

    main()        
