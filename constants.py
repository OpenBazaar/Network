__author__ = 'foxcarlos-TeamCreed'
import os
from platform import platform
from os import getcwd
from os.path import expanduser, join, isfile
from ConfigParser import ConfigParser
from urlparse import urlparse

PROTOCOL_VERSION = 10
CONFIG_FILE = 'ob.cfg'      # FIXME: server must be run from within source directory

defaults = {
    'data_folder' : 'OpenBazaar',
    'ksize' : '20',
    'alpha' : '3',
    'transaction_fee' : '10000',
    'libbitcoin_server' : 'tcp://libbitcoin1.openbazaar.org:9091',
    'libbitcoin_server_testnet' : 'tcp://libbitcoin2.openbazaar.org:9091',
    'ssl_cert' : None,
    'ssl_key' : None,
    'seed' : 'seed.openbazaar.org:8080,5b44be5c18ced1bc9400fe5e79c8ab90204f06bebacc04dd9c70a95eaca6e117',
    }

def _platform_agnostic_data_path(data_folder):
    if data_folder:
        if os.path.isabs(data_folder):
            return data_folder

    return join(_platform_agnostic_home_path(), _platform_agnostic_data_folder(data_folder))


def _platform_agnostic_home_path():
    home_path = ''
    if _is_windows():
        home_path = os.environ['HOMEPATH'] # Does this work for versions before Windows 7?
    else:
        home_path = expanduser('~')

    return home_path


def _platform_agnostic_data_folder(data_folder):
    '''
    Try to fit in with platform file naming conventions.
    '''
    if data_folder:
        return data_folder

    name = ''
    if _is_linux():
        name = '.openbazaar'
    else:                       # TODO add clauses for Windows, OSX, and BSD
        name = 'OpenBazaar'

    return name


def _is_windows():
    which_os = platform(aliased=True, terse=True).lower()
    return 'window' in which_os


def _is_linux():
    which_os = platform(aliased=True, terse=True).lower()
    return 'linux' in which_os


def _is_well_formed_seed(seed):
    '''
    Parse seed string url:port,key

    '''
    if ',' in seed:
        url, key = seed.split(',')
        parsed = urlparse(url)
        if _validate_url(parsed.geturl()):
            if _validate_key(key):
                return True
                
    return False


def _validate_url(url):
    # TODO (How tight should the configuration requirements be?)
    return True


def _validate_key(key):
    # TODO (is this done elsewhere in the project?)
    return True


def _is_seed_tuple(tup):
    if isinstance(tup, tuple):
        return 'seed' in tup[0]

    return False


def _tuple_from_seed(seed):
    '''
    Accepts well formed seed, returns tuple (url:port, key)
    '''
    return tuple(item[1].split(','))


cfg = ConfigParser(defaults)

if isfile(CONFIG_FILE):
    cfg.read(CONFIG_FILE)
else:
    print 'Error: configuration file not found: (%s), using defaults' % CONFIG_FILE

section = 'CONSTANTS'
path = _platform_agnostic_data_path(cfg.get(section, 'DATA_FOLDER'))

DATA_FOLDER = path
KSIZE = int(cfg.get(section, 'KSIZE'))
ALPHA = int(cfg.get(section, 'ALPHA'))
TRANSACTION_FEE = int(cfg.get(section, 'TRANSACTION_FEE'))
LIBBITCOIN_SERVER = cfg.get(section, 'LIBBITCOIN_SERVER')
LIBBITCOIN_SERVER_TESTNET = cfg.get(section, 'LIBBITCOIN_SERVER_TESTNET')
SSL_CERT = cfg.get(section, 'SSL_CERT')
SSL_KEY = cfg.get(section, 'SSL_KEY')
SEEDS = []

items = cfg.items('SEEDS')  # this also includes all default items
for item in items:
    if _is_seed_tuple(item):
        seed = item[1]
        if _is_well_formed_seed(seed):
            SEEDS.append(_tuple_from_seed(seed))
        else:
            print 'Configuration parse error: one of your seeds appears incorrect: %s' % seed


if __name__ == '__main__':
    '''
    Define and Run test suite.
    '''
    
    def test_is_well_formed_seed():
        well_formed = 'seed.openbazaar.org:8080,5b44be5c18ced1bc9400fe5e79c8ab90204f06bebacc04dd9c70a95eaca6e117'
        bad_short_key = 'seed.openbazaar.org:8080,5b44be5c18ced1bc9400fe5e79'
        bad_no_port = 'seed.openbazaar.org,5b44be5c18ced1bc9400fe5e79c8ab90204f06bebacc04dd9c70a95eaca6e117'
        bad_non_existant_host = 'openbazaar.org:8080,5b44be5c18ced1bc9400fe5e79c8ab90204f06bebacc04dd9c70a95eaca6e117'
        
        assert _is_well_formed_seed(well_formed)
#        assert not _is_well_formed_seed(bad_short_key)
#        assert not _is_well_formed_seed(bad_no_port)
#        assert not _is_well_formed_seed(bad_non_existant_host)

    def test_is_seed_tuple():
        good = ('seed.openbazaar.org:8080' , '5b44be5c18ced1bc9400fe5e79c8ab90204f06bebacc04dd9c70a95eaca6e117')
        bad_not_tuple = 'seed.openbazaar.org:8080,5b44be5c18ced1bc9400fe5e79c8ab90204f06bebacc04dd9c70a95eaca6e117'
        bad_not_seed_tuple = ('aoioai', 'aoioai')
        assert _is_seed_tuple(good)
        assert not _is_seed_tuple(bad_not_tuple)
        assert not _is_seed_tuple(bad_not_seed_tuple)


    _is_linux()
    _is_windows()
    if _is_linux():
        assert not _is_windows()

    test_is_well_formed_seed()
    test_is_seed_tuple()
