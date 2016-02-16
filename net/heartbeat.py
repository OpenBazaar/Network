__author__ = 'chris'

import json
from twisted.internet.protocol import Protocol, Factory, connectionDone
from twisted.internet.task import LoopingCall

from config import ALLOWIP

# pylint: disable=W0232
class HeartbeatProtocol(Protocol):
    """
    Handles new incoming requests coming from a websocket.
    """

    def connectionLost(self, reason=connectionDone):
        self.factory.unregister(self)

    def connectionMade(self):
        self.factory.register(self)

    def dataReceived(self, payload):
        return


class HeartbeatFactory(Factory):

    def __init__(self):
        self.status = "starting up"
        self.protocol = HeartbeatProtocol
        self.clients = []
        LoopingCall(self._heartbeat).start(10, now=True)

    def buildProtocol(self, addr):
        if self.status in ("starting up", "generating GUID") and ALLOWIP != "127.0.0.1":
            return
        if addr.host != ALLOWIP and ALLOWIP != "0.0.0.0":
            return
        return Factory.buildProtocol(self, addr)

    def set_status(self, status):
        self.status = status

    def register(self, client):
        if client not in self.clients:
            self.clients.append(client)
            self._heartbeat()

    def unregister(self, client):
        if client in self.clients:
            self.clients.remove(client)

    def push(self, msg):
        for c in self.clients:
            c.transport.write(msg)

    def _heartbeat(self):
        self.push(json.dumps({
            "status": self.status
        }))
