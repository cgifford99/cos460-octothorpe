import logging
import time
from typing import cast

from common.models.game.treasure import Treasure
from common.models.user import OctothorpeUser
from common.services.serviceBase import ServiceBase
from common.services.serviceManager import ServiceManager
from constants import POLLING_INTERVAL, SERVER_NAME
from server.services.serverClientWriterManager import ServerClientWriterManager
from server.services.serverWriterService import ServerWriterService
from server.services.userService import UserManager

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
        self.user_manager: UserManager = self.service_manager.get_service(UserManager)
        self.server_writer_service: ServerWriterService = self.service_manager.get_service(ServerWriterService)
        self.server_client_writer_manager: ServerClientWriterManager = self.service_manager.get_service(ServerClientWriterManager)

        self.valid_events: list[str] = ['login', 'quit', 'move', 'treasure']

    def server_writer_handler(self) -> None:
        while True:
            if self.server_writer_service.queue.qsize() != 0:
                event = self.server_writer_service.queue.get()
                self.execute_cmd(event)
            else:
                # this allows the server to poll for outgoing messages only every 100ms, but allow the queue of events to be processed instantaneously
                time.sleep(POLLING_INTERVAL)

    def execute_cmd(self, event: tuple[str, object]) -> None:
        event_type, argument = event
        if event_type not in self.valid_events:
            logger.error(f'Invalid event from client server [{event_type}]')
            return
        
        if event_type == 'login':
            if not argument:
                return
            user = cast(OctothorpeUser, argument)
            if not user.position:
                return
            for client in self.user_manager.active_clients:
                if client.user_info == argument:
                    continue
                server_client_writer_service = self.server_client_writer_manager.get_writer_service(client)
                server_client_writer_service.queue.put(('info', f'{user.username}, {user.position[0]}, {user.position[1]}, {user.score}, joined the game'))
        elif event_type == 'quit':
            if not argument:
                return
            user = cast(OctothorpeUser, argument)
            for client in self.user_manager.active_clients:
                server_client_writer_service = self.server_client_writer_manager.get_writer_service(client)
                server_client_writer_service.queue.put(('info', f'{user.username}, -1, -1, {user.score}, left the game'))
        elif event_type == 'move':
            if not argument:
                return
            user = cast(OctothorpeUser, argument)
            if not user.position:
                return
            for client in self.user_manager.active_clients:
                server_client_writer_service = self.server_client_writer_manager.get_writer_service(client)
                server_client_writer_service.queue.put(('info', f'{user.username}, {user.position[0]}, {user.position[1]}, {user.score}'))
        elif event_type == 'treasure':
            treasure_args = cast(tuple[OctothorpeUser, Treasure], argument)
            user: OctothorpeUser = treasure_args[0]
            treasure: Treasure = treasure_args[1]
            for client in self.user_manager.active_clients:
                server_client_writer_service = self.server_client_writer_manager.get_writer_service(client)
                server_client_writer_service.queue.put(('treasure-info', f'{user.username}, {treasure.id}, {treasure.score}'))
