__author__ = 'chris'

import argparse
import json
import platform
import socket
import stun
import sys
import time
import urllib2
from obelisk.client import LibbitcoinClient
from protos.objects import FULL_CONE, RESTRICTED, SYMMETRIC
from twisted.internet import reactor, task
from twisted.python import log, logfile
from txws import WebSocketFactory
from os.path import join

from api.ws import WSFactory, AuthenticatedWebSocketProtocol, AuthenticatedWebSocketFactory
from api.restapi import RestAPI
from config import DATA_FOLDER, KSIZE, ALPHA, LIBBITCOIN_SERVER,\
    LIBBITCOIN_SERVER_TESTNET, SSL_KEY, SSL_CERT, SEEDS, SSL,\
    TESTNET, LOGLEVEL, PORT, ALLOWIP, WSPORT, HEARTBEATPORT,\
    RESTPORT
from daemon import Daemon
from db.datastore import Database
from dht.network import Server as KServer
from market.network import Server as MServer
from dht.node import Node
from dht.storage import PersistentStorage, ForgetfulStorage
from keys.credentials import get_credentials
from keys.keychain import KeyChain
from log import Logger, FileLogObserver
from market.listeners import MessageListenerImpl, BroadcastListenerImpl, NotificationListenerImpl
from market.contracts import check_unfunded_for_payment
from market.profile import Profile
from net.heartbeat import HeartbeatFactory
from net.sslcontext import ChainedOpenSSLContextFactory
from net.upnp import PortMapper
from net.utils import looping_retry, IP_Port
from net.wireprotocol import OpenBazaarProtocol

LOG_FILE = 'debug.log'
LOGGER_INITIALISED = False

def run():
    logger = _get_logger()
 
    _initialise_database()
    logger.info('initialised database: %s' % Database.get_database_path())
    
    _initialise_heartbeat_server()
    logger.info('initialised heartbeat server')

    KeyChain(_start_server)     # uses threads so we need a callback function

    reactor.run()


def _initialise_database():
    Database()


def _initialise_heartbeat_server():
    heartbeat_server = HeartbeatFactory()
    interface = _get_interface()
    ws_factory = WebSocketFactory(heartbeat_server)

    _connect_reactor(ws_factory)


def _start_server(keys, first_startup=False):
    start_time = time.time()
    logger = _get_logger()

    ip_address, nat_type = _initialise_nat_traversal()

    protocol =  OpenBazaarProtocol(ip_address, nat_type)

    # kademlia
    storage = _get_storage()
    relay_node = _initialise_relay(nat_type)
    protocol.relay_node = relay_node

    cache = join(DATA_FOLDER + 'cache.pickle')

    def on_bootstrap_complete(resp):
        logger.info("bootstrap complete")
        mserver.get_messages(mlistener)
        task.LoopingCall(check_unfunded_for_payment,
                         libbitcoin_client, nlistener).start(600)

    kserver = _initialise_kserver(keys, cache, ip_address, nat_type, relay_node,
                                  on_bootstrap_complete, storage)
    _connect_multiplexer_and_register_processor(protocol, kserver)
    mserver = MServer(kserver, keys.signing_key)
    _connect_multiplexer_and_register_processor(protocol, mserver)
    
    looping_retry(reactor.listenUDP, PORT, protocol)

    _initialise_rest_and_ws_api(mserver, kserver, protocol)
    ws_api = WSFactory(mserver, kserver)
    libbitcoin_client = _initialise_libbitcoin_client()
    protocol.set_servers(ws_api, libbitcoin_client)
    
    listeners = _initialise_listeners(ws_api)
    blistener, mlistener, nlistener = listeners # needed for closure
    for listener in listeners:
        mserver.protocol.add_listener(listener)

    if first_startup:
        _bring_heartbeat_server_online(first_startup)
    
    logger.info("Startup took %s seconds" % str(round(time.time() - start_time, 2)))


def _get_interface():
    interface = "0.0.0.0" if ALLOWIP not in ("127.0.0.1", "0.0.0.0") else ALLOWIP    
    return interface


def _connect_reactor(factory):
    interface = _get_interface()
    if SSL:
        reactor.listenSSL(RESTPORT, factory,
                          ChainedOpenSSLContextFactory(SSL_KEY, SSL_CERT),
                          interface=interface)
    else:
        reactor.listenTCP(RESTPORT, factory, interface=interface)


def _get_logger():
    if not LOGGER_INITIALISED:
        _initialise_logger()

    return Logger(system="OpenBazaard")


def _initialise_nat_traversal():
    logger = _get_logger()
    p = PortMapper()
    p.add_port_mapping(PORT, PORT, "UDP")

    logger.info("Finding NAT Type...")
    response = looping_retry(stun.get_ip_info, "0.0.0.0", PORT)
    logger.info("%s on %s:%s" % (response[0], response[1], response[2]))

    nat_response = response[0]
    ip = response[1]
    port = response[2]
    
    if nat_response == "Full Cone":
        nat_type = FULL_CONE
    elif nat_response == "Restric NAT":
        nat_type = RESTRICTED
    else:
        nat_type = SYMMETRIC

    return ((ip, port), nat_type)


def _get_storage():
    """Get DHT storage object."""
    if TESTNET:
        return ForgetfulStorage()

    db_path = Database.get_database_path()
    return PersistentStorage(db_path)


def _initialise_relay(nat_type):
    relay_node = None
    if nat_type != FULL_CONE:
        for seed in SEEDS:
            try:
                relay_node = (socket.gethostbyname(seed[0].split(":")[0]), PORT)
                break
            except socket.gaierror:
                pass

    return relay_node


def _initialise_kserver(keys, cache, ip_address, nat_type, relay_node,
                                  callback, storage):
    """
    Args:
      ip_address: (ip, port)
    """
    ip = ip_address[0]
    port = ip_address[1]
    try:
        kserver = KServer.loadState(cache, ip, port, nat_type,
                                   relay_node, on_bootstrap_complete, storage)
    except Exception:
        node = Node(keys.guid, ip, port, keys.verify_key.encode(),
                    relay_node, nat_type, Profile().get().vendor)
        kserver = KServer(node, keys.signing_key, KSIZE, ALPHA, storage=storage)
        kserver.bootstrap(kserver.querySeed(SEEDS)).addCallback(on_bootstrap_complete)


    kserver.saveStateRegularly(cache, 10)


def _connect_multiplexer_and_register_processor(protocol, server):
    server.protocol.connect_multiplexer(protocol)
    protocol.register_processor(server.protocol)


def _initialise_rest_and_ws_api(mserver, kserver, protocol):
    authenticated_sessions = _initialise_ws(mserver, kserver)

    rest_api = RestAPI(mserver, kserver, protocol, authenticated_sessions)

    interface = _get_interface()
    _connect_reactor(rest_api)


def _initialise_libbitcoin_client():
    logger = Logger(service="LibbitcoinClient")

    if TESTNET:
        lbc_server = LIBBITCOIN_SERVER_TESTNET
    else:
        lbc_server = LIBBITCOIN_SERVER

    return LibbitcoinClient(lbc_server, log=logger)


def _initialise_listeners(ws_api):
    nlistener = NotificationListenerImpl(ws_api)
    mlistener = MessageListenerImpl(ws_api)
    blistener = BroadcastListenerImpl(ws_api)

    return (blistener, mlistener, nlisterner)


def _bring_heartbeat_server_online():
    heartbeat_server = HeartbeatServer()
    username, password = get_credentials()
    heartbeat_server.push(json.dumps({
        "status": "GUID generation complete",
        "username": username,
        "password": password
    }))

    heartbeat_server.set_status("online")


def _initialise_logger():
    global LOGGER_INITIALISED

    log_file = join(DATA_FOLDER, LOG_FILE)
    _add_log_observer_to_file(log_file)
    _add_log_observer_to_stdout()

    logger = Logger(system="OpenBazaard")
    logger.info('initialised logger: %s' % log_file)
    
    LOGGER_INITIALISED = True


def _initialise_ws(mserver, kserver):
    interface = _get_interface()
    authenticated_sessions = []
    ws_api = WSFactory(mserver, kserver)
    ws_factory = AuthenticatedWebSocketFactory(ws_api)
    ws_factory.authenticated_sessions = authenticated_sessions
    ws_factory.protocol = AuthenticatedWebSocketProtocol

    _connect_reactor(ws_factory)

    return authenticated_sessions


def _add_log_observer_to_file(log_file):
    log.addObserver(FileLogObserver(log_file, level=LOGLEVEL).emit)


def _add_log_observer_to_stdout():
    log.addObserver(FileLogObserver(level=LOGLEVEL).emit)


if __name__ == "__main__":
    # pylint: disable=anomalous-backslash-in-string
    class OpenBazaard(Daemon):
        def run(self, *args):
            run(*args)

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

            if args.daemon and platform.system().lower() in unix:
                self.daemon.pidfile = "/tmp/" + args.pidfile
                self.daemon.start()
            else:
                run()

        def stop(self):
            # pylint: disable=W0612
            parser = argparse.ArgumentParser(
                description="Shutdown the server and disconnect",
                usage='''usage:
        python openbazaard.py stop''')
            parser.add_argument('-r', '--restapiport', help="set the rest api port to shutdown cleanly",
                                default=18469)
            args = parser.parse_args(sys.argv[2:])
            print "OpenBazaar server stopping..."
            try:
                request = urllib2.build_opener()
                request.open('http://localhost:' + args.restapiport + '/api/v1/shutdown')
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
