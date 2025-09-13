import logging
import time

import server.models.serverClientWriterEvent as scwe
import server.models.serverWriterEvent as swe
from common.services.serviceBase import ServiceBase
from common.services.serviceManager import ServiceManager
from constants import POLLING_INTERVAL, SERVER_NAME
from server.services.serverClientManager import ServerClientManager
from server.services.serverClientWriterManager import ServerClientWriterManager
from server.services.serverUserManager import ServerUserManager
from server.services.serverWriterService import ServerWriterService

logger = logging.getLogger(SERVER_NAME)
logger.setLevel(logging.INFO)


class ServerWriter(ServiceBase):
    '''The Server Writer is responsible for listening for any new server-wide events placed into its queue and sends global messages to all currently active clients. For each event, a command is executed and certain tasks are performed for each type of command.
    
    The Server Writer should only be created once on the server and must be initialized on its own thread.

    Each user will get notified of any of the following:
    * Any user collects a treasure
    * Any user moves
    * Any user logs in or quits
    '''
    def __init__(self, service_manager: ServiceManager):
        self.service_manager: ServiceManager = service_manager
        self.user_manager: ServerUserManager = self.service_manager.get_service(ServerUserManager)
        self.server_writer_service: ServerWriterService = self.service_manager.get_service(ServerWriterService)
        self.server_client_writer_manager: ServerClientWriterManager = self.service_manager.get_service(ServerClientWriterManager)
        self.client_manager: ServerClientManager = self.service_manager.get_service(ServerClientManager)

    def server_writer_handler(self) -> None:
        while True:
            if self.server_writer_service.queue.qsize() != 0:
                event = self.server_writer_service.queue.get()
                self.execute_cmd(event)
            else:
                # this allows the server to poll for outgoing messages only every 100ms, but allow the queue of events to be processed instantaneously
                time.sleep(POLLING_INTERVAL)

    def execute_cmd(self, event: swe.ServerWriterEventBase) -> None:
        if isinstance(event, swe.ServerWriterEventLogin):
            user = event.user
            if not user or not user.position:
                return
            for client in self.client_manager.active_clients:
                client_user = self.user_manager.get_user_by_client_id(client.client_id)
                # ensure a message about the user joining the game is not send to the user themselves
                if not client_user or client_user == user:
                    continue
                server_client_writer_service = self.server_client_writer_manager.get_writer_service(client.client_id)
                server_client_writer_service.dispatch_event(
                    scwe.ServerClientWriterEventInfo(f'{user.username}, {user.position[0]}, {user.position[1]}, {user.score}, joined the game')
                )
        elif isinstance(event, swe.ServerWriterEventLogout):
            user = event.user
            if not user:
                return
            for client in self.client_manager.active_clients:
                server_client_writer_service = self.server_client_writer_manager.get_writer_service(client.client_id)
                server_client_writer_service.dispatch_event(
                    scwe.ServerClientWriterEventInfo(f'{user.username}, -1, -1, {user.score}, left the game')
                )
        elif isinstance(event, swe.ServerWriterEventMove):
            user = event.user
            if not user or not user.position:
                return
            for client in self.client_manager.active_clients:
                server_client_writer_service = self.server_client_writer_manager.get_writer_service(client.client_id)
                server_client_writer_service.dispatch_event(
                    scwe.ServerClientWriterEventInfo(f'{user.username}, {user.position[0]}, {user.position[1]}, {user.score}')
                )
        elif isinstance(event, swe.ServerWriterEventTreasureFound):
            user = event.user
            treasure = event.treasure
            if not user:
                return
            for client in self.client_manager.active_clients:
                server_client_writer_service = self.server_client_writer_manager.get_writer_service(client.client_id)
                server_client_writer_service.dispatch_event(
                    scwe.ServerClientWriterEventTreasureInfo(f'{user.username}, {treasure.id}, {treasure.score}')
                )
