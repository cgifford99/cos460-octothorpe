import logging
import time
from queue import Queue
from typing import TYPE_CHECKING, cast

from constants import POLLING_INTERVAL, SERVER_NAME

from ..models.game.treasure import Treasure
from ..models.user import OctothorpeUser

if TYPE_CHECKING:
    from .serverBase import OctothorpeServer

logger = logging.getLogger(SERVER_NAME)
logger.setLevel(logging.INFO)


class OctothorpeServerWriter(object):
    '''The Server Writer is responsible for listening for any new server-wide events placed into its queue and sends global messages to all currently active clients. For each event, a command is executed and certain tasks are performed for each type of command.
    
    The Server Writer should only be created once on the server and must be initialized on its own thread.

    Each user will get notified of any of the following:
    * Any user collects a treasure
    * Any user moves
    * Any user logs in or quits
    '''
    def __init__(self, server: 'OctothorpeServer'):
        self.server: 'OctothorpeServer' = server
        self.valid_events: list[str] = ['login', 'quit', 'move', 'treasure']

        self.queue: Queue[tuple[str, object]] = Queue()

    def server_writer_handler(self) -> None:
        while True:
            if self.queue.qsize() != 0:
                event = self.queue.get()
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
            for client in self.server.active_clients:
                if client.user_info == argument:
                    continue
                client.client_writer.queue.put(('info', f'{user.username}, {user.position[0]}, {user.position[1]}, {user.score}, joined the game'))
        elif event_type == 'quit':
            if not argument:
                return
            user = cast(OctothorpeUser, argument)
            for client in self.server.active_clients:
                client.client_writer.queue.put(('info', f'{user.username}, -1, -1, {user.score}, left the game'))
        elif event_type == 'move':
            if not argument:
                return
            user = cast(OctothorpeUser, argument)
            if not user.position:
                return
            for client in self.server.active_clients:
                client.client_writer.queue.put(('info', f'{user.username}, {user.position[0]}, {user.position[1]}, {user.score}'))
        elif event_type == 'treasure':
            treasure_args = cast(tuple[OctothorpeUser, Treasure], argument)
            user: OctothorpeUser = treasure_args[0]
            treasure: Treasure = treasure_args[1]
            for client in self.server.active_clients:
                client.client_writer.queue.put(('treasure-info', f'{user.username}, {treasure.id}, {treasure.score}'))
