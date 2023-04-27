import numpy as np
from dtcc_viewer import colors
from dtcc_viewer.colors import color_maps
from pprint import pp

class TestColors:

    def setup_method(self):

        pass

    def test_colors(self):
        values = np.arange(100)
        min = np.min(values)
        max = np.max(values)
        cs_a = colors.calc_colors_arctic(values, min, max)
        cs_c = colors.calc_colors_cold(values, min, max)
        cs_f = colors.calc_colors_warm(values, min, max)
        cs_r = colors.calc_colors_rainbow(values, min, max)
        
        assert (len(cs_a) == len(cs_c) and len(cs_a) == len(cs_f) and len(cs_a) == len(cs_r))


    def test_colors_2(self):
        values = np.arange(100)
        min = np.mean(values)
        max = np.max(values)
        cs_a = colors.calc_colors_arctic(values, min, max)
        cs_c = colors.calc_colors_cold(values, min, max)
        cs_f = colors.calc_colors_warm(values, min, max)
        cs_r = colors.calc_colors_rainbow(values, min, max)

        assert (len(cs_a) == len(cs_c) and len(cs_a) == len(cs_f) and len(cs_a) == len(cs_r))

if __name__ == '__main__':

    test = TestColors()
    test.test_colors_2()
    

