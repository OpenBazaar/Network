'''Parses configuration file and sets project wide constants.
'''
__author__ = 'foxcarlos-TeamCreed', 'Tobin Harding'

import os
from os.path import join, isfile
from ConfigParser import ConfigParser, NoSectionError
from urlparse import urlparse
from platform_agnostic import options_tmp_path, is_linux, is_windows,\
    is_osx, default_data_path


PROTOCOL_VERSION = 10
WINDOWS_CONFIG_FILE = 'ob.cfg'

DEFAULTS = {
    'data_folder': None,
    'ksize': '20',
    'alpha': '3',
    'transaction_fee': '10000',
    'libbitcoin_server': 'tcp://libbitcoin1.openbazaar.org:9091',
    'libbitcoin_server_testnet': 'tcp://libbitcoin2.openbazaar.org:9091',
    'resolver': 'http://resolver.onename.com/',
    'ssl': False,
    'ssl_cert': None,
    'ssl_key': None,
    # FIXME nameing convention differs (use of underscores)
    'daemon': False,
    'testnet': False,
    'loglevel': 'info',
    'allowip': '127.0.0.1',
    'node_port': None,          # NEW: needs core dev confirmation
    'restapiport': '18469',     
    'websocketport': '18466',
    'pidfile': 'openbazaard.pid',
    'seed': 'seed.openbazaar.org:8080,5b44be5c18ced1bc9400fe5e79c8ab90204f06bebacc04dd9c70a95eaca6e117',
}


def _data_path(data_folder):
    '''
    Used to set DATA_FOLDER.
    '''
    if data_folder:
        if os.path.isabs(data_folder):
            return data_folder

    return default_data_folder(data_folder)


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
        if isfile(config_file):
            config_parser.read(config_file)


def _parse_linux_config_files(config_parser):
    basename = 'openbazaar.conf'
    system_wide_config_file = join('/etc', basename)
    user_config_file = join(default_data_path(), basename)
    options_config_file = options_tmp_path()
    in_order_config_files = [system_wide_config_file, user_config_file, options_config_file]
    for config_file in in_order_config_files:
        if isfile(config_file):
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
    if testnet:
        return 28467
    return 18467


def _parse_options(config_parser):
    options = options_tmp_path()
    if isfile(options):
        config_parser.read(options)


cfg = ConfigParser(DEFAULTS)
_parse_config_file(cfg)
_parse_options(cfg)

available_sections = cfg.sections()
section = 'CONSTANTS'
if section not in available_sections:
    section = 'DEFAULT'
    
DATA_FOLDER = _data_path(cfg.get(section, 'DATA_FOLDER'))
KSIZE = int(cfg.get(section, 'KSIZE'))
ALPHA = int(cfg.get(section, 'ALPHA'))
TRANSACTION_FEE = int(cfg.get(section, 'TRANSACTION_FEE'))
LIBBITCOIN_SERVER = cfg.get(section, 'LIBBITCOIN_SERVER')
LIBBITCOIN_SERVER_TESTNET = cfg.get(section, 'LIBBITCOIN_SERVER_TESTNET')
RESOLVER = cfg.get(section, 'RESOLVER')
SSL = cfg.get(section, 'SSL'),
SSL_CERT = cfg.get(section, 'SSL_CERT')
SSL_KEY = cfg.get(section, 'SSL_KEY')
DAEMON = cfg.get(section, 'DAEMON')
TESTNET = cfg.get(section, 'TESTNET')
LOGLEVEL = cfg.get(section, 'LOGLEVEL')
ALLOWIP = cfg.get(section, 'ALLOWIP')
NODE_PORT = cfg.get(section, 'NODE_PORT')
RESTAPIPORT = cfg.get(section, 'RESTAPIPORT')
WEBSOCKETPORT = cfg.get(section, 'WEBSOCKETPORT')
PIDFILE = cfg.get(section, 'PIDFILE')
SEEDS = []

section = 'SEEDS'
if section not in available_sections:
    section = 'DEFAULT'

items = cfg.items(section)  # this also includes items in DEFAULTS
for item in items:
    if _is_seed_tuple(item):
        seed = item[1]
        if _is_well_formed_seed_string(seed):
            SEEDS.append(_tuple_from_seed_string(seed))
        else:
            print 'Warning: please check your configuration file: %s' % seed


if __name__ == '__main__':
    '''
    Define and run tests.
    '''
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


    is_linux()
    is_windows()
    is_osx()
    if is_linux():
        assert not is_windows()
        assert not is_osx()

    test_is_well_formed_seed_string()
    test_is_seed_tuple()
