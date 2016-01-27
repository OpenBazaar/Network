__author__ = 'chris', 'tobin'
import argparse
import requests
import sys
import os

from constants import RESTAPIPORT
from daemon import Daemon
from platform_agnostic import options_tmp_path

class Parser(object):
    def __init__(self):
        parser = argparse.ArgumentParser(
            description='OpenBazaar-Server v0.1.0',
            usage='''
    python openbazaard.py <command> [<args>]
    python openbazaard.py <command> --help

commands:
    start            start the OpenBazaar server
    stop             shutdown the server and disconnect
    restart          restart the server
''')
        parser.add_argument('command', help='Execute the given command')
        args = parser.parse_args(sys.argv[1:2])
        if not hasattr(self, args.command):
            parser.print_help()
            exit(1)
        self._options = sys.argv[2:]
        getattr(self, args.command)()

    def start(self):

        parser = argparse.ArgumentParser(
            description="Start the OpenBazaar server",
            usage="python openbazaard.py start [<args>]"
            )
        parser.add_argument('-d', '--daemon', action='store_true',
                            help="run the server in the background as a daemon")
        parser.add_argument('-t', '--testnet', action='store_true',
                            help="use the test network")
        parser.add_argument('-s', '--ssl', action='store_true',
                            help="use ssl on api connections. you must set the path to your "
                            "certificate and private key in the config file.")
        parser.add_argument('-l', '--loglevel', default="info",
                            help="set the logging level [debug, info, warning, error, critical]")
        parser.add_argument('-p', '--port', help="set the network port")
        parser.add_argument('-a', '--allowip', default="127.0.0.1",
                            help="only allow api connections from this ip")
        parser.add_argument('-r', '--restapiport', help="set the rest api port")
        parser.add_argument('-w', '--websocketport', help="set the websocket api port")
        parser.add_argument('--pidfile', help="name of the pid file")
        args = parser.parse_args(self._options)

        _write_args_to_file(args)
        _print_splash_screen()
        Daemon().start()

    def stop(self):
        # pylint: disable=W0612
        parser = argparse.ArgumentParser(
            description="Shutdown the server and disconnect",
            usage='''usage:
        python openbazaard.py stop''')
        parser.parse_args(sys.argv[2:])
        print "OpenBazaar server stopping..."
        try:
            request = 'http://localhost:' + RESTAPIPORT + '/api/v1/shutdown'
            requests.get(request)
        except Exception:
            pass
        Daemon().stop()

    def restart(self):
        # pylint: disable=W0612
        parser = argparse.ArgumentParser(
            description="Restart the server",
            usage='''usage:
        python openbazaard.py restart''')

        if len(sys.argv) > 1:
            warning = 'Warning: restart does not accept options'
            warning += ', manually stop then start server instead.'
            print warning
        print "Restarting OpenBazaar server..."
        self.stop()
        self.start()


def _write_args_to_file(args):
    '''
    Write command line options to file.

    File is temporary and in format accepted by ConfigParser
    '''
    path = options_tmp_path()
    if isfile(path):
        os.remove(path)
    f = open(path, 'w')
    print >>f, '[CONSTANTS]'

    for arg in vars(args):
        if getattr(args, arg):
            config_string = arg + ' = ' + str(getattr(args, arg))
            print >>f, config_string

    f.close()


def _print_splash_screen():
    # pylint: disable=anomalous-backslash-in-string
    OKBLUE = '\033[94m'
    ENDC = '\033[0m'
    print "________             " + OKBLUE + "         __________" + ENDC
    print "\_____  \ ______   ____   ____" + OKBLUE + \
        "\______   \_____  _____________  _____ _______" + ENDC
    print " /   |   \\\____ \_/ __ \ /    \\" + OKBLUE +\
        "|    |  _/\__  \ \___   /\__  \ \__  \\\_  __ \ " + ENDC
    print "/    |    \  |_> >  ___/|   |  \    " + OKBLUE \
        + "|   \ / __ \_/    /  / __ \_/ __ \|  | \/" + ENDC
    print "\_______  /   __/ \___  >___|  /" + OKBLUE + \
        "______  /(____  /_____ \(____  (____  /__|" + ENDC
    print "        \/|__|        \/     \/  " + OKBLUE + \
    "     \/      \/      \/     \/     \/" + ENDC
    print
    print "OpenBazaar Server v0.1 starting..."


if __name__ == '__main__':
    Parser()
