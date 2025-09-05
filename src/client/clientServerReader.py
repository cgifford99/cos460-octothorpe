from constants import CLIENT_NAME

import logging
logger = logging.getLogger(CLIENT_NAME)
logger.setLevel(logging.INFO)

class OctothorpeServerReader(object):
    def __init__(self, client, socket):
        self.socket = socket
        self.username = None
        self.client = client
        self.map_buffer = []

    def server_reader_handler(self):
        while True:
            try:
                server_resp = self.socket.recv(2048)
            except Exception as e:
                logger.error(e)
                break
            server_resp = server_resp.decode('utf-8')
            for resp in server_resp.split('\r\n'):
                if not resp:
                    continue
                self.execute_cmd(resp)

    def execute_cmd(self, resp):
        if 'Welcome' in resp and not self.username:
            self.username = resp[resp.rindex(' ')+1:-1]

        operation, msg = resp.split(':', 1) # using maxsplit of 1 to protect against any colons in response message
        if operation == '101':
            username, x, y, score = self.unpack_user_update(msg)
            if self.username and self.username in resp:
                self.client.user_info['username'] = username
                self.client.user_info['position'] = (x, y)
                self.client.user_info['score'] = score
                if self.client.map:
                    self.client.update_player_position(
                        self.client.user_info['username'][0].upper(), x, y)
            else:
                if self.client.map:
                    self.client.update_player_position(
                        username[0].upper(), x, y)
        elif operation == '102':
            t_id, x, y = self.unpack_treasure_update(msg)
            self.client.update_treasure_position(x, y)
        elif operation == '104' and not self.client.map:
            _, msg = resp.split(':')
            if ',' in msg and len(msg.split(',')) == 2:
                x, y = [int(coord.replace('(', '').replace(')', ''))
                        for coord in msg.split(',')]
                self.client.map_dimensions = (x, y)
            else:
                self.map_buffer.append(msg + '\r\n')
                if len(self.map_buffer) >= self.client.map_dimensions[0]:
                    self.client.map = self.map_buffer
                    self.map_buffer = []

        if operation != '104':
            if operation != '101':
                self.client.print_to_scrolling(resp)
            self.client.update_screen()

    def unpack_user_update(self, msg):
        components = msg.split(',')
        if len(components) == 5:
            self.client.print_to_scrolling(f'101:{msg}')
            components.pop(len(components)-1)
        username, x, y, score = components
        x = int(x.strip())
        y = int(y.strip())
        username = username.strip()
        score = score.strip()
        return username, x, y, score

    def unpack_treasure_update(self, msg):
        t_id, x, y = msg.split(',')
        x = int(x.strip())
        y = int(y.strip())
        return t_id, x, y