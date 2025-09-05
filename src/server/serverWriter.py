import time

from constants import SERVER_NAME

import logging
logger = logging.getLogger(SERVER_NAME)
logger.setLevel(logging.INFO)


class OctothorpeServerWriter(object):
    def __init__(self, server, queue):
        self.server = server
        self.queue = queue
        self.valid_events = ['login', 'quit', 'move', 'treasure']

    def server_writer_handler(self):
        while True:
            if self.queue.not_empty:
                event = self.queue.get()
                self.execute_cmd(event)

            time.sleep(0.1)

    def execute_cmd(self, event):
        event_type, argument = event
        if event_type not in self.valid_events:
            logger.error(f'Invalid event from client server [{event_type}]')
            return
        
        if event_type == 'login':
            if not argument:
                return
            for client in self.server.active_clients:
                if client.user_info == argument:
                    continue
                client.send_msg(101, f'{argument.username}, {argument.position[0]}, {argument.position[1]}, {argument.score}, joined the game')
        elif event_type == 'quit':
            if not argument:
                return
            for client in self.server.active_clients:
                client.send_msg(101, f'{argument.username}, -1, -1, {argument.score}, left the game')
        elif event_type == 'move':
            if not argument:
                return
            for client in self.server.active_clients:
                client.send_msg(101, f'{argument.username}, {argument.position[0]}, {argument.position[1]}, {argument.score}')
        elif event_type == 'treasure':
            user = argument[0]
            treasure = argument[1]
            for client in self.server.active_clients:
                client.send_msg(103, f'{user.username}, {treasure["id"]}, {treasure["score"]}')