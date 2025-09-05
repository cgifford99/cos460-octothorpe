import copy
import time

from .serverClientInterface import OctothorpeServerClientInterface

from constants import SERVER_NAME

import logging
logger = logging.getLogger(SERVER_NAME)
logger.setLevel(logging.INFO)


class OctothorpeServerClientWriter(OctothorpeServerClientInterface):
    def __init__(self, server, conn, addr, queue, client):
        super().__init__(conn, addr)
        self.server = server
        self.queue = queue
        self.valid_events = ['login', 'quit', 'move', 'map', 'cheatmap', 'treasure-found', 'treasure-nearby']
        self.client = client

    def client_writer_handler(self):
        while True:
            if not self.queue.empty():
                event = self.queue.get()
                self.execute_cmd(event)

            time.sleep(0.1)

    def write_map(self, user_map):
        for map_line in user_map:
            self.send_msg(104, map_line.replace('\n', ''))

    def execute_cmd(self, event):
        event_type, argument = event
        if event_type not in self.valid_events:
            logger.error(f'Invalid event from client server [{event_type}]')
            return False

        if event_type == 'login':
            user_map = self.server.game_logic.map
            self.send_msg(104, str((len(user_map), len(user_map[0]))))
            self.write_map(user_map)
            for client in self.server.active_clients:
                if not client.user_info:
                    continue
                user = client.user_info
                self.send_msg(101, f'{user.username}, {user.position[0]}, {user.position[1]}, {user.score}')
            self.server.writer_queue.put(('login', self.client.user_info))
        elif event_type == 'quit':
            self.server.writer_queue.put(('quit', self.client.user_info))
        elif event_type == 'move':
            self.server.writer_queue.put(('move', self.client.user_info))
        elif event_type == 'map':
            user_map = copy.deepcopy(self.server.game_logic.map)
            x, y = self.client.user_info.position
            user_map[y] = user_map[y][:x] + self.client.user_info.username[0].upper() + user_map[y][x+1:]
            self.write_map(user_map)
        elif event_type == 'cheatmap':
            user_map = copy.deepcopy(self.server.game_logic.map)
            
            for treasure in self.server.game_logic.treasures:
                x, y = treasure['position']
                score = str(treasure['score'])
                user_map[y] = user_map[y][:x] + score + user_map[y][x+(len(score)):]
            x, y = self.client.user_info.position
            user_map[y] = user_map[y][:x] + self.client.user_info.username[0].upper() + user_map[y][x+1:]
            self.write_map(user_map)
        elif event_type == 'treasure-found':
            self.server.writer_queue.put(('treasure', (self.client.user_info, argument)))
        elif event_type == 'treasure-nearby':
            self.send_msg(102, f'{argument["id"]}, {argument["position"][0]}, {argument["position"][1]}')