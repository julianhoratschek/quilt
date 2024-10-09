import script.builtins as m
import unittest

class BuiltinTest(unittest.TestCase):
    def test_btwn(self):
        self.assertTrue(m.builtin_btwn([1, 0, 2]))
        self.assertFalse(m.builtin_btwn([0, 1, 2]))
        self.assertFalse(m.builtin_btwn([]))
        self.assertFalse(m.builtin_btwn([1, 2, 3, 4]))
        self.assertFalse(m.builtin_btwn([1, 2]))
        self.assertFalse(m.builtin_btwn([1, -1, 2]))

    def test_counter(self):
        self.assertEqual(m.builtin_counter(["cntr"]), 1)
        self.assertEqual(m.builtin_counter(["cntr"]), 2)
        self.assertEqual(m.builtin_counter(["ncntr", 1, 2]), 1)
        self.assertEqual(m.builtin_counter(["cntr"]), 3)
        self.assertEqual(m.builtin_counter(["ncntr"]), 3)
        self.assertEqual(m.builtin_counter(["ncntr"]), 5)

    def test_empty(self):
        self.assertTrue(m.builtin_empty([[]]), True)
        self.assertTrue(m.builtin_empty([[1]]), False)

if __name__ == "__main__":
    unittest.main()