'''Parses configuration file and sets project wide constants.

This file has intrinsic naming difficulties because it is trying to be platform
agnostic but naming variables is inherently platform specific (i.e directory vs
folder)
'''
__author__ = 'foxcarlos-TeamCreed', 'Tobin Harding'

import os
from os.path import join, isfile
from ConfigParser import ConfigParser
from urlparse import urlparse

PROTOCOL_VERSION = 10
CONFIG_FILE = join(os.getcwd(), 'ob.cfg')

# FIXME probably a better way to do this. This curretly checks two levels deep
for i in range(2):
    if not isfile(CONFIG_FILE):
        paths = CONFIG_FILE.rsplit('/', 2)
        CONFIG_FILE = join(paths[0], paths[2])

DEFAULTS = {
    # Default project config file may now remove these items
    'data_folder': 'OpenBazaar',  # FIXME change to 'None' when issue #163 is resolved
    'ksize': '20',
    'alpha': '3',
    'transaction_fee': '10000',
    'libbitcoin_server': 'tcp://libbitcoin1.openbazaar.org:9091',
    'libbitcoin_server_testnet': 'tcp://libbitcoin2.openbazaar.org:9091',
    'resolver': 'http://resolver.onename.com/',
    'ssl_cert': None,
    'ssl_key': None,
    'seed': 'seed.openbazaar.org:8080,5b44be5c18ced1bc9400fe5e79c8ab90204f06bebacc04dd9c70a95eaca6e117',
}


def _platform_agnostic_data_path(data_folder):
    '''
    Create absolute path name, exported as DATA_FOLDER.

    User may configure using relative path, absolute path or use default.
      Relative path puts named folder in users home directory.
      Absolute path uses (obviously) the named absolute path.
      Default is currently to use 'OpenBazaar' in home directory.

    See issue #163
    '''
    if data_folder:
        if os.path.isabs(data_folder):
            return data_folder

    return join(_platform_agnostic_home_path(), _platform_agnostic_data_folder(data_folder), '')


def _platform_agnostic_home_path():
    home_path = ''
    if _is_windows():
        home_path = os.environ['HOMEPATH'] # Does this work for versions before Windows 7?
    else:
        home_path = expanduser('~')

    return home_path


# see issue  #163
def _platform_agnostic_data_folder(data_folder):
    '''
    Try to fit in with platform file naming conventions.
    '''
    if data_folder:
        return data_folder

    name = ''
    if _is_osx():
        name = join('Library', 'Application Support', 'OpenBazzar')
    elif _is_linux():
        name = '.openbazaar'
    else:                       # TODO add clauses for Windows, and BSD
        name = 'OpenBazaar'

    return name


def _is_windows():
    which_os = platform(aliased=True, terse=True).lower()
    return 'window' in which_os


def _is_linux():
    which_os = platform(aliased=True, terse=True).lower()
    return 'linux' in which_os


def _is_osx():
    which_os = platform(aliased=True, terse=True).lower()
    return 'darwin' in which_os


def _is_well_formed_seed_string(string):
    '''
    Parse string url:port,key

    '''
    if ',' in string:
        url, key = string.split(',')
        parsed = urlparse(url)
        if _validate_url(parsed.geturl()):
            if _validate_key(key):
                return True

    return False


def _validate_url(url):
    # TODO (How tight should the configuration requirements for a url be?)
    return True


def _validate_key(key):
    # TODO (is this done elsewhere in the project?)
    return True


def _is_seed_tuple(tup):
    if isinstance(tup, tuple):
        return 'seed' in tup[0]

    return False


def _tuple_from_seed_string(string):
    '''
    Accepts well formed seed string, returns tuple (url:port, key)
    '''
    return tuple(string.split(','))


def _parse_config_file(config_parser):
    if is_windows():
        _parse_windows_config_file(config_parser)
    elif is_osx():
        _parse_osx_config_files(config_parser)
    elif is_linux():
        _parse_linux_config_files(config_parser)


def _parse_windows_config_file(config_parser):
    if isfile(WINDOWS_CONFIG_FILE):
        config_parser.read(WINDOWS_CONFIG_FILE)
    else:
        print 'Warning: configuration file (%s) not found, using default values' % WINDOWS_CONFIG_FILE


def _parse_osx_config_files(config_parser):
    system_wide_config_file = '/etc/openbazaar.conf'

    # user config file should be ~/Library/Preferences/OpenBazaar.app
    # but they must be in XML

    options_config_file = options_tmp_path()
    in_order_config_files = [system_wide_config_file, options_config_file]
    for config_file in in_order_config_files:
        config_parser.read(config_file)


def _parse_linux_config_files(config_parser):
    basename = 'openbazaar.conf'
    system_wide_config_file = join('/etc', basename)
    user_config_file = join(default_data_path(), basename)
    options_config_file = options_tmp_path()
    in_order_config_files = [system_wide_config_file, user_config_file, options_config_file]
    for config_file in in_order_config_files:
        config_parser.read(config_file)


def _data_path(absolute_path=None):
    '''
    Used to set constant DATA_FOLDER.
    '''
    if absolute_path:
        if os.path.isabs(absolute_path):
            return absolute_path

    return default_data_path()

def _openbazaard_node_port(port=None, testnet=None):
    '''
    Port used for node to node communication.
    '''
    if port:
        return port
    dif testnet:
        return 28467
    return 18467


cfg = ConfigParser(DEFAULTS)

if isfile(CONFIG_FILE):
    cfg.read(CONFIG_FILE)
else:
    print 'Warning: configuration file not found: (%s), using default values' % CONFIG_FILE

DATA_FOLDER = _platform_agnostic_data_path(cfg.get('CONSTANTS', 'DATA_FOLDER'))
KSIZE = int(cfg.get('CONSTANTS', 'KSIZE'))
ALPHA = int(cfg.get('CONSTANTS', 'ALPHA'))
TRANSACTION_FEE = int(cfg.get('CONSTANTS', 'TRANSACTION_FEE'))
LIBBITCOIN_SERVER = cfg.get('CONSTANTS', 'LIBBITCOIN_SERVER')
LIBBITCOIN_SERVER_TESTNET = cfg.get('CONSTANTS', 'LIBBITCOIN_SERVER_TESTNET')
RESOLVER = cfg.get('CONSTANTS', 'RESOLVER')
SSL_CERT = cfg.get('CONSTANTS', 'SSL_CERT')
SSL_KEY = cfg.get('CONSTANTS', 'SSL_KEY')
SEEDS = []

items = cfg.items('SEEDS')  # this also includes items in DEFAULTS
for item in items:
    if _is_seed_tuple(item):
        seed = item[1]
        if _is_well_formed_seed_string(seed):
            SEEDS.append(_tuple_from_seed_string(seed))
        else:
            print 'Warning: please check your configuration file: %s' % seed


if __name__ == '__main__':

    def test_is_well_formed_seed_string():
        well_formed = 'seed.openbazaar.org:8080,5b44be5c18ced1bc9400fe5e79c8ab90204f06bebacc04dd9c70a95eaca6e117'
        # test ill-formed url's (build fails with pylint error if we use long/descriptive names
        # key too short
#        bad_1 = 'seed.openbazaar.org:8080,5b44be5c18ced1bc9400fe5e79'
        # no port number
#        bad_2 = 'seed.openbazaar.org,5b44be5c18ced1bc9400fe5e79c8ab90204f06bebacc04dd9c70a95eaca6e117'
        # no host name in url
#        bad_3 = 'openbazaar.org:8080,5b44be5c18ced1bc9400fe5e79c8ab90204f06bebacc04dd9c70a95eaca6e117'

        assert _is_well_formed_seed_string(well_formed)
#        assert not _is_well_formed_seed_string(b1)
#        assert not _is_well_formed_seed_string(b2)
#        assert not _is_well_formed_seed_string(b3)

    def test_is_seed_tuple():
        good = ('seed.openbazaar.org:8080', '5b44be5c18ced1bc9400fe5e79c8ab90204f06bebacc04dd9c70a95eaca6e117')
        bad_not_tuple = 'seed.openbazaar.org:8080,5b44be5c18ced1bc9400fe5e79c8ab90204f06bebacc04dd9c70a95eaca6e117'
        bad_not_seed_tuple = ('aoioai', 'aoioai')
        assert _is_seed_tuple(good)
        assert not _is_seed_tuple(bad_not_tuple)
        assert not _is_seed_tuple(bad_not_seed_tuple)


    _is_linux()
    _is_windows()
    _is_osx()
    if _is_linux():
        assert not _is_windows()
        assert not _is_osx()

    test_is_well_formed_seed_string()
    test_is_seed_tuple()
