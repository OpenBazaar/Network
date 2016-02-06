__author__ = 'chris'

import argparse
import platform
import requests
import sys
import time

from daemon import OpenBazaard, run


if __name__ == "__main__":
    # pylint: disable=anomalous-backslash-in-string

    class Parser(object):
        def __init__(self, daemon):
            self.daemon = daemon
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
            getattr(self, args.command)()

        def start(self):

            parser = argparse.ArgumentParser(
                description="Start the OpenBazaar server",
                usage="python openbazaard.py start [<args>]"
            )
            parser.add_argument('-d', '--daemon', action='store_true',
                                help="run the server in the background as a daemon")
            parser.add_argument('-t', '--testnet', action='store_true', help="use the test network")
            parser.add_argument('-s', '--ssl', action='store_true',
                                help="use ssl on api connections. you must set the path to your "
                                     "certificate and private key in the config file.")
            parser.add_argument('-l', '--loglevel', default="info",
                                help="set the logging level [debug, info, warning, error, critical]")
            parser.add_argument('-p', '--port', help="set the network port")
            parser.add_argument('-a', '--allowip', default="127.0.0.1",
                                help="only allow api connections from this ip")
            parser.add_argument('-r', '--restapiport', help="set the rest api port", default=18469)
            parser.add_argument('-w', '--websocketport', help="set the websocket api port", default=18466)
            parser.add_argument('--pidfile', help="name of the pid file", default="openbazaard.pid")
            args = parser.parse_args(sys.argv[2:])

            OKBLUE = '\033[94m'
            ENDC = '\033[0m'
            print "________             " + OKBLUE + "         __________" + ENDC
            print "\_____  \ ______   ____   ____" + OKBLUE + \
                  "\______   \_____  _____________  _____ _______" + ENDC
            print " /   |   \\\____ \_/ __ \ /    \\" + OKBLUE +\
                  "|    |  _/\__  \ \___   /\__  \ \__  \\\_  __ \ " + ENDC
            print "/    |    \  |_> >  ___/|   |  \    " + OKBLUE \
                  + "|   \ / __ \_/    /  / __ \_/ __ \|  | \/" + ENDC
            print "\_______  /   __/ \___  >___|  /" + OKBLUE + "______  /(____  /_____ \(____  (____  /__|" + ENDC
            print "        \/|__|        \/     \/  " + OKBLUE + "     \/      \/      \/     \/     \/" + ENDC
            print
            print "OpenBazaar Server v0.1 starting..."

            unix = ("linux", "linux2", "darwin")

            if args.port:
                port = int(args.port)
            else:
                port = 18467 if not args.testnet else 28467
            if args.daemon and platform.system().lower() in unix:
                self.daemon.pidfile = "/tmp/" + args.pidfile
                self.daemon.start(args.testnet, args.loglevel, port, args.allowip, args.ssl,
                                  int(args.restapiport), int(args.websocketport), time.time())
            else:
                run(args.testnet, args.loglevel, port, args.allowip, args.ssl,
                    int(args.restapiport), int(args.websocketport), time.time())

        def stop(self):
            # pylint: disable=W0612
            parser = argparse.ArgumentParser(
                description="Shutdown the server and disconnect",
                usage='''usage:
        python openbazaard.py stop''')
            parser.parse_args(sys.argv[2:])
            print "OpenBazaar server stopping..."
            try:
                requests.get("http://localhost:18469/api/v1/shutdown")
            except Exception:
                self.daemon.stop()

        def restart(self):
            # pylint: disable=W0612
            parser = argparse.ArgumentParser(
                description="Restart the server",
                usage='''usage:
        python openbazaard.py restart''')
            parser.parse_args(sys.argv[2:])
            print "Restarting OpenBazaar server..."
            self.daemon.restart()

    Parser(OpenBazaard('/tmp/openbazaard.pid'))
