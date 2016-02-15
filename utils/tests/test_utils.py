import unittest

from utils.platform_independent import is_linux, is_osx, is_unix_like, is_windows


class UtilsPlatformIndependant(unittest.TestCase):

    def setUp(self):
        pass

    def test_platform_predicates(self):
        is_linux()
        is_windows()
        is_osx()
        is_unix_like()

        if is_linux():
            self.assertTrue(is_unix_like())
            self.assertFalse(is_windows())
            self.assertFalse(is_osx())

        if is_osx():
            self.assertTrue(is_unix_like())
            self.assertFalse(is_windows())
            self.assertFalse(is_linux())

        if is_windows():
            self.assertFalse(is_linux())
            self.assertFalse(is_osx())
            self.assertFalse(is_unix_like())
