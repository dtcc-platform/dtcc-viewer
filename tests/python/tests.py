import unittest
from dtcc_viewer import *


class TestPythonCode(unittest.TestCase):

    def test_add(self):
        assert add(1, 2) == 3

    def test_sub(self):
        assert sub(1, 2) == -1

    def test_complex(self):
        c1 = Complex(1, 2)
        c2 = Complex(3, 4)

        assert (c1 + c2 == Complex(4, 6))
        assert (c1 - c2 == Complex(-2, -2))
        assert c1 * c2 == Complex(-5, 10)
        assert c1 / c2 == Complex(0.44, 0.08)


class TestCppCode(unittest.TestCase):

    def test_mul(self):
        assert mul(1, 2) == 2

    def test_div(self):
        assert div(1, 2) == 0


if __name__ == '__main__':
    unittest.main()
