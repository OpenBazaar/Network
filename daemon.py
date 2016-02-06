__author__ = 'chris'
import sys
import os
import time
import atexit
import socket
import stun
from signal import SIGTERM

from obelisk.client import LibbitcoinClient
from protos.objects import FULL_CONE, RESTRICTED, SYMMETRIC
from twisted.internet import reactor, task
from twisted.python import log, logfile
from txws import WebSocketFactory

from api.ws import WSFactory
from api.restapi import RestAPI
from config import DATA_FOLDER, KSIZE, ALPHA, LIBBITCOIN_SERVER,\
    LIBBITCOIN_SERVER_TESTNET, SSL_KEY, SSL_CERT, SEEDS
from db.datastore import Database
from dht.network import Server
from dht.node import Node
from dht.storage import PersistentStorage, ForgetfulStorage
from keys.keychain import KeyChain
from log import Logger, FileLogObserver
from market import network
from market.listeners import MessageListenerImpl, BroadcastListenerImpl, NotificationListenerImpl
from market.contracts import check_unfunded_for_payment
from market.profile import Profile
from net.sslcontext import ChainedOpenSSLContextFactory
from net.upnp import PortMapper
from net.utils import looping_retry
from net.wireprotocol import OpenBazaarProtocol


def run(*args):
    TESTNET = args[0]
    LOGLEVEL = args[1]
    PORT = args[2]
    ALLOWIP = args[3]
    SSL = args[4]
    RESTPORT = args[5]
    WSPORT = args[6]

    # database
    db = Database(TESTNET)

    # key generation
    keys = KeyChain(db)

    # logging
    logFile = logfile.LogFile.fromFullPath(DATA_FOLDER + "debug.log", rotateLength=15000000, maxRotatedFiles=1)
    log.addObserver(FileLogObserver(logFile, level=LOGLEVEL).emit)
    log.addObserver(FileLogObserver(level=LOGLEVEL).emit)
    logger = Logger(system="OpenBazaard")

    # NAT traversal
    p = PortMapper()
    p.add_port_mapping(PORT, PORT, "UDP")
    logger.info("Finding NAT Type...")

    response = looping_retry(stun.get_ip_info, "0.0.0.0", PORT)

    logger.info("%s on %s:%s" % (response[0], response[1], response[2]))
    ip_address = response[1]
    port = response[2]

    if response[0] == "Full Cone":
        nat_type = FULL_CONE
    elif response[0] == "Restric NAT":
        nat_type = RESTRICTED
    else:
        nat_type = SYMMETRIC

    def on_bootstrap_complete(resp):
        logger.info("bootstrap complete")
        mserver.get_messages(mlistener)
        task.LoopingCall(check_unfunded_for_payment, db, libbitcoin_client, nlistener, TESTNET).start(600)

    protocol = OpenBazaarProtocol((ip_address, port), nat_type, testnet=TESTNET,
                                  relaying=True if nat_type == FULL_CONE else False)

    # kademlia
    storage = ForgetfulStorage() if TESTNET else PersistentStorage(db.get_database_path())
    relay_node = None
    if nat_type != FULL_CONE:
        for seed in SEEDS:
            try:
                relay_node = (socket.gethostbyname(seed[0].split(":")[0]),
                              28469 if TESTNET else 18469)
                break
            except socket.gaierror:
                pass

    try:
        kserver = Server.loadState(DATA_FOLDER + 'cache.pickle', ip_address, port, protocol, db,
                                   nat_type, relay_node, on_bootstrap_complete, storage)
    except Exception:
        node = Node(keys.guid, ip_address, port, keys.guid_signed_pubkey,
                    relay_node, nat_type, Profile(db).get().vendor)
        protocol.relay_node = node.relay_node
        kserver = Server(node, db, KSIZE, ALPHA, storage=storage)
        kserver.protocol.connect_multiplexer(protocol)
        kserver.bootstrap(kserver.querySeed(SEEDS)).addCallback(on_bootstrap_complete)
    kserver.saveStateRegularly(DATA_FOLDER + 'cache.pickle', 10)
    protocol.register_processor(kserver.protocol)

    # market
    mserver = network.Server(kserver, keys.signing_key, db)
    mserver.protocol.connect_multiplexer(protocol)
    protocol.register_processor(mserver.protocol)

    looping_retry(reactor.listenUDP, port, protocol)

    interface = "0.0.0.0" if ALLOWIP not in ("127.0.0.1", "0.0.0.0") else ALLOWIP

    # websockets api
    ws_api = WSFactory(mserver, kserver, only_ip=ALLOWIP)
    if SSL:
        reactor.listenSSL(RESTPORT, WebSocketFactory(ws_api),
                          ChainedOpenSSLContextFactory(SSL_KEY, SSL_CERT), interface=interface)
    else:
        reactor.listenTCP(WSPORT, WebSocketFactory(ws_api), interface=interface)

    # rest api
    rest_api = RestAPI(mserver, kserver, protocol, only_ip=ALLOWIP)
    if SSL:
        reactor.listenSSL(RESTPORT, rest_api, ChainedOpenSSLContextFactory(SSL_KEY, SSL_CERT), interface=interface)
    else:
        reactor.listenTCP(RESTPORT, rest_api, interface=interface)

    # blockchain
    if TESTNET:
        libbitcoin_client = LibbitcoinClient(LIBBITCOIN_SERVER_TESTNET, log=Logger(service="LibbitcoinClient"))
    else:
        libbitcoin_client = LibbitcoinClient(LIBBITCOIN_SERVER, log=Logger(service="LibbitcoinClient"))

    # listeners
    nlistener = NotificationListenerImpl(ws_api, db)
    mserver.protocol.add_listener(nlistener)
    mlistener = MessageListenerImpl(ws_api, db)
    mserver.protocol.add_listener(mlistener)
    blistener = BroadcastListenerImpl(ws_api, db)
    mserver.protocol.add_listener(blistener)

    protocol.set_servers(ws_api, libbitcoin_client)

    logger.info("Startup took %s seconds" % str(round(time.time() - args[7], 2)))

    reactor.run()


class Daemon(object):
    """
    A generic daemon class.

    Usage: subclass the Daemon class and override the run() method
    """
    # pylint: disable=file-builtin
    def __init__(self, pidfile, stdin='/dev/null', stdout='/dev/null', stderr='/dev/null'):
        self.stdin = stdin
        self.stdout = stdout
        self.stderr = stderr
        self.pidfile = pidfile

    def daemonize(self):
        """
        do the UNIX double-fork magic, see Stevens' "Advanced
        Programming in the UNIX Environment" for details (ISBN 0201563177)
        http://www.erlenstar.demon.co.uk/unix/faq_2.html#SEC16
        """
        try:
            pid = os.fork()
            if pid > 0:
                # exit first parent
                sys.exit(0)
        except OSError, e:
            sys.stderr.write("fork #1 failed: %d (%s)\n" % (e.errno, e.strerror))
            sys.exit(1)

        # decouple from parent environment
        os.chdir("/")
        os.setsid()
        os.umask(0)

        # do second fork
        try:
            pid = os.fork()
            if pid > 0:
                # exit from second parent
                sys.exit(0)
        except OSError, e:
            sys.stderr.write("fork #2 failed: %d (%s)\n" % (e.errno, e.strerror))
            sys.exit(1)

        # redirect standard file descriptors
        sys.stdout.flush()
        sys.stderr.flush()
        si = file(self.stdin, 'r')
        so = file(self.stdout, 'a+')
        se = file(self.stderr, 'a+', 0)
        os.dup2(si.fileno(), sys.stdin.fileno())
        os.dup2(so.fileno(), sys.stdout.fileno())
        os.dup2(se.fileno(), sys.stderr.fileno())

        # write pidfile
        atexit.register(self.delpid)
        pid = str(os.getpid())
        file(self.pidfile, 'w+').write("%s\n" % pid)

    def delpid(self):
        os.remove(self.pidfile)

    def start(self, *args):
        """
        Start the daemon
        """
        # Check for a pidfile to see if the daemon already runs
        try:
            pf = file(self.pidfile, 'r')
            pid = int(pf.read().strip())
            pf.close()
        except IOError:
            pid = None

        if pid:
            message = "pidfile %s already exist. Daemon already running?\n"
            sys.stderr.write(message % self.pidfile)
            sys.exit(1)

        # Start the daemon
        self.daemonize()
        self.run(*args)

    def stop(self):
        """
        Stop the daemon
        """
        # Get the pid from the pidfile
        try:
            pf = file(self.pidfile, 'r')
            pid = int(pf.read().strip())
            pf.close()
        except IOError:
            pid = None

        if not pid:
            message = "pidfile %s does not exist. Daemon not running?\n"
            sys.stderr.write(message % self.pidfile)
            return # not an error in a restart

        # Try killing the daemon process
        try:
            while 1:
                os.kill(pid, SIGTERM)
                time.sleep(0.1)
        except OSError, err:
            err = str(err)
            if err.find("No such process") > 0:
                if os.path.exists(self.pidfile):
                    os.remove(self.pidfile)
            else:
                print str(err)
                sys.exit(1)

    def restart(self):
        """
        Restart the daemon
        """
        self.stop()
        self.start()

    def run(self, *args):
        """
        You should override this method when you subclass Daemon. It will be called after the process has been
        daemonized by start() or restart().
        """


class OpenBazaard(Daemon):
    def run(self, *args):
        run(*args)
