import unittest

from utils.platform_independant import is_linux, is_osx, is_unix_like, is_windows


def test_platform_predicates():
    is_linux()
    is_windows()
    is_osx()
    is_unix_like()

    if is_linux():
        assert is_unix_like()
        assert not is_windows()
        assert not is_osx()

    if is_osx():
        assert is_unix_like()
        assert not is_windows()
        assert not is_linux()

    if is_windows():
        assert not is_linux()
        assert not is_osx()
        assert not is_unix_like()
