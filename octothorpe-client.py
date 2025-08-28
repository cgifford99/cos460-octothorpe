import argparse
import copy
import logging
import math
import os
import signal
import socket
import sys
import time
from queue import Queue
from threading import Thread

import blessed

CLIENT_NAME = 'cgif-octothorpe-gameclient'
DEFAULT_CLIENT_ROOT_PATH = os.path.split(os.path.abspath(sys.argv[0]))[0]
DEFAULT_SERVER_HOST = 'localhost'
DEFAULT_SERVER_PORT = 8001


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

        operation, msg = resp.split(':')
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


class OctothorpeClientWriter(object):
    def __init__(self, queue, socket):
        self.queue = queue
        self.socket = socket

    def client_writer_handler(self):
        while True:
            if not self.queue.empty():
                event = self.queue.get()
                self.socket.send(event.encode('utf-8'))

            time.sleep(0.1)


class OctothorpeClient(object):
    def __init__(self, socket, root_path):
        self.socket = socket
        self.root_path = root_path

        self.term = blessed.Terminal()
        if not self.term.is_a_tty:
            raise Exception('A terminal is required to use this program')
        self.input_pos = math.floor(self.term.height * 0.6)
        self.scroll_lines = []

        self.user_info = {'username': None, 'position': None, 'score': None}
        self.shortcuts = {'KEY_UP': 'move north', 'KEY_DOWN': 'move south',
                          'KEY_LEFT': 'move west', 'KEY_RIGHT': 'move east'}

        self.map = []
        # map_mask using array of tuple
        # where tuple = (entity_abbr, x, y)
        # and entity_abbr is preferably a single char
        self.map_mask = []
        self.treasure_mask = []

        self.writer_queue = Queue()
        clientwriter = OctothorpeClientWriter(self.writer_queue, self.socket)
        new_clientwriter_thread = Thread(
            target=clientwriter.client_writer_handler)
        new_clientwriter_thread.start()

        serverreader = OctothorpeServerReader(self, self.socket)
        new_serverreader_thread = Thread(
            target=serverreader.server_reader_handler)
        new_serverreader_thread.start()

    def sh_shutdown(self, signum, frame):
        self.socket.close()
        sys.exit()

    def build_map(self):
        # add map and map_mask to build string/ascii map with mask
        temp_map = copy.deepcopy(self.map)
        masks = self.treasure_mask + self.map_mask
        for entity_abbr, x, y in masks:
            temp_map[y] = temp_map[y][:x] + entity_abbr + temp_map[y][x+1:]
        return temp_map

    def client_handler(self):
        print(self.term.clear)
        while True:
            raw_input_buffer = ''
            char = ''
            with self.term.cbreak():
                while True:
                    char = self.term.inkey()
                    if not char:
                        continue
                    if char.name == 'KEY_ENTER':
                        char = '\r\n'
                    elif char.name == 'KEY_BACKSPACE' or char.name == 'KEY_DELETE':
                        if len(raw_input_buffer) > 0:
                            raw_input_buffer = raw_input_buffer[:-1]
                            self.print_to_input_line(raw_input_buffer)
                        continue
                    elif char.name in self.shortcuts:
                        char = self.shortcuts[char.name] + '\r\n'
                    raw_input_buffer += char
                    if raw_input_buffer[-2:] == '\r\n':
                        break
                    self.print_to_input_line(raw_input_buffer)
            self.print_to_input_line('')
            self.writer_queue.put(raw_input_buffer)

    def update_screen(self):
        self.input_pos = math.floor(self.term.height * 0.6)
        username = self.user_info["username"] or 'N/A'
        position = self.user_info["position"] or 'N/A'
        score = self.user_info["score"] or 'N/A'
        with self.term.hidden_cursor():
            print(self.term.home + self.term.clear_eol +
                  f'Username:{username}, Position:{position}, Score:{score}\n')
            if self.map and self.map_mask:
                temp_map = self.build_map()
                num_map_lines = self.input_pos - 1
                upper_map = 0
                lower_map = num_map_lines
                if self.user_info['username']:
                    zone = self.user_info['position'][1] // num_map_lines
                    upper_map = zone * num_map_lines
                    lower_map = num_map_lines + upper_map
                    if lower_map > len(temp_map):
                        lower_map = len(temp_map)
                        upper_map = lower_map - num_map_lines

                scr_line_idx = 0
                for map_line_idx in range(upper_map, lower_map):
                    line = temp_map[map_line_idx]
                    print(self.term.move_xy(0, scr_line_idx + 1) +
                          self.term.clear_eol + line)
                    scr_line_idx += 1

            for line_idx in range(len(self.scroll_lines)):
                line = self.scroll_lines[line_idx]
                print(self.term.move_xy(0, self.input_pos +
                      line_idx) + self.term.clear_eol + line)
        print(self.term.move_xy(0, self.input_pos + len(self.scroll_lines) - 1))

    def print_to_input_line(self, msg):
        print(self.term.move_xy(0, self.input_pos + len(self.scroll_lines)
                                ) + self.term.clear_eol + msg, flush=True, end='')

    def print_to_scrolling(self, msg):
        self.scroll_lines.append(msg)
        if self.input_pos + len(self.scroll_lines) >= self.term.height:
            lines_for_removal = (
                self.input_pos + len(self.scroll_lines)) - self.term.height + 1
            for line_idx in range(lines_for_removal):
                self.scroll_lines.pop(line_idx)

    def update_player_position(self, entity_abbr, x, y):
        entity_idx = -1
        for index, item in enumerate(self.map_mask):
            if item[0] == entity_abbr:
                entity_idx = index
                break
        if entity_idx != -1:
            self.map_mask[entity_idx] = (entity_abbr, x, y)
        else:
            self.map_mask.append((entity_abbr, x, y))

    def update_treasure_position(self, x, y):
        self.treasure_mask.append(('#', x, y))


if __name__ == '__main__':
    logger = logging.getLogger(CLIENT_NAME)
    logger.setLevel(logging.INFO)

    host = 'localhost'

    parser = argparse.ArgumentParser(
        description='A client implementation interfacing with the Octothorpe server')
    parser.add_argument('--port', metavar='p', type=int, help='server port',
                        choices=range(1024, 65535), default=DEFAULT_SERVER_PORT, required=False)
    parser.add_argument('--host', metavar='h', type=str,
                        help='server host', default=DEFAULT_SERVER_HOST, required=False)
    parser.add_argument('--root_path', metavar='r',
                        help='root directory to client resources', default=DEFAULT_CLIENT_ROOT_PATH, required=False)

    args = parser.parse_args()
    port = args.port
    host = args.host
    root_path = args.root_path
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            s.connect((host, port))
        except socket.error as msg:
            logger.error(
                f'Connect failed to server {host} on port {port}: ' + str(msg))
            sys.exit()

        logger.info(f'Successfully connected to server {host} on port {port}')

        octothorpe_client = OctothorpeClient(s, root_path)

        signal.signal(signal.SIGINT, octothorpe_client.sh_shutdown)
        signal.signal(signal.SIGTERM, octothorpe_client.sh_shutdown)
        if hasattr(signal, 'SIGBREAK'):
            signal.signal(signal.SIGBREAK, octothorpe_client.sh_shutdown)

        octothorpe_client.client_handler()
