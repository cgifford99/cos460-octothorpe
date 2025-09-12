import time
from socket import socket

from client.services.clientServerWriterService import ClientServerWriterService
from common.services.serviceManager import ServiceManager
from constants import POLLING_INTERVAL


class ClientServerWriter(object):
    '''The Client Server Writer is responsible for sending any events that get placed into its queue to the server.

    The Client Server Writer is created once for each client and must be initialized on its own thread.
    '''
    def __init__(self, service_manager: ServiceManager, sock: socket):
        self.service_manager = service_manager
        self.client_server_writer_service = service_manager.get_service(ClientServerWriterService)

        self.sock: socket = sock

    def client_server_writer_handler(self) -> None:
        while True:
            if self.client_server_writer_service.queue.qsize() != 0:
                client_cmd = self.client_server_writer_service.queue.get()
                self.sock.send(client_cmd.encode('utf-8'))
            else:
                # this allows the server to poll the client only every 100ms, but allow the queue of events to be processed instantaneously
                time.sleep(POLLING_INTERVAL)