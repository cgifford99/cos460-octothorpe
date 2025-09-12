import logging
from socket import socket

from common.services.serviceBase import ServiceBase
from constants import SERVER_NAME
from server.models.serverClient import ServerClient

logger = logging.getLogger(SERVER_NAME)
logger.setLevel(logging.INFO)

class ServerClientManager(ServiceBase):
    def __init__(self) -> None:
        self.active_clients: list[ServerClient] = [] # active, connected clients

    def get_client_by_client_id(self, client_id: str) -> ServerClient | None:
        return next((c for c in self.active_clients if c.client_id == client_id), None)

    def initialize_client(self, conn: socket, addr: str) -> ServerClient:
        new_client = ServerClient(conn, addr)
        self.active_clients.append(new_client)

        return new_client

    def disconnect_client(self, client_id: str) -> None:
        client = self.get_client_by_client_id(client_id)
        if client:
            try:
                client.conn.close()
                logger.info(f'Client has disconnected at addr: {client.addr}')
            except OSError as os_error:
                logger.error(
                    f'Received error while attempting to close client connection for addr: {client.addr}, msg: {str(os_error)}')

            self.active_clients.remove(client)
        else:
            logger.error(f'Active client with client_id \'{client_id}\' attempted uninitialization, but could not be found')

    def disconnect_all_clients(self) -> bool:
        try:
            for client in self.active_clients:
                client.conn.close()
        except Exception as ex:
            logger.error(f'Failed to close all clients: {ex}')
            return False

        return True