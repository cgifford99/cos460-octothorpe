from common.services.serviceBase import ServiceBase
from common.services.serviceManager import ServiceManager
from server.services.serverClientWriterService import ServerClientWriterService


class ServerClientWriterManager(ServiceBase):
    def __init__(self, service_manager: ServiceManager) -> None:
        self.service_manager: ServiceManager = service_manager

        self.client_writer_services: dict[str, ServerClientWriterService] = {}

    def register_client(self, client_id: str) -> ServerClientWriterService:
        client_writer_service: ServerClientWriterService = ServerClientWriterService()
        self.client_writer_services[client_id] = client_writer_service

        return client_writer_service

    def get_writer_service(self, client_id: str) -> ServerClientWriterService:
        if client_id in self.client_writer_services.keys():
            return self.client_writer_services[client_id]
        
        raise ValueError(f'Client Writer Service cannot be found for client id {client_id}')


