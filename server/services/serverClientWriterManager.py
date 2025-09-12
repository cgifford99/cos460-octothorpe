from typing import TYPE_CHECKING

from common.services.serviceBase import ServiceBase
from common.services.serviceManager import ServiceManager
from server.services.serverClientWriterService import ServerClientWriterService

if TYPE_CHECKING:
    from server.serverClient import OctothorpeServerClient

class ServerClientWriterManager(ServiceBase):
    def __init__(self, service_manager: ServiceManager) -> None:
        self.service_manager: ServiceManager = service_manager

        self.client_writer_services: dict['OctothorpeServerClient', ServerClientWriterService] = {}

    def register_client(self, client: 'OctothorpeServerClient') -> ServerClientWriterService:
        client_writer_service: ServerClientWriterService = ServerClientWriterService()
        self.client_writer_services[client] = client_writer_service

        return client_writer_service

    def get_writer_service(self, client: 'OctothorpeServerClient') -> ServerClientWriterService:
        if client in self.client_writer_services.keys():
            return self.client_writer_services[client]
        
        raise ValueError('Client Writer Service cannot be found')

