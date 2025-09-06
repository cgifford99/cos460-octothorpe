import time

from ...constants import POLLING_INTERVAL


class OctothorpeClientWriter(object):
    '''The Client Writer is responsible for sending any events that get placed into its queue to the server.

    The Client Writer is created once for each client and must be initialized on its own thread.
    '''
    def __init__(self, queue, socket):
        self.queue = queue
        self.socket = socket

    def client_writer_handler(self):
        while True:
            if not self.queue.empty():
                event = self.queue.get()
                self.socket.send(event.encode('utf-8'))
            else:
                # this allows the server to poll the client only every 100ms, but allow the queue of events to be processed instantaneously
                time.sleep(POLLING_INTERVAL)