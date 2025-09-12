import sys
from socket import socket
from threading import Thread
from types import FrameType
from typing import Any

from client.clientServerReader import ServerReader
from client.clientServerWriter import ClientServerWriter
from client.clientWriter import ClientWriter
from client.services.clientCoreService import ClientCoreService
from client.services.clientMapService import ClientMapService
from client.services.clientServerWriterService import ClientServerWriterService
from client.services.clientWriterService import ClientWriterService
from common.services.serviceManager import ServiceManager


class OctothorpeClient(object):
    '''The Client is responsible for managing all core resources for each client.
    
    The Client is created once on the main thread and does not need a separate thread.
    '''
    def __init__(self, service_manager: ServiceManager, sock: socket):
        self.service_manager: ServiceManager = service_manager
        self.client_map_service = self.service_manager.get_service(ClientMapService)
        self.client_core_service = self.service_manager.get_service(ClientCoreService)
        self.client_writer_service = self.service_manager.get_service(ClientWriterService)
        self.client_server_writer_service = self.service_manager.get_service(ClientServerWriterService)

        self.sock: socket = sock

        self.shortcuts: dict[str, str] = {
            'KEY_UP': 'move north', 'KEY_DOWN': 'move south',
            'KEY_LEFT': 'move west', 'KEY_RIGHT': 'move east'
        }

        client_writer: ClientWriter = ClientWriter(self.service_manager)
        new_client_writer_thread = Thread(
            target=client_writer.client_writer_handler)
        new_client_writer_thread.start()

        client_server_writer = ClientServerWriter(self.service_manager, self.sock)
        new_client_server_writer_thread = Thread(
            target=client_server_writer.client_server_writer_handler)
        new_client_server_writer_thread.start()

        server_reader = ServerReader(self.service_manager, self.sock)
        new_serverreader_thread = Thread(
            target=server_reader.server_reader_handler)
        new_serverreader_thread.start()

    def sh_shutdown(self, signal: int, frame: FrameType | None) -> Any:
        self.sock.close()
        sys.exit()

    def client_handler(self) -> None:
        print(self.client_core_service.term.clear)
        while True:
            raw_input_buffer: str = ''
            char_in: str = ''
            with self.client_core_service.term.cbreak():
                while True:
                    char_in = self.client_core_service.term.inkey()
                    if not char_in:
                        continue
                    if char_in.name == 'KEY_ENTER':
                        char_in = '\r\n'
                    elif char_in.name == 'KEY_BACKSPACE' or char_in.name == 'KEY_DELETE':
                        if len(raw_input_buffer) > 0:
                            raw_input_buffer = raw_input_buffer[:-1]
                            self.client_writer_service.queue.put(('print-input-line', raw_input_buffer))
                        continue
                    elif char_in.name in self.shortcuts:
                        char_in = self.shortcuts[char_in.name] + '\r\n'
                    raw_input_buffer += char_in
                    if raw_input_buffer[-2:] == '\r\n':
                        break
                    self.client_writer_service.queue.put(('print-input-line', raw_input_buffer))
            self.client_writer_service.queue.put(('print-input-line', ''))
            self.client_server_writer_service.queue.put(raw_input_buffer)

