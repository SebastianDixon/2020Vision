import unittest
import VISION

class TestVision(unittest.TestCase):
    def test_extremeties(self):
        coordinates = [(1,1), (2,2), (3,3), (4, 4)]
        extremeties = vision.extremeties(*coordinates)
        self.assertEqual(extremeties, [(1, 1), (1, 4), (4, 1), (4, 4)])