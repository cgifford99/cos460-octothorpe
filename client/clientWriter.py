import time
from queue import Queue
from socket import socket

from constants import POLLING_INTERVAL


class OctothorpeClientWriter(object):
    '''The Client Writer is responsible for sending any events that get placed into its queue to the server.

    The Client Writer is created once for each client and must be initialized on its own thread.
    '''
    def __init__(self, sock: socket):
        self.sock: socket = sock
        
        self.queue: Queue[str] = Queue()

    def client_writer_handler(self) -> None:
        while True:
            if self.queue.qsize() != 0:
                client_cmd = self.queue.get()
                self.sock.send(client_cmd.encode('utf-8'))
            else:
                # this allows the server to poll the client only every 100ms, but allow the queue of events to be processed instantaneously
                time.sleep(POLLING_INTERVAL)