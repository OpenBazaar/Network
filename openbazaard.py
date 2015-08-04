__author__ = 'chris'
import pickle
import stun
import os
import sys
from twisted.internet import reactor
from twisted.python import log, logfile
from twisted.web.server import Site
from guidutils.guid import GUID
from dht.network import Server
from dht.node import Node
from wireprotocol import OpenBazaarProtocol
from constants import DATA_FOLDER
from market import network
from txjsonrpc.netstring import jsonrpc
from restapi import OpenBazaarAPI
from networkcli import RPCCalls

# logging
logFile = logfile.LogFile.fromFullPath(DATA_FOLDER + "debug.log")
log.addObserver(log.FileLogObserver(logFile).emit)
log.startLogging(sys.stdout)

# stun
print "Finding NAT Type.."
response = stun.get_ip_info(stun_host='seed.openbazaar.org', stun_port=3478, source_port=0)
print "%s on %s:%s" % (response[0], response[1], response[2])
ip_address = response[1]
port = response[2]

# key generation
if os.path.isfile(DATA_FOLDER + 'keys.pickle'):
    keys = pickle.load(open(DATA_FOLDER + "keys.pickle", "r"))
    g = keys["guid"]
else:
    print "Generating GUID, stand by..."
    g = GUID()
    keys = {'guid': g}
    pickle.dump(keys, open(DATA_FOLDER + "keys.pickle", "wb"))

protocol = OpenBazaarProtocol((ip_address, port))

# kademlia
node = Node(g.guid, ip_address, port, signed_pubkey=g.signed_pubkey)

if os.path.isfile(DATA_FOLDER + 'cache.pickle'):
    kserver = Server.loadState(DATA_FOLDER + 'cache.pickle', ip_address, port, protocol)
else :
    kserver = Server(node)
    kserver.protocol.connect_multiplexer(protocol)
    kserver.bootstrap(kserver.querySeed("162.213.253.147:8080", "909b4f614ec4fc8c63aab83b91bc620d7a238600bf256472e968fdafce200128"))

kserver.saveStateRegularly(DATA_FOLDER + 'cache.pickle', 10)
protocol.register_processor(kserver.protocol)

# market
mserver = network.Server(kserver, g.signing_key)
mserver.protocol.connect_multiplexer(protocol)
protocol.register_processor(mserver.protocol)

reactor.listenUDP(port, protocol)

# json-rpc server
factory = jsonrpc.RPCFactory(RPCCalls(kserver, mserver, g))
reactor.listenTCP(18465, factory, interface="127.0.0.1")

# REST API endpoint
api = OpenBazaarAPI()
site = Site(api, timeout=None)
reactor.listenTCP(18469, site, interface="127.0.0.1")

reactor.run()