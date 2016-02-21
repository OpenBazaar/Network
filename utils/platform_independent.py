"""Platform independent utility functions."""
__author__ = 'tobin'

import os
from os.path import expanduser, join, isfile
from platform import platform
import tempfile
#
# If you import anything here from OB it breaks Parser() see openbazaard.py
#

CONFIG = 'tmp_config.ini'       # file created by running OB instance
CONFIG_FILE = 'ob.cfg'

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
        path = os.environ['HOMEPATH']
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


def options_tmp_path():
    """Return a path for use by openbazaard to store command line options."""
    tmp_dir = tempfile.gettempdir()
    return join(tmp_dir, 'ob_cmd_options')


def pid_path():
    """Return a path for use by openbazaard to store pid."""
    tmp_dir = tempfile.gettempdir()
    return join(tmp_dir, 'openbazaard.pid')


def tmp_config_path():
    """Return path for config database."""
    return join(data_path(), CONFIG)


def ordered_config_files():
    """Return list of config files to be passed in order."""
    ordered = []

    if is_linux:
        system = '/etc/openbazaar.conf'
        home_file = join(expanduser('~'), '.openbazaar.conf')
        data_folder_file = join(data_path(), 'openbazaar.conf')
        ordered.extend([system, home_file, data_folder_file])
    elif is_osx:
        system = '/etc/openbazaar.conf'
#        home_file = '' We can't have this until we have an XML version of the config file
        data_folder_file = join(data_path(), 'openbazaar.conf')
        ordered.extend([system, data_folder_file])
    elif is_windows:
        # if windows users run a pre-built executable ob.cfg will suffice
        pass

    return ordered


def ob_repo_config_file():
    """
    Find the git repository config file.
    
    We are doing this 2 level hack so the test suite can find the config file.
    """
    config_file = CONFIG_FILE
    for _ in range(2):
        if not isfile(config_file):
            paths = config_file.rsplit('/', 2)
            config_file = join(paths[0], paths[2])

    return config_file
