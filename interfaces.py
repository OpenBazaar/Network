__author__ = 'chris'

import abc
import collections


class MessageProcessor(collections.Iterable):

    """
    This is an interface for processing messages coming off the wire.

    Classes that implement this interface should be passed into
    'OpenBazaarProtocol.register_processor' which will parse new
    messages to determine the message type then route them to the
    correct processor.
    """

    __metaclass__ = abc.ABCMeta

    # The main `ConnectionMultiplexer` protocol.
    # We store it here so we can directly send datagrams from this class.
    multiplexer = None

    # Sequence of commands (strings) that this `MessageProcessor` handles
    commands = None

    @abstractmethod
    def receive_message(self, datagram, connection):
        """
        Called by OpenBazaarProtocol when it receives a new message
        intended for this processor.

        Args:
            datagram: The protobuf that came off the wire in
                unserialized format. Basic validity checks, such as
                minimum size and valid protobuf format have already
                been done.

            connection: The txrudp connection to the peer who sent the
                message. To respond directly to the peer call
                `connection.send_message()`.
        """

    @abstractmethod
    def connect_multiplexer(self, multiplexer):
        """
        Connect the main ConnectionMultiplexer to this class so we can
        send outgoing messages.
        """

    def __iter__(self):
        """Return an iterator over the commands."""
        return iter(self.commands)
