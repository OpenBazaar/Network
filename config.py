"""Parses configuration file and sets project wide constants."""

__author__ = 'foxcarlos-TeamCreed', 'tobin'

import os
from os.path import join, isfile
from ConfigParser import ConfigParser
from urlparse import urlparse

from utils.platform_independent import data_path, tmp_config_path
from utils.string import str_to_bool

PROTOCOL_VERSION = 13

MAINNET_PORT = 18467
TESTNET_PORT = 28467

def _is_well_formed_seed_string(string):
    """Parse string url:port,key."""
    print string
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
    """Accepts well formed seed string, returns tuple (url:port, key)."""
    return tuple(string.split(','))


def _is_well_formed_data_path(path):
    """Path is well formed if absolute and it exists."""
    if path:
        if os.path.isabs(path):
            if os.path.exists(path):
                return True

    return False


cfg = ConfigParser()
tmp_config = tmp_config_path()

if isfile(tmp_config):
    cfg.read(tmp_config)
else:
    print 'Error: temp config file %s not found in user data directory' % tmp_config
    exit(1)

DATA_FOLDER = ''
config_data_path = cfg.get('CONSTANTS', 'DATA_FOLDER')
if _is_well_formed_data_path(config_data_path):
    DATA_FOLDER = join(config_data_path, '')
else:
    DATA_FOLDER = data_path()

KSIZE = int(cfg.get('CONSTANTS', 'KSIZE'))
ALPHA = int(cfg.get('CONSTANTS', 'ALPHA'))
TRANSACTION_FEE = int(cfg.get('CONSTANTS', 'TRANSACTION_FEE'))
LIBBITCOIN_SERVER = cfg.get('CONSTANTS', 'LIBBITCOIN_SERVER')
LIBBITCOIN_SERVER_TESTNET = cfg.get('CONSTANTS', 'LIBBITCOIN_SERVER_TESTNET')
RESOLVER = cfg.get('CONSTANTS', 'RESOLVER')
LOGLEVEL = cfg.get('CONSTANTS', 'LOGLEVEL')
TESTNET = str_to_bool(cfg.get('CONSTANTS', 'TESTNET'))
ALLOWIP = cfg.get('CONSTANTS', 'ALLOWIP')

NETWORK_PORT = 0
user_defined_network_port = int(cfg.get('CONSTANTS', 'NETWORK_PORT'))
if user_defined_network_port:
    NETWORK_PORT = user_defined_network_port
elif TESTNET:
    NETWORK_PORT = TESTNET_PORT
else:
    NETWORK_PORT = MAINNET_PORT

WEBSOCKET_PORT = int(cfg.get('CONSTANTS', 'WEBSOCKET_PORT'))
RESTAPI_PORT = int(cfg.get('CONSTANTS', 'RESTAPI_PORT'))
HEARTBEAT_PORT = int(cfg.get('CONSTANTS', 'HEARTBEAT_PORT'))
SSL = str_to_bool(cfg.get('AUTHENTICATION', 'SSL'))
SSL_CERT = cfg.get('AUTHENTICATION', 'SSL_CERT')
SSL_KEY = cfg.get('AUTHENTICATION', 'SSL_KEY')
USERNAME = cfg.get('AUTHENTICATION', 'USERNAME')
PASSWORD = cfg.get('AUTHENTICATION', 'PASSWORD')

SEEDS = []
items = cfg.items('SEEDS')  # this also includes items in DEFAULTS
for item in items:
    if _is_seed_tuple(item):
        seed = item[1]
        if _is_well_formed_seed_string(seed):
            new_seed = _tuple_from_seed_string(seed)
            if new_seed not in SEEDS:
                SEEDS.append(new_seed)
        else:
            print 'Warning: please check your configuration file: %s' % seed


if __name__ == '__main__':

    def test_is_well_formed_seed_string():
        well_formed = 'seed.openbazaar.org:8080,5b44be5c18ced1bc9400fe5e79c8ab90204f06bebacc04dd9c70a95eaca6e117'
        # test ill-formed url's (build fails with pylint error if we use long/descriptive names
        # key too short
        # bad_1 = 'seed.openbazaar.org:8080,5b44be5c18ced1bc9400fe5e79'
        # no port number
        # bad_2 = 'seed.openbazaar.org,5b44be5c18ced1bc9400fe5e79c8ab90204f06bebacc04dd9c70a95eaca6e117'
        # no host name in url
        # bad_3 = 'openbazaar.org:8080,5b44be5c18ced1bc9400fe5e79c8ab90204f06bebacc04dd9c70a95eaca6e117'

        assert _is_well_formed_seed_string(well_formed)
        # assert not _is_well_formed_seed_string(b1)
        # assert not _is_well_formed_seed_string(b2)
        # assert not _is_well_formed_seed_string(b3)

    def test_is_seed_tuple():
        good = ('seed.openbazaar.org:8080', '5b44be5c18ced1bc9400fe5e79c8ab90204f06bebacc04dd9c70a95eaca6e117')
        bad_not_tuple = 'seed.openbazaar.org:8080,5b44be5c18ced1bc9400fe5e79c8ab90204f06bebacc04dd9c70a95eaca6e117'
        bad_not_seed_tuple = ('aoioai', 'aoioai')
        assert _is_seed_tuple(good)
        assert not _is_seed_tuple(bad_not_tuple)
        assert not _is_seed_tuple(bad_not_seed_tuple)


    test_is_well_formed_seed_string()
    test_is_seed_tuple()
