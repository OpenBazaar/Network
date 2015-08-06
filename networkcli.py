__author__ = 'chris'
import sys
import argparse
import json
import time
from twisted.internet import reactor
from txjsonrpc.netstring.jsonrpc import Proxy
from binascii import hexlify, unhexlify
from dht.utils import digest
from txjsonrpc.netstring import jsonrpc
from market.profile import Profile
from protos import objects, countries
from protos.objects import Value, Node
from db.datastore import HashMap
from market.contracts import Contract
from collections import OrderedDict

def do_continue(value):
    pass


def print_value(value):
    print json.dumps(value, indent=4)
    reactor.stop()


def print_error(error):
    print 'error', error
    reactor.stop()


class Parser(object):
    def __init__(self, proxy):
        parser = argparse.ArgumentParser(
            description='OpenBazaar Network CLI',
            usage='''
    python networkcli.py command [<arguments>]

commands:
    getinfo             returns an object containing various state info
    getpeers            returns the id of all the peers in the routing table
    get                 fetches the given keyword from the dht
    set                 sets the given keyword/key in the dht
    delete              deletes the keyword/key from the dht
    getnode             returns a node's ip address given its guid.
    getcontract         fetchs a contract from a node given its hash and guid
    getcontractmetadata fetches the metadata (including thumbnail image) for the contract
    getimage            fetches an image from a node given its hash and guid
    getprofile          fetches the profile from the given node.
    getusermetadata     fetches the metadata (shortened profile) for the node
    getlistings         fetches metadata about the store's listings
    getmoderators       fetches moderators data from the dht
    setcontract         sets a contract in the filesystem and db
    setimage            maps an image hash to a filepath in the db
    setasmoderator      sets a node as a moderator
    setprofile          sets the given profile data in the database
    shutdown            closes all outstanding connections.
''')
        parser.add_argument('command', help='Execute the given command')
        args = parser.parse_args(sys.argv[1:2])
        if not hasattr(self, args.command):
            parser.print_help()
            exit(1)
        getattr(self, args.command)()
        self.proxy = proxy

    def get(self):
        parser = argparse.ArgumentParser(
            description="Fetch the given keyword from the dht and return all the entries",
            usage='''usage:
    networkcli.py get [-kw KEYWORD]''')
        parser.add_argument('-kw', '--keyword', required=True, help="the keyword to fetch")
        args = parser.parse_args(sys.argv[2:])
        keyword = args.keyword
        d = proxy.callRemote('get', keyword)
        d.addCallbacks(print_value, print_error)
        reactor.run()

    def set(self):
        parser = argparse.ArgumentParser(
            description='Set the given keyword/key pair in the dht. The value will be your '
                        'serialized node information.',
            usage='''usage:
    networkcli.py set [-kw KEYWORD] [-k KEY]''')
        parser.add_argument('-kw', '--keyword', required=True, help="the keyword to set in the dht")
        parser.add_argument('-k', '--key', required=True, help="the key to set at the keyword")
        args = parser.parse_args(sys.argv[2:])
        keyword = args.keyword
        key = args.key
        d = proxy.callRemote('set', keyword, key)
        d.addCallbacks(print_value, print_error)
        reactor.run()

    def delete(self):
        parser = argparse.ArgumentParser(
            description="Deletes the given keyword/key from the dht. Signature will be automatically generated.",
            usage='''usage:
    networkcli.py delete [-kw KEYWORD] [-k KEY]''')
        parser.add_argument('-kw', '--keyword', required=True, help="where to find the key")
        parser.add_argument('-k', '--key', required=True, help="the key to delete")
        args = parser.parse_args(sys.argv[2:])
        keyword = args.keyword
        key = args.key
        d = proxy.callRemote('delete', keyword, key)
        d.addCallbacks(print_value, print_error)
        reactor.run()

    def getinfo(self):
        parser = argparse.ArgumentParser(
            description="Returns an object containing various state info",
            usage='''usage:
    networkcli getinfo''')
        args = parser.parse_args(sys.argv[2:])
        d = proxy.callRemote('getinfo')
        d.addCallbacks(print_value, print_error)
        reactor.run()

    def shutdown(self):
        parser = argparse.ArgumentParser(
            description="Terminates all outstanding connections.",
            usage='''usage:
    networkcli shutdown''')
        args = parser.parse_args(sys.argv[2:])
        d = proxy.callRemote('shutdown')
        d.addCallbacks(print_value, print_error)
        reactor.run()

    def getpubkey(self):
        parser = argparse.ArgumentParser(
            description="Returns this node's public key.",
            usage='''usage:
    networkcli getpubkey''')
        args = parser.parse_args(sys.argv[2:])
        d = proxy.callRemote('getpubkey')
        d.addCallbacks(print_value, print_error)
        reactor.run()

    def getcontract(self):
        parser = argparse.ArgumentParser(
            description="Fetch a contract given its hash and guid.",
            usage='''usage:
    networkcli.py getcontract [-c HASH] [-g GUID]''')
        parser.add_argument('-c', '--hash', required=True, help="the hash of the contract")
        parser.add_argument('-g', '--guid', required=True, help="the guid to query")
        args = parser.parse_args(sys.argv[2:])
        hash = args.hash
        guid = args.guid
        d = proxy.callRemote('getcontract', hash, guid)
        d.addCallbacks(print_value, print_error)
        reactor.run()

    def getimage(self):
        parser = argparse.ArgumentParser(
            description="Fetch an image given its hash and guid.",
            usage='''usage:
    networkcli.py getcontract [-i HASH] [-g GUID]''')
        parser.add_argument('-i', '--hash', required=True, help="the hash of the image")
        parser.add_argument('-g', '--guid', required=True, help="the guid to query")
        args = parser.parse_args(sys.argv[2:])
        hash = args.hash
        guid = args.guid
        d = proxy.callRemote('getimage', hash, guid)
        d.addCallbacks(print_value, print_error)
        reactor.run()

    def getpeers(self):
        parser = argparse.ArgumentParser(
            description="Returns id of all peers in the routing table",
            usage='''usage:
    networkcli getpeers''')
        d = proxy.callRemote('getpeers')
        d.addCallbacks(print_value, print_error)
        reactor.run()

    def getnode(self):
        parser = argparse.ArgumentParser(
            description="Fetch the ip address for a node given its guid.",
            usage='''usage:
    networkcli.py getnode [-g GUID]''')
        parser.add_argument('-g', '--guid', required=True, help="the guid to find")
        args = parser.parse_args(sys.argv[2:])
        guid = args.guid
        d = proxy.callRemote('getnode', guid)
        d.addCallbacks(print_value, print_error)
        reactor.run()

    def setprofile(self):
        parser = argparse.ArgumentParser(
            description="Sets a profile in the database.",
            usage='''usage:
    networkcli.py setprofile [options]''')
        parser.add_argument('-n', '--name', help="the name of the user/store")
        parser.add_argument('-o', '--onename', help="the onename id")
        parser.add_argument('-a', '--avatar', help="the file path to the avatar image")
        parser.add_argument('-hd', '--header', help="the file path to the header image")
        parser.add_argument('-c', '--country', help="a string consisting of country from protos.countries.CountryCode")
        # we could add all the fields here but this is good enough to test.
        args = parser.parse_args(sys.argv[2:])
        p = Profile()
        u = objects.Profile()
        h = HashMap()
        if args.name is not None:
            u.name = args.name
        if args.country is not None:
            u.location = countries.CountryCode.Value(args.country.upper())
        if args.onename is not None:
            u.handle = args.onename
        if args.avatar is not None:
            with open(args.avatar, "r") as file:
                image = file.read()
            hash = digest(image)
            u.avatar_hash = hash
            h.insert(hash, args.avatar)
        if args.header is not None:
            with open(args.header, "r") as file:
                image = file.read()
            hash = digest(image)
            u.header_hash = hash
            h.insert(hash, args.header)
        p.update(u)

    def getprofile(self):
        parser = argparse.ArgumentParser(
            description="Fetch the profile from the given node. Images will be saved in cache.",
            usage='''usage:
    networkcli.py getprofile [-g GUID]''')
        parser.add_argument('-g', '--guid', required=True, help="the guid to query")
        args = parser.parse_args(sys.argv[2:])
        guid = args.guid
        d = proxy.callRemote('getprofile', guid)
        d.addCallbacks(print_value, print_error)
        reactor.run()

    def getusermetadata(self):
        parser = argparse.ArgumentParser(
            description="Fetches the metadata (small profile) from a given node. The images will be saved in cache.",
            usage='''usage:
    networkcli.py getusermetadata [-g GUID]''')
        parser.add_argument('-g', '--guid', required=True, help="the guid to query")
        args = parser.parse_args(sys.argv[2:])
        guid = args.guid
        d = proxy.callRemote('getusermetadata', guid)
        d.addCallbacks(print_value, print_error)
        reactor.run()

    def setcontract(self, ):
        parser = argparse.ArgumentParser(
            description="Sets a new contract in the database and filesystem.",
            usage='''usage:
    networkcli.py setcontract [-f FILEPATH]''')
        parser.add_argument('-f', '--filepath', help="a path to a completed json contract")
        args = parser.parse_args(sys.argv[2:])
        with open(args.filepath) as data_file:
            contract = json.load(data_file, object_pairs_hook=OrderedDict)
        Contract(contract).save()

    def setimage(self, ):
        parser = argparse.ArgumentParser(
            description="Maps a image hash to a file path in the database",
            usage='''usage:
    networkcli.py setimage [-f FILEPATH]''')
        parser.add_argument('-f', '--filepath', help="a path to the image")
        args = parser.parse_args(sys.argv[2:])
        with open(args.filepath, "r") as file:
            image = file.read()
        d = digest(image)
        h = HashMap()
        h.insert(d, args.filepath)
        print h.get_file(d)

    def getlistings(self):
        parser = argparse.ArgumentParser(
            description="Fetches metadata about the store's listings",
            usage='''usage:
    networkcli.py getmetadata [-g GUID]''')
        parser.add_argument('-g', '--guid', required=True, help="the guid to query")
        args = parser.parse_args(sys.argv[2:])
        guid = args.guid
        d = proxy.callRemote('getlistings', guid)
        d.addCallbacks(print_value, print_error)
        reactor.run()

    def getmoderators(self):
        parser = argparse.ArgumentParser(
            description="Fetches moderator data from the dht",
            usage='''usage:
    networkcli.py getmoderators''')
        d = proxy.callRemote('getmoderators')
        d.addCallbacks(print_value, print_error)
        reactor.run()

    def getcontractmetadata(self):
        parser = argparse.ArgumentParser(
            description="Fetches the metadata for the given contract. The thumbnail images will be saved in cache.",
            usage='''usage:
    networkcli.py getcontractmetadata [-g GUID] [-c CONTRACT]''')
        parser.add_argument('-g', '--guid', required=True, help="the guid to query")
        parser.add_argument('-c', '--contract', required=True, help="the contract hash")
        args = parser.parse_args(sys.argv[2:])
        guid = args.guid
        contract = args.contract
        d = proxy.callRemote('getcontractmetadata', guid, contract)
        d.addCallbacks(print_value, print_error)
        reactor.run()

    def setasmoderator(self):
        parser = argparse.ArgumentParser(
            description="Sets the given node as a moderator.",
            usage='''usage:
    networkcli.py setasmoderator [-g GUID]''')
        parser.add_argument('-g', '--guid', required=True, help="the guid to set")
        args = parser.parse_args(sys.argv[2:])
        guid = args.guid
        d = proxy.callRemote('setasmoderator', guid)
        d.addCallbacks(print_value, print_error)
        reactor.run()

# RPC-Server
class RPCCalls(jsonrpc.JSONRPC):
    def __init__(self, kserver, mserver, guid):
        self.kserver = kserver
        self.mserver = mserver
        self.guid = guid

    def jsonrpc_getpubkey(self):
        return hexlify(self.guid.signed_pubkey)

    def jsonrpc_getinfo(self):
        info = {"version": "0.1"}
        num_peers = 0
        for bucket in self.kserver.protocol.router.buckets:
            num_peers += bucket.__len__()
        info["known peers"] = num_peers
        info["stored messages"] = len(self.kserver.storage.data)
        size = sys.getsizeof(self.kserver.storage.data)
        size += sum(map(sys.getsizeof, self.kserver.storage.data.itervalues())) + sum(
            map(sys.getsizeof, self.kserver.storage.data.iterkeys()))
        info["db size"] = size
        return info

    def jsonrpc_set(self, keyword, key):
        def handle_result(result):
            print "JSONRPC result:", result

        d = self.kserver.set(str(keyword), digest(key), self.kserver.node.getProto().SerializeToString())
        d.addCallback(handle_result)
        return "Sending store request..."

    def jsonrpc_get(self, keyword):
        def handle_result(result):
            print "JSONRPC result:", result
            for mod in result:
                try:
                    val = objects.Value()
                    val.ParseFromString(mod)

                    node = objects.Node()
                    node.ParseFromString(val.serializedData)
                    print node
                except Exception as e:
                    print 'malformed protobuf', e.message

        d = self.kserver.get(keyword)
        d.addCallback(handle_result)
        return "Sent get request. Check log output for result"

    def jsonrpc_delete(self, keyword, key):
        def handle_result(result):
            print "JSONRPC result:", result

        signature = self.guid.signing_key.sign(digest(key))
        d = self.kserver.delete(str(keyword), digest(key), signature[:64])
        d.addCallback(handle_result)
        return "Sending delete request..."

    def jsonrpc_shutdown(self):
        for addr in self.kserver.protocol:
            connection = self.kserver.protocol._active_connections.get(addr)
            if connection is not None:
                connection.shutdown()
        return "Closing all connections."

    def jsonrpc_getpeers(self):
        peers = []
        for bucket in self.kserver.protocol.router.buckets:
            for node in bucket.getNodes():
                peers.append(node.id.encode("hex"))
        return peers

    def jsonrpc_getnode(self, guid):
        def print_node(node):
            print node.ip, node.port
        d = self.kserver.resolve(unhexlify(guid))
        d.addCallback(print_node)
        return "finding node..."

    def jsonrpc_getcontract(self, contract_hash, guid):
        def get_node(node):
            def print_resp(resp):
                print resp
            if node is not None:
                d = self.mserver.get_contract(node, unhexlify(contract_hash))
                d.addCallback(print_resp)
        d = self.kserver.resolve(unhexlify(guid))
        d.addCallback(get_node)
        return "getting contract..."

    def jsonrpc_getimage(self, image_hash, guid):
        def get_node(node):
            def print_resp(resp):
                print resp
            if node is not None:
                d = self.mserver.get_image(node, unhexlify(image_hash))
                d.addCallback(print_resp)
        d = self.kserver.resolve(unhexlify(guid))
        d.addCallback(get_node)
        return "getting image..."

    def jsonrpc_getprofile(self, guid):
        start = time.time()

        def get_node(node):
            def print_resp(resp):
                print time.time() - start
                print resp
            if node is not None:
                d = self.mserver.get_profile(node)
                d.addCallback(print_resp)
        d = self.kserver.resolve(unhexlify(guid))
        d.addCallback(get_node)
        return "getting profile..."

    def jsonrpc_getusermetadata(self, guid):
        start = time.time()

        def get_node(node):
            def print_resp(resp):
                print time.time() - start
                print resp
            if node is not None:
                d = self.mserver.get_user_metadata(node)
                d.addCallback(print_resp)
        d = self.kserver.resolve(unhexlify(guid))
        d.addCallback(get_node)
        return "getting user metadata..."

    def jsonrpc_getlistings(self, guid):
        start = time.time()

        def get_node(node):
            def print_resp(resp):
                print time.time() - start
                for l in resp.listing:
                    resp.listing.remove(l)
                    h = l.contract_hash
                    l.contract_hash = hexlify(h)
                    resp.listing.extend([l])
                print resp
            if node is not None:
                d = self.mserver.get_listings(node)
                d.addCallback(print_resp)
        d = self.kserver.resolve(unhexlify(guid))
        d.addCallback(get_node)
        return "getting listing metadata..."

    def jsonrpc_getmoderators(self):
        start = time.time()

        self.mserver.get_moderators()
        return "getting moderators..."

    def jsonrpc_getcontractmetadata(self, guid, contract_hash):
        start = time.time()

        def get_node(node):
            def print_resp(resp):
                print time.time() - start
                print resp
            if node is not None:
                d = self.mserver.get_contract_metadata(node, unhexlify(contract_hash))
                d.addCallback(print_resp)
        d = self.kserver.resolve(unhexlify(guid))
        d.addCallback(get_node)
        return "getting contract metadata..."

    def jsonrpc_setasmoderator(self, node_id):
        def get_node(node):
            proto = node.getProto().SerializeToString()
            if node is not None:
                self.kserver.set("moderators", digest(proto), proto)
        d = self.kserver.resolve(unhexlify(node_id))
        d.addCallback(get_node)

if __name__ == "__main__":
    proxy = Proxy('127.0.0.1', 18465)
    Parser(proxy)