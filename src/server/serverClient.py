import logging
import sys
import threading
import traceback

from constants import SERVER_NAME

from ..models.user import OctothorpeUser
from .serverClientGameLogic import OctothorpeServerClientGameLogic
from .serverClientInterface import OctothorpeServerClientInterface
from .serverClientWriter import OctothorpeServerClientWriter

logger = logging.getLogger(SERVER_NAME)
logger.setLevel(logging.INFO)

class OctothorpeServerClient(OctothorpeServerClientInterface):
    '''The Server Client is responsible for connecting to and interacting with the client.
    It is the core object that listens for all input from the client.
    '''
    def __init__(self, server, conn, addr):
        super().__init__(conn, addr)
        self.server = server
        self.user_info = None
        self.client_game_logic = None
        self.valid_cmds = ['quit', 'login']

        self.client_writer = OctothorpeServerClientWriter(self.server, self.conn, self.addr, self)
        new_client_writer_thread = threading.Thread(target=self.client_writer.client_writer_handler)
        new_client_writer_thread.start()

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
        self.client_game_logic = OctothorpeServerClientGameLogic(self.server, self.conn, self.addr, self.client_writer, self.server.game_logic, self.user_info)
        return True

    def logout_handler(self):
        try:
            self.conn.close()
            logger.info(f'Client has disconnected at addr: {self.addr}')
        except OSError as os_error:
            logger.error(
                f'Received error while attempting to close client connection for addr: {self.addr}, msg: {str(os_error)}')
        finally:
            self.client_writer.queue.put(('quit',None))
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
                self.client_writer.queue.put(('login', None))
            return login_success
        elif operation == 'quit':
            self.send_msg(200, 'Goodbye. Thanks for playing!')
            return False
        
        self.send_msg(500, f'Internal error while processing your request: Operation \'{operation}\' given, but only {self.valid_cmds} are processed here')
        return False

    def cmd_handler(self):
        incoming_data = ''
        # build incoming packet from first char input to some '\r\n'
        while True:
            chunk = self.conn.recv(1024)
            if not chunk:
                return None

            incoming_data += chunk.decode('utf-8')

            # handle backspace in telnet
            while '\b' in incoming_data:
                self.conn.send(b' \b') # The single space ' ' replaces char at cursor and '\b' moves cursor to the left within telnet
                bs_idx = incoming_data.index('\b')
                incoming_data = incoming_data[:bs_idx - 1] + incoming_data[bs_idx + 1:]

            if '\r\n' in incoming_data:
                break

        if incoming_data == None:
            return False
        
        # sometimes, the client will send requests faster than the server can process each request independently. That is, the client will send more than one request before the socket buffer can be ingested and cleared and the server ends up receiving multiple requests at once.
        # therefore, we need to separate those requests to be processed separately
        incoming_requests = list(filter(None, incoming_data.split('\r\n'))) # filter out None (aka falsey) values
        data_process_result = True
        for req in incoming_requests:
            command_agg = [elem.strip().lower() for elem in req.split(' ')]
            operation = command_agg[0]
            
            allowed_operations = list(self.valid_cmds) # ensure a new list is created and we aren't referencing
            if self.client_game_logic:
                # exclude 'cheatmap' from being shown to the user since it's a secret cheat command
                allowed_operations += [cmd for cmd in self.client_game_logic.valid_cmds if cmd != 'cheatmap']
            
            if operation in self.valid_cmds:
                # execute basic Server Client commands
                server_client_execute_res = self.execute_cmd(command_agg)
                data_process_result &= (server_client_execute_res or False)
                continue
            elif self.client_game_logic and operation in self.client_game_logic.valid_cmds:
                # execute Game Logic commands
                game_logic_execute_res = self.client_game_logic.execute_cmd(command_agg)
                data_process_result &= (game_logic_execute_res or False)
                continue
            else:
                invalid_op_res = self.send_msg(400, f'Invalid operation \'{operation}\'. Allowed operations: [{",".join(allowed_operations)}]')
                data_process_result &= (invalid_op_res or False)
                continue
        
        return data_process_result