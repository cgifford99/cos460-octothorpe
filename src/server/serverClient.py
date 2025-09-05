import sys
import traceback

from .serverClientGameLogic import OctothorpeServerClientGameLogic
from .serverClientInterface import OctothorpeServerClientInterface

from ..models.user import OctothorpeUser

from constants import SERVER_NAME

import logging
logger = logging.getLogger(SERVER_NAME)
logger.setLevel(logging.INFO)

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
        self.client_game_logic = OctothorpeServerClientGameLogic(self.server, self.conn, self.addr, self.queue, self.server.game_logic, self.user_info)
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