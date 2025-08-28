#!/usr/bin/python
import argparse
import logging
import copy
import math
import os
from queue import Queue
import socket
import sys
import threading
import time
import random
import traceback
import json
import signal

logging.basicConfig()

DEFAULT_PORT = 8001
SERVER_NAME = 'cgif-octothorpe-gameserver'
DEFAULT_SERVER_ROOT_PATH = os.path.split(os.path.abspath(sys.argv[0]))[0]


class OctothorpeServerClientInterface(object):
    def __init__(self, conn, addr):
        self.conn = conn
        self.addr = addr
        self.code_msgs = {101: 'PlayerUpdate', 102:'TreasureProximity', 103: 'TreasureUpdate', 104: 'Map', 200: 'Success', 400: 'UserError', 500: 'ServerError'}

    def send_msg(self, code, msg):
        msg_send_result = bool(self.conn.send(self.resp(code, msg)))
        if not msg_send_result and len(msg) > 0:
            raise ConnectionAbortedError('Received error sending message to client')
        else:
            return True

    def resp(self, code, msg=''):
        if not code or code not in self.code_msgs:
            logger.error('Invalid code given: ' +
                         code if code else 'None')
            code = 500

        code_msg = msg if msg else self.code_msgs.get(code, self.code_msgs.get(500))

        response = f'{code}:{code_msg}\r\n'
        return response.encode('utf-8')

class OctothorpeUser(object):
    def __init__(self, username, spawnpoint):
        self.username = username
        self.score = 0
        self.position = spawnpoint


class OctothorpeClientGameLogic(OctothorpeServerClientInterface):
    def __init__(self, server, conn, addr, queue, game_logic, user):
        super().__init__(conn, addr)
        self.server = server
        self.queue = queue
        self.game_logic = game_logic
        self.user = user

        self.valid_cmds = ['move', 'map', 'cheatmap']

    def execute_cmd(self, command_agg):
        operation = command_agg[0]
        if operation == 'move':
            return self.move(command_agg)
        elif operation == 'map':
            self.queue.put(('map', None))
            return True
        elif operation == 'cheatmap':
            self.queue.put(('cheatmap', None))
            return True
    
    def move(self, command_agg):
        if len(command_agg) != 2:
            return self.send_msg(400, f'Invalid login command. Use format: \'move [direction]\'')
        direction = command_agg[1]
        new_pos = self.user.position
        if direction == 'north':
            new_pos = (new_pos[0], new_pos[1] - 1)
        elif direction == 'south':
            new_pos = (new_pos[0], new_pos[1] + 1)
        elif direction == 'west':
            new_pos = (new_pos[0] - 1, new_pos[1])
        elif direction == 'east':
            new_pos = (new_pos[0] + 1, new_pos[1])
        else:
            return self.send_msg(400, f'invalid direction \'{direction}\'')
        if self.game_logic.map[new_pos[1]][new_pos[0]] in [' ', 'S']:
            self.user.position = new_pos
            nearby_treasures = self.game_logic.nearby_treasures(self.user.position)
            for treasure, dist in nearby_treasures:
                if dist == 0:
                    self.queue.put(('treasure-found', treasure))
                    self.user.score += treasure["score"]
                else:
                    self.queue.put(('treasure-nearby', treasure))
            self.queue.put(('move', None))
        self.send_msg(200, 'move ' + direction)
        return True

class OctothorpeServerClient(OctothorpeServerClientInterface):
    def __init__(self, server, conn, addr, queue):
        super().__init__(conn, addr)
        self.server = server
        self.queue = queue
        self.user_info = None
        self.client_game_logic = None
        self.valid_cmds = ['quit', 'login']

    def client_handler(self):
        try:
            self.send_msg(200, 'Please first login using command \'login [username]\'')

            while True:
                if not self.cmd_handler():
                    break

        except ConnectionAbortedError:
            logger.error(f'Client unexpectedly disconnected at address {self.addr}')
        except Exception:
            logger.error(f'Internal Exception: ' + traceback.format_exc())
            self.send_msg(500, 'We experienced a critical internal error. Please contact christopher.gifford@maine.edu for support.')
        finally:
            self.logout_handler()
            sys.exit()

    def login_handler(self, command_agg):
        if len(command_agg) != 2:
            return self.send_msg(400, f'Invalid login command. Use format: \'login [username]\'')
        username = command_agg[1]
        if not username:
            return self.send_msg(400, f'Invalid username')
        if username in self.server.active_users:
            return self.send_msg(400, f'Username [{username}] is already logged in')

        logger.debug(f'Client at address {self.addr} has logged in as user {username}')
    
        if username not in self.server.users:
            self.server.users[username] = OctothorpeUser(username, self.server.game_logic.spawnpoint)
            self.send_msg(200, f'Welcome new user {username}!')
        else:
            self.send_msg(200, f'Welcome back {username}!')
        self.server.active_users.append(username)
        self.user_info = self.server.users[username]
        self.client_game_logic = OctothorpeClientGameLogic(self.server, self.conn, self.addr, self.queue, self.server.game_logic, self.user_info)
        return True

    def logout_handler(self):
        try:
            self.conn.close()
            logger.info(f'Client has disconnected at addr: {self.addr}')
        except OSError as os_error:
            logger.error(
                f'Received error while attempting to close client connection for addr: {self.addr}, msg: {str(os_error)}')
        finally:
            self.queue.put(('quit',None))
            if self.user_info and self.user_info.username:
                self.server.active_users.remove(self.user_info.username)
            self.server.active_clients.remove(self)
            self.server.user_data_save()

    def execute_cmd(self, command_agg):
        operation = command_agg[0]
        if operation == 'login':
            if self.user_info:
                return self.send_msg(400, f'You\'re already logged in!')

            login_success = self.login_handler(command_agg)
            if self.user_info:
                self.queue.put(('login', None))
            return login_success
        elif operation == 'quit':
            self.send_msg(200, 'Goodbye. Thanks for playing!')
            return False

    def parse_player_cmd(self):
        incoming_data = ''
        # build incoming packet from first char input to some '\r\n\r\n'
        while True:
            chunk = self.conn.recv(1024)
            if not chunk:
                return None

            incoming_data += chunk.decode('utf-8')

            # handling backspace in telnet. 'space' replaces char at cursor and '\b' moves cursor to the left
            while '\b' in incoming_data:
                self.conn.send(b' \b')
                bs_idx = incoming_data.index('\b')
                incoming_data = incoming_data[:bs_idx -
                                              1] + incoming_data[bs_idx + 1:]

            if '\r\n' in incoming_data:
                break
        return incoming_data

    def cmd_handler(self):
        incoming_data = self.parse_player_cmd()
        if incoming_data == None:
            return False
        incoming_data = incoming_data.replace('\r\n', '')

        command_agg = [elem.strip().lower() for elem in incoming_data.split(' ')]
        operation = command_agg[0]
        allowed_operations = [cmd for cmd in self.client_game_logic.valid_cmds if cmd != 'cheatmap'] + self.valid_cmds if self.client_game_logic else self.valid_cmds
        if operation in self.valid_cmds:
            return self.execute_cmd(command_agg)
        elif self.client_game_logic and operation in self.client_game_logic.valid_cmds:
            return self.client_game_logic.execute_cmd(command_agg)
        else:
            return self.send_msg(400, f'Invalid operation \'{operation}\'. Allowed operations: [{",".join(allowed_operations)}]')


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

class OctothorpeServerGameLogic(object):
    MAP_FILENAME = 'map.txt'
    MAP_FILEPATH = os.path.join(os.path.split(os.path.abspath(sys.argv[0]))[0], MAP_FILENAME)
    NUM_TREASURES = 15
    TREASURE_BOUNDARY = 3
    TREASURE_FOW = 5

    def __init__(self):
        self._load_map(self.MAP_FILEPATH)
        self.spawnpoint = (1,1)
        for line_idx in range(len(self.map)):
            if 'S' in self.map[line_idx]:
                sp_pos = self.map[line_idx].index('S')
                self.spawnpoint = (sp_pos, line_idx)

        self.treasures = []
        self._generate_treasures()

    def _load_map(self, filename):
        with open(filename, 'r', encoding='utf-8') as map_f:
            self.map = map_f.readlines()

    def _generate_treasures(self):
        num_treasure = 0
        while num_treasure < self.NUM_TREASURES:
            x = random.randrange(1, len(self.map[0])-1)
            y = random.randrange(1, len(self.map)-1)
            distance_to_nearest_treasure = self.distance_nearest_treasure((x,y))
            if self.map[y][x] == ' ' and (distance_to_nearest_treasure > self.TREASURE_BOUNDARY or distance_to_nearest_treasure == -1):
                self.treasures.append({'id':len(self.treasures), 'position':(x,y), 'score':random.randint(1, 20)})
                num_treasure += 1

    def nearby_treasures(self, position):
        nearby_treasure = []
        for treasure in self.treasures:
            dist = self.distance_to_treasure(treasure, position)
            if dist < self.TREASURE_FOW:
                nearby_treasure.append((treasure, dist))
        return nearby_treasure

    def distance_nearest_treasure(self, position):
        min_distance = -1
        for treasure in self.treasures:
            distance = self.distance_to_treasure(treasure, position)
            if min_distance < 0 or distance < min_distance:
                min_distance = distance
        return min_distance

    def distance_to_treasure(self, treasure, position):
        x0, y0 = position
        x1, y1 = treasure['position']
        return round(math.sqrt((x1-x0)**2+(y1-y0)**2), 2)


class OctothorpeServer(object):
    USER_STORE_FILE = 'users.json'
    USER_STORE_PATH = os.path.join(os.path.split(os.path.abspath(sys.argv[0]))[0], USER_STORE_FILE)

    def __init__(self, root_path):
        self.root_path = root_path
        self.game_logic = OctothorpeServerGameLogic()

        self.users = self.load_users() # persistent users, inactive included.
        self.active_users = [] # active, logged-in usernames
        self.active_clients = [] # active, connected clients

        self.timer_event = threading.Event()
        self.save_timer(self.timer_event)

        self.writer_queue = Queue()
        serverwriter = OctothorpeServerWriter(self, self.writer_queue)
        new_serverwriter_thread = threading.Thread(target=serverwriter.server_writer_handler)
        new_serverwriter_thread.start()

    def load_users(self):
        if not os.path.exists(self.USER_STORE_PATH):
            return {}
        with open(self.USER_STORE_PATH, 'r', encoding='utf-8') as user_f:
            serializable_users = json.load(user_f)
            users = {}
            for user_key in serializable_users:
                serializable_user = serializable_users[user_key]
                octo_user = OctothorpeUser(user_key, self.game_logic.spawnpoint)
                octo_user.score = serializable_user['score']
                users[user_key] = octo_user
            return users

    def save_timer(self, event):
        self.user_data_save()
        if not event.is_set():
            threading.Timer(60, self.save_timer, [event]).start()

    def user_data_save(self):
        logger.info(f'Saving user data')
        with open(self.USER_STORE_PATH, 'w', encoding='utf-8') as user_f:
            serializable_users = {}
            for user_key in self.users:
                user = self.users[user_key]
                serializable_user = {'score': user.score}
                serializable_users[user.username] = serializable_user
            user_f.seek(0)
            json.dump(serializable_users, user_f)

    def sh_shutdown(self, signum, frame):
        for client in self.active_clients:
            client.conn.close()
        self.user_data_save()
        sys.exit()

    def initialize_client(self, conn, addr):
        logger.info(f'Incoming client at addr: {addr}')

        queue = Queue()
        client_main = OctothorpeServerClient(self, conn, addr, queue)
        self.active_clients.append(client_main)
        new_client_thread = threading.Thread(target=client_main.client_handler)
        new_client_thread.start()
        
        client_writer = OctothorpeServerClientWriter(self, conn, addr, queue, client_main)
        new_client_writer_thread = threading.Thread(target=client_writer.client_writer_handler)
        new_client_writer_thread.start()


if __name__ == '__main__':
    logger = logging.getLogger(SERVER_NAME)
    logger.setLevel(logging.INFO)

    host = 'localhost'

    parser = argparse.ArgumentParser(
        description='An implementation of Octothorpe with sockets and a custom protocol')
    parser.add_argument('--port', metavar='p', type=int, help='port to bind server',
                        choices=range(1024, 65535), default=DEFAULT_PORT, required=False)
    parser.add_argument('--root_path', metavar='r',
                        help='root directory to game resources', default=DEFAULT_SERVER_ROOT_PATH, required=False)

    args = parser.parse_args()
    port = args.port
    root_path = args.root_path
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            s.bind((host, port))
        except socket.error as msg:
            logger.error(f'Bind failed on host {host} for port {port}')
            sys.exit()

        logger.info(f'Started {SERVER_NAME} on port {port}')

        octothorpe_server = OctothorpeServer(root_path)

        signal.signal(signal.SIGINT, octothorpe_server.sh_shutdown)
        signal.signal(signal.SIGTERM, octothorpe_server.sh_shutdown)
        if hasattr(signal, 'SIGBREAK'):
            signal.signal(signal.SIGBREAK, octothorpe_server.sh_shutdown)

        s.listen(1)
        while True:
            conn, addr = s.accept()
            octothorpe_server.initialize_client(conn, addr)
