import logging
import socket
import sys
import threading
from socket import socket
from types import FrameType
from typing import Any

from common.services.serviceManager import ServiceManager
from constants import SERVER_NAME, USER_AUTOSAVE_INTERVAL
from server.serverClientReader import OctothorpeServerClientReader
from server.serverWriter import ServerWriter
from server.services.serverClientManager import ServerClientManager
from server.services.serverCoreService import ServerCoreService
from server.services.serverUserManager import ServerUserManager

logger = logging.getLogger(SERVER_NAME)
logger.setLevel(logging.INFO)

class OctothorpeServer(object):
    '''The Server is responsible for managing all major resources on the server. It acts as a container for server resources including active and non-active users/clients.

    The Server is created once on the main thread and does not need a separate thread.
    '''
    def __init__(self, service_manager: ServiceManager, sock: socket):
        self.service_manager: ServiceManager = service_manager
        self.server_core_service: ServerCoreService = service_manager.get_service(ServerCoreService)
        self.user_manager: ServerUserManager = service_manager.get_service(ServerUserManager)
        self.client_manager: ServerClientManager = self.service_manager.get_service(ServerClientManager)

        self.sock = sock

        self.start_save_timer()

        self.server_writer = ServerWriter(self.service_manager)
        new_serverwriter_thread = threading.Thread(target=self.server_writer.server_writer_handler, daemon=True)
        new_serverwriter_thread.start()

    def start_save_timer(self) -> None:
        self.user_manager.user_data_save()
        threading.Timer(USER_AUTOSAVE_INTERVAL, self.start_save_timer).start()

    def sh_shutdown(self, signal: int, frame: FrameType | None) -> Any:
        self.user_manager.user_data_save()
        self.sock.close()
        logger.info('Socket connection closed. Shutting down server...')
        sys.exit()

    def initialize_client(self, conn: socket, addr: str) -> None:
        logger.info(f'Incoming client at addr: {addr}')

        client_info = self.client_manager.initialize_client(conn, addr)
        client_main = OctothorpeServerClientReader(self.service_manager, client_info)
        new_client_thread = threading.Thread(target=client_main.client_handler)
        new_client_thread.start()