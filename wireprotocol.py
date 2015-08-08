__author__ = 'chris'

import collections

from txrudp.rudp import ConnectionMultiplexer
from txrudp.connection import HandlerFactory, Handler
from txrudp.crypto_connection import CryptoConnectionFactory

from protos.message import Message
from log import Logger


class OpenBazaarProtocol(ConnectionMultiplexer):
    def __init__(self, ip_address):
        """
        Initialize the new protocol with the connection handler factory.

        Args:
                ip_address: a `tuple` of the (ip address, port) of ths node.
        """
        self.ip_address = ip_address
        self.processors = set()
        self.factory = self.ConnHandlerFactory(self.processors)
        self._dispatcher = collections.defaultdict(set)
        ConnectionMultiplexer.__init__(self, CryptoConnectionFactory(self.factory), self.ip_address[0])

    class ConnHandler(Handler):

        def __init__(self, protocol):
            self.log = Logger(system=self)
            self._proto = protocol
            self.connection = None

        def receive_message(self, datagram):
            if len(datagram) < 166:
                self.log.warning("received datagram too small from %s, ignoring" % str(self.connection.dest_addr))
                return False
            m = Message()
            try:
                m.ParseFromString(datagram)
                for processor in self._proto.get_processors_for(m.command):
                    processor.receive_message(datagram, self.connection)
                    # NOTE: Maybe we should defer the actual processing via the reactor?
            except:
                # If message isn't formatted property then ignore
                self.log.warning("Received unknown message from %s, ignoring" % str(self.connection.dest_addr))
                return False

        def handle_shutdown(self):
            self.log.info("Connection with (%s, %s) terminated" % (self.connection.dest_addr[0], self.connection.dest_addr[1]))

    class ConnHandlerFactory(HandlerFactory):

        def __init__(self, protocol):
            self.protocol = protocol

        def make_new_handler(self, *args, **kwargs):
            return OpenBazaarProtocol.ConnHandler(self.protocol)

    def register_processor(self, processor):
        """
        Add a new processor.

        Also, populate the inverse index with the commands handled by
        this processor

        Args:
            processor: An interfaces.MessageProcessor
        """
        self.processors.add(processor)
        for command in processor:
            self._dispatcher[command].add(processor)

    def unregister_processor(self, processor):
        """
        Remove the given processor.

        Also, remove the processor from the inverse index.

        Args:
            processor: An interfaces.MessageProcessor
        """
        self.processors.discard(processor)
        for command in processor:
            self._dispatcher[command].discard(processor)

    def get_processors_for(self, command):
        """
        Return registered processors for a given command.

        Args:
            command: str or unicode

        Returns:
            Iterator over qualified processors.
        """
        return self._dispatcher[command]

    def send_message(self, datagram, address):
        """
        Sends a datagram over the wire to the given address. It will create a new rudp connection if one
        does not already exist for this peer.

        Args:
            datagram: the raw data to send over the wire
            address: a `tuple` of (ip address, port) of the recipient.
        """
        if address not in self:
                con = self.make_new_connection((self.ip_address[0], self.ip_address[1]), address)
        else:
                con = self[address]
        con.send_message(datagram)
