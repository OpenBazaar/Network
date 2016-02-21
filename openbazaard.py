"""OpenBazaard main file. `python openbazaard -h` for help."""
__author__ = 'chris', 'tobin'

import argparse
from os.path import isfile
from ConfigParser import ConfigParser, NoSectionError

from utils.platform_independent import tmp_config_path, ordered_config_files
#
# If you import anything else here from OB it breaks _parse_command_line()
#
# There is a temporal coupling between OB imports and parsing the command line.
# Parsing must complete before any other OB imports so that the system wide
# tmp config file has been written
#
PROTOCOL_VERSION = 13

MAINNET_PORT = 18467
TESTNET_PORT = 28467

DEFAULTS = {
    'data_folder': None,
    'ksize': '20',
    'alpha': '3',
    'transaction_fee': '10000',
    'libbitcoin_server': 'tcp://libbitcoin1.openbazaar.org:9091',
    'libbitcoin_server_testnet': 'tcp://libbitcoin2.openbazaar.org:9091',
    'resolver': 'http://resolver.onename.com/',
    'loglevel': 'info',
    'testnet': 'True',
    'network_port': '0',
    'websocket_port': '18466',
    'restapi_port': '18469',
    'heartbeat_port': '18470',
    'allowip' : '127.0.0.1',
}


def _parse_command_line():
    parser = argparse.ArgumentParser(
        description='OpenBazaar-Server v0.1.0',
        usage='python openbazaard.py  [<args>]')

    # Remove short form options to conform to Unix semantic standards.
    # Ref: The Art of UNIX Programming - Eric S. Raymond (section 10.5.1)
    parser.add_argument('--testnet', action='store_true',
                        help="use the test network")
    parser.add_argument('--ssl', action='store_true',
                        help="use ssl on api connections. you must set the path to your "
                             "certificate and private key in the config file.")
    parser.add_argument('--loglevel',
                        help="set the logging level [debug, info, warning, error, critical]")
    parser.add_argument('-p', '--network_port',
                        help="set the network port")
    parser.add_argument('--restapi_port',
                        help="set the rest api port")
    parser.add_argument('--websocket_port',
                        help="set the websocket api port")
    parser.add_argument('--heartbeat_port',
                        help="set the heartbeat port")
    parser.add_argument('--allowip',
                        help="only allow api connections from this IP")

    args = parser.parse_args()
    options = _dict_from_args(args)
    _store_config_with_options(options)


def _dict_from_args(args):
    """Return dictionary of option:value for set options."""
    options = {}
    for arg in vars(args):
        if getattr(args, arg):
            options[arg] = str(getattr(args, arg))

    return options


def _store_config_with_options(options):
    """Save current configuration to file."""
    cfg = _cfg_with_options(options)
    outf = open(tmp_config_path(), 'w+')
    cfg.write(outf)


def _cfg_with_options(options):
    """Parse config file hierarchy and options."""
    cfg = _initialise_cfg()
    cfg = _parse_config_files(cfg)
    cfg = _set_cfg_options(cfg, options)

    return cfg


def _initialise_cfg():
    """Make sure we have all the sections we need."""
    cfg = ConfigParser(DEFAULTS)
    cfg.add_section('CONSTANTS')
    cfg.add_section('SEEDS')
    cfg = _setup_auth_section(cfg)

    return cfg


def _parse_config_files(cfg):
    """
    Parse config file hierarchy.
    
    We look for config files according to platform methodologies. If, and only
    if, none are found then we parse the config file from the OpenBazaar github
    repository (i.e the file in the same directory as the executable.)
    """
    config_files = ordered_config_files()
    config_file_found = False

    for config_file in config_files:
        if config_file and isfile(config_file):
            cfg.read(config_file)
            config_file_found = True

    if not config_file_found:
        cfg.read(ob_repo_config_file())
        
    return cfg


def _set_cfg_options(cfg, options):
    """Allow command line options to override config."""
    auth = ['ssl', 'ssl_cert', 'ssl_key', 'username', 'password']

    for key, value in options.iteritems():
        section = 'CONSTANTS'
        if key in auth:
            section = 'AUTHENTICATION'
        try:
            cfg.set(section, key, value)
        except NoSectionError:
            pass

    return cfg


def _setup_auth_section(cfg):
    """Add section and also add (set) options."""
    section = 'AUTHENTICATION'
    cfg.add_section(section)
    cfg.set(section, 'ssl', False)
    cfg.set(section, 'ssl_cert', None)
    cfg.set(section, 'ssl_key', None)
    cfg.set(section, 'username', None)
    cfg.set(section, 'password', None)

    return cfg


if __name__ == "__main__":
    _parse_command_line()
    from run import run      # daemon relies on Parser() having completed
    run()

