import time


class OctothorpeClientWriter(object):
    def __init__(self, queue, socket):
        self.queue = queue
        self.socket = socket

    def client_writer_handler(self):
        while True:
            if not self.queue.empty():
                event = self.queue.get()
                self.socket.send(event.encode('utf-8'))

            time.sleep(0.1)