import logging
import time
from queue import Queue

from constants import POLLING_INTERVAL, SERVER_NAME

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
    def __init__(self, server):
        self.server = server
        self.valid_events = ['login', 'quit', 'move', 'treasure']

        self.queue = Queue()

    def server_writer_handler(self):
        while True:
            if self.queue.not_empty:
                event = self.queue.get()
                self.execute_cmd(event)
            else:
                # this allows the server to poll for outgoing messages only every 100ms, but allow the queue of events to be processed instantaneously
                time.sleep(POLLING_INTERVAL)

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