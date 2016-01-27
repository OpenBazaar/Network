'''Platform agnostic functions.'''
from platform import platform
import os
from os.path import expanduser, join

#
# Omission: the 'free' BSD's are not covered here
#

OPTIONS_TMP_FILE = 'openbazaard_options.tmp'

def is_unixlike():
    if is_linux() or is_osx():
        return True
    return False


def is_windows():
    which_os = platform(aliased=True, terse=True).lower()
    return 'window' in which_os


def is_linux():
    which_os = platform(aliased=True, terse=True).lower()
    return 'linux' in which_os


def is_osx():
    which_os = platform(aliased=True, terse=True).lower()
    return 'darwin' in which_os


def options_tmp_path():
    # FIXME Unix only
    return '/tmp/' + OPTIONS_TMP_FILE


# see issue  #163
def default_data_path():
    '''
    Try to fit in with platform file naming conventions.
    '''
    if is_osx():
        return join(home_path(), 'Library', 'Application Support', 'OpenBazzar')
    elif is_linux():
        return join(home_path(), '.openbazaar')

    return join(home_path(), 'OpenBazaar')


def home_path():
    if is_windows():
        return os.environ['HOMEPATH']
    if is_unixlike():
        return expanduser('~')

    error = 'Cannot determine home path for your platform'
    error += ', please report this to OpenBazaar so we can fix it.'
    error += '  Thank you for your patience.'
    raise RuntimeError(error)


if __name__ == '__main__':
    is_linux()
    is_windows()
    is_osx()
    if is_linux():
        assert not is_windows()
        assert not is_osx()
