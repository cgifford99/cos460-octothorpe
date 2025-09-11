import threading
from typing import TYPE_CHECKING

from common.services.serviceBase import ServiceBase
from common.services.serviceManager import ServiceManager
from server.services.serverClientWriterService import ServerClientWriterService

if TYPE_CHECKING:
    from server.serverClient import OctothorpeServerClient
    from server.serverClientWriter import OctothorpeServerClientWriter

class ServerClientWriterManager(ServiceBase):
    def __init__(self, service_manager: ServiceManager) -> None:
        self.service_manager: ServiceManager = service_manager

        self.client_writer_services: dict['OctothorpeServerClient', ServerClientWriterService] = {}
        self.client_writers: dict['OctothorpeServerClient', 'OctothorpeServerClientWriter']

    def register_client(self, client: 'OctothorpeServerClient') -> ServerClientWriterService:
        client_writer_service: ServerClientWriterService = ServerClientWriterService()
        self.client_writer_services[client] = client_writer_service

        client_writer = OctothorpeServerClientWriter(self.service_manager, client.conn, client.addr, client)
        self.client_writers[client] = client_writer

        new_client_writer_thread = threading.Thread(target=client_writer.client_writer_handler)
        new_client_writer_thread.start()

        return client_writer_service

    def get_writer_service(self, client: 'OctothorpeServerClient') -> ServerClientWriterService:
        if client in self.client_writer_services.keys():
            return self.client_writer_services[client]
        
        raise ValueError('Client Writer Service cannot be found')
    
    def get_writer(self, client: 'OctothorpeServerClient') -> 'OctothorpeServerClientWriter':
        if client in self.client_writers.keys():
            return self.client_writers[client]
        
        raise ValueError('Client Writer cannot be found')
