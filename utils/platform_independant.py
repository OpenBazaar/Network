"""Platform independant utility functions."""
__author__ = 'tobin'

from os import environ
from os.path import expanduser, join
from platform import platform

def is_windows():
    """Are we on a Windows platform."""
    which_os = platform(aliased=True, terse=True).lower()
    return 'window' in which_os


def is_linux():
    """Are we on a Linux platform."""
    which_os = platform(aliased=True, terse=True).lower()
    return 'linux' in which_os


def is_osx():
    """Are we on the OS X platform."""
    which_os = platform(aliased=True, terse=True).lower()
    return 'darwin' in which_os

def is_unix_like():
    """Are we on a Unix-like platform."""
    return is_osx() or is_linux()


def is_bsd():
    """We should really support BSD as well."""
    pass


def home_path():
    """Determine system home path."""
    path = ''
    if is_windows():
        path = environ['HOMEPATH']
    else:
        path = expanduser('~')

    return path


def data_path():
    """
    Create absolute path name.

    This is used to set DATA_FOLDER if it is not configured by user.
    """
    return join(home_path(), _data_folder())


def _data_folder():
    """Try to fit in with platform file naming conventions."""
    name = ''
    if is_osx():
        name = join('Library', 'Application Support', 'OpenBazaar')
    elif is_linux():
        name = '.openbazaar'
    else:                       # TODO add clauses for Windows, and BSD
        name = 'OpenBazaar'

    return join(name, '')
