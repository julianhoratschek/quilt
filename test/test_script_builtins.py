import script.builtins as m
import unittest

class BuiltinTest(unittest.TestCase):
    def test_btwn(self):
        self.assertTrue(m.builtin_btwn([1, 0, 2]))
        self.assertFalse(m.builtin_btwn([0, 1, 2]))
        self.assertFalse(m.builtin_btwn([]))
        self.assertFalse(m.builtin_btwn([1, 2, 3, 4]))
        self.assertFalse(m.builtin_btwn([1, 2]))


if __name__ == "__main__":
    unittest.main()