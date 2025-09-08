import logging
from socket import socket

from constants import CLIENT_NAME

from .clientBase import OctothorpeClient

logger = logging.getLogger(CLIENT_NAME)
logger.setLevel(logging.INFO)

class OctothorpeServerReader(object):
    '''The Server Reader is responsible for listening to and processing any incoming responses from the server.

    The Server Reader is created once for each client and must be initialized on its own thread.
    '''
    def __init__(self, client: OctothorpeClient, sock: socket):
        self.client = client
        self.sock: socket = sock
        self.username: str | None = None
        self.map_buffer: list[str] = []

    def server_reader_handler(self) -> None:
        # begin listening for responses from the server
        while True:
            try:
                server_res_raw: bytes = self.sock.recv(2048)
            except Exception as e:
                logger.error(e)
                break
            server_res: str = server_res_raw.decode('utf-8')
            for resp in server_res.split('\r\n'):
                if not resp:
                    continue
                self.execute_cmd(resp)

    def execute_cmd(self, resp: str) -> None:
        if 'Welcome' in resp and not self.username:
            self.username = resp[resp.rindex(' ')+1:-1]

        operation, msg = resp.split(':', 1) # using maxsplit of 1 to protect against any colons in response message
        if operation == '101':
            username, x, y, score = self.unpack_user_update(msg)
            if self.username and self.username in resp:
                self.client.user_info.username = username
                self.client.user_info.position = (x, y)
                self.client.user_info.score = score
                if self.client.map:
                    self.client.update_player_position(
                        self.client.user_info.username[0].upper(), x, y)
            else:
                if self.client.map:
                    self.client.update_player_position(
                        username[0].upper(), x, y)
        elif operation == '102':
            _, x, y = self.unpack_treasure_update(msg)
            self.client.update_treasure_position(x, y)
        elif operation == '104' and not self.client.map:
            _, msg = resp.split(':')
            if ',' in msg and len(msg.split(',')) == 2:
                x, y = [int(coord.replace('(', '').replace(')', ''))
                        for coord in msg.split(',')]
                self.client.map_dimensions = (x, y)
            else:
                if not self.client.map_dimensions:
                    raise ValueError('map_dimenions was None!')

                self.map_buffer.append(msg + '\r\n')
                if len(self.map_buffer) >= self.client.map_dimensions[0]:
                    self.client.map = self.map_buffer
                    self.map_buffer = []

        if operation != '104': # 104 should not update screen
            if operation != '101' or logger.getEffectiveLevel() == logging.DEBUG: # 101 should not appear in the message log on normal execution
                self.client.print_to_scrolling(resp)
            self.client.update_screen()

    def unpack_user_update(self, msg: str) -> tuple[str, int, int, int]:
        '''This unpacks the user update response (code 101). This may be for the current user or others'''
        components: list[str] = msg.split(',')
        if len(components) == 5:
            # If this 101 message has 5 components, then this is declaring that another user has joined the game.
            # Ensure updates for other users that have joined are shown (since we normally hide code 101 in this client)
            # then, remove the 'joined the game' message and continue on.
            self.client.print_to_scrolling(f'101:{msg}')
            components.pop(len(components)-1)
        username, x, y, score = components
        username: str = username.strip()
        x = int(x.strip())
        y = int(y.strip())
        score = int(score.strip())
        return username, x, y, score

    def unpack_treasure_update(self, msg: str) -> tuple[str, int, int]:
        t_id, x, y = msg.split(',')
        x = int(x.strip())
        y = int(y.strip())
        return t_id, x, y