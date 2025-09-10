import copy
import logging
import time
from queue import Queue
from socket import socket
from typing import TYPE_CHECKING, cast

from constants import POLLING_INTERVAL, SERVER_NAME

from ..models.game.treasure import Treasure
from .serverClientInterface import OctothorpeServerClientInterface

if TYPE_CHECKING:
    from .serverBase import OctothorpeServer
    from .serverClient import OctothorpeServerClient

logger = logging.getLogger(SERVER_NAME)
logger.setLevel(logging.INFO)


class OctothorpeServerClientWriter(OctothorpeServerClientInterface):
    '''The Server Client Writer is responsible for handling all client-specific events that get placed into its queue. This is also responsible for communicating server-wide events to the Server Writer
    
    This object should be created for each client and must be created on its own thread.
    '''
    def __init__(self, server: 'OctothorpeServer', conn: socket, addr: str, client: 'OctothorpeServerClient'):
        super().__init__(conn, addr)
        self.server = server
        self.valid_events = ['login', 'quit', 'move', 'map', 'cheatmap', 'treasure-found', 'treasure-nearby', 'info', 'treasure-info', 'success', 'user-error', 'server-error']
        self.client = client
        
        self.queue: Queue[tuple[str, object]] = Queue()

    def client_writer_handler(self) -> None:
        while True:
            if self.queue.qsize() != 0:
                event = self.queue.get()
                self.execute_cmd(event)
            else:
                # this allows the server to poll the client only every 100ms, but allow the queue of events to be processed instantaneously
                time.sleep(POLLING_INTERVAL)

    def write_map(self, user_map: list[str]) -> None:
        for map_line in user_map:
            self.send_msg(104, map_line.replace('\n', ''))

    def execute_cmd(self, event: tuple[str, object]) -> bool:
        event_type, argument = event
        if event_type not in self.valid_events:
            logger.error(f'Invalid event for client server writer [{event_type}]')
            return False

        if event_type == 'login':
            user_map = self.server.game_logic.map
            self.send_msg(104, str((len(user_map), len(user_map[0]))))
            self.write_map(user_map)
            for client in self.server.active_clients:
                user = client.user_info
                if not user or not user.position:
                    continue
                self.send_msg(101, f'{user.username}, {user.position[0]}, {user.position[1]}, {user.score}')
            self.server.server_writer.queue.put(('login', self.client.user_info))
        elif event_type == 'quit':
            self.server.server_writer.queue.put(('quit', self.client.user_info))
        elif event_type == 'move':
            self.send_msg(200, 'move ' + str(argument))

            self.server.server_writer.queue.put(('move', self.client.user_info))
        elif event_type == 'map':
            user_map = copy.deepcopy(self.server.game_logic.map)
            if not self.client.user_info or not self.client.user_info:
                raise ValueError('User info was found to be incomplete or missing when sending map updates to client')
            x, y = self.client.user_info.position or (-1, -1)
            user_map[y] = user_map[y][:x] + self.client.user_info.username[0].upper() + user_map[y][x+1:]
            self.write_map(user_map)
        elif event_type == 'cheatmap':
            user_map = copy.deepcopy(self.server.game_logic.map)
            
            for treasure in self.server.game_logic.treasures:
                x, y = treasure.position
                score = str(treasure.score)
                user_map[y] = user_map[y][:x] + score + user_map[y][x+(len(score)):]
            if not self.client.user_info or not self.client.user_info:
                raise ValueError('User info was found to be incomplete or missing when sending map updates to client')
            x, y = self.client.user_info.position or (-1, -1)
            user_map[y] = user_map[y][:x] + self.client.user_info.username[0].upper() + user_map[y][x+1:]
            self.write_map(user_map)
        elif event_type == 'treasure-found':
            self.server.server_writer.queue.put(('treasure', (self.client.user_info, argument)))
        elif event_type == 'treasure-nearby':
            treasure = cast(Treasure, argument)
            self.send_msg(102, f'{treasure.id}, {treasure.position[0]}, {treasure.position[1]}')
        elif event_type == 'info':
            self.send_msg(101, str(argument))
        elif event_type == 'treasure-info':
            self.send_msg(103, str(argument))
        elif event_type == 'success':
            self.send_msg(200, str(argument))
        elif event_type == 'user-error':
            self.send_msg(400, str(argument))
        elif event_type == 'server-error':
            self.send_msg(500, str(argument))

        return True