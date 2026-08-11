import unittest
from bubble_sort import bubble_sort

class TestBubbleSort(unittest.TestCase):
    def test_bubble_sort(self):
        self.assertEqual(bubble_sort([64, 34, 25, 12, 22, 11, 90]), [11, 12, 22, 25, 34, 64, 90])
        self.assertEqual(bubble_sort([5, 1, 4, 3, 2]), [1, 2, 3, 4, 5])
        self.assertEqual(bubble_sort([1]), [1])
        self.assertEqual(bubble_sort([]), [])

if __name__ == '__main__':
    unittest.main()