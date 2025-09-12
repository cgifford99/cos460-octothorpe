import logging
import sys
import threading
import traceback

from common.models.user import OctothorpeUser
from common.services.serviceManager import ServiceManager
from constants import SERVER_NAME
from server.models.serverClient import ServerClient
from server.models.serverExceptions import (ServerInternalException,
                                            UserRequestException)
from server.serverClientGameLogic import OctothorpeServerClientGameLogic
from server.serverClientWriter import OctothorpeServerClientWriter
from server.services.serverClientWriterManager import ServerClientWriterManager
from server.services.serverClientWriterService import ServerClientWriterService
from server.services.serverGameLogicService import ServerGameLogicService
from server.services.serverUserManager import ServerUserManager

logger = logging.getLogger(SERVER_NAME)
logger.setLevel(logging.INFO)

class OctothorpeServerClientReader():
    '''The Server Client is responsible for connecting to and interacting with the client.
    It is the core object that listens for all input from the client.
    '''
    def __init__(self, service_manager: ServiceManager, client_info: ServerClient):
        self.service_manager: ServiceManager = service_manager
        self.user_manager: ServerUserManager = self.service_manager.get_service(ServerUserManager)
        self.server_game_logic: ServerGameLogicService = self.service_manager.get_service(ServerGameLogicService)
        self.server_client_writer_manager: ServerClientWriterManager = self.service_manager.get_service(ServerClientWriterManager)

        self.client_info: ServerClient = client_info      
        self.client_game_logic: OctothorpeServerClientGameLogic | None = None

        self.valid_cmds: list[str] = ['quit', 'login']

        self.client_writer_service: ServerClientWriterService = self.server_client_writer_manager.register_client(self.client_info.client_id)

        client_writer = OctothorpeServerClientWriter(self.service_manager, self.client_info)

        new_client_writer_thread = threading.Thread(target=client_writer.client_writer_handler)
        new_client_writer_thread.start()

    def client_handler(self) -> None:
        try:
            self.client_writer_service.queue.put(('success', 'Please first login using command \'login [username]\''))

            while True:
                if not self.cmd_handler():
                    logger.error(f'Client reader for address \'{self.client_info.addr}\' has stopped')
                    break

        except ConnectionAbortedError:
            logger.error(f'Client unexpectedly disconnected at address {self.client_info.addr}')
        except Exception:
            logger.error(f'Internal Exception: ' + traceback.format_exc())
            self.client_writer_service.queue.put(('server-error', 'We experienced a critical internal error. Please contact chrisgifford99@gmail.com for support.'))
        finally:
            self.logout_handler()
            sys.exit()

    def login_handler(self, command_agg: list[str]) -> OctothorpeUser | None:
        if len(command_agg) != 2:
            self.client_writer_service.queue.put(('user-error', f'Invalid login command. Use format: \'login [username]\''))
            return None
        username: str = command_agg[1]
        try:
            user, new_user = self.user_manager.login_user(self.client_info.client_id, username)
        except UserRequestException as ex:
            self.client_writer_service.queue.put(('user-error', ex))
            return None
        except ServerInternalException as ex:
            self.client_writer_service.queue.put(('server-error', ex))
            return None
    
        if new_user:
            self.client_writer_service.queue.put(('success', f'Welcome new user {username}!'))
        else:
            self.client_writer_service.queue.put(('success', f'Welcome back {username}!'))

        self.client_game_logic = OctothorpeServerClientGameLogic(self.service_manager, self.client_info)
        return user

    def logout_handler(self) -> None:
        self.client_writer_service.queue.put(('quit',None))
        self.user_manager.logout_user(self.client_info.client_id)

    def execute_cmd(self, command_agg: list[str]) -> bool:
        operation: str = command_agg[0]

        user_info = self.user_manager.get_user_by_client_id(self.client_info.client_id)
        if operation == 'login':
            if user_info:
                self.client_writer_service.queue.put(('user-error', f'You\'re already logged in!'))
                return True

            user_info = self.login_handler(command_agg)
            login_success: bool = bool(user_info)
            if login_success:
                self.client_writer_service.queue.put(('login', None))
            return login_success
        elif operation == 'quit':
            self.client_writer_service.queue.put(('success', 'Goodbye. Thanks for playing!'))
            return False
        
        self.client_writer_service.queue.put(('server-error', f'Internal error while processing your request: Operation \'{operation}\' given, but only {self.valid_cmds} are processed here'))
        return False

    def cmd_handler(self) -> bool:
        incoming_data: str = ''
        # build incoming packet from first char input to some '\r\n'
        while True:
            chunk: bytes = self.client_info.conn.recv(1024)
            if not chunk:
                return False

            incoming_data += chunk.decode('utf-8')

            # handle backspace in telnet
            while '\b' in incoming_data:
                self.client_info.conn.send(b' \b') # The single space ' ' replaces char at cursor and '\b' moves cursor to the left within telnet
                bs_idx: int = incoming_data.index('\b')
                incoming_data = incoming_data[:bs_idx - 1] + incoming_data[bs_idx + 1:]

            if '\r\n' in incoming_data:
                break

        if not incoming_data:
            return False
        
        # sometimes, the client will send requests faster than the server can process each request independently. That is, the client will send more than one request before the socket buffer can be ingested and cleared and the server ends up receiving multiple requests at once.
        # therefore, we need to separate those requests to be processed separately
        incoming_requests: list[str] = list(filter(None, incoming_data.split('\r\n'))) # filter out None (aka falsey) values
        data_process_result: bool = True
        for req in incoming_requests:
            command_agg: list[str] = [elem.strip().lower() for elem in req.split(' ')]
            operation: str = command_agg[0]
            
            allowed_operations: list[str] = list(self.valid_cmds) # ensure a new list is created and we aren't referencing
            if self.client_game_logic:
                # exclude 'cheatmap' from being shown to the user since it's a secret cheat command
                allowed_operations += [cmd for cmd in self.client_game_logic.valid_cmds if cmd != 'cheatmap']
            
            if operation in self.valid_cmds:
                # execute basic Server Client commands
                server_client_execute_res: bool = self.execute_cmd(command_agg)
                data_process_result &= (server_client_execute_res or False)
                continue
            elif self.client_game_logic and operation in self.client_game_logic.valid_cmds:
                # execute Game Logic commands
                game_logic_execute_res: bool = self.client_game_logic.execute_cmd(command_agg)
                data_process_result &= (game_logic_execute_res or False)
                continue
            else:
                self.client_writer_service.queue.put(('user-error', f'Invalid operation \'{operation}\'. Allowed operations: [{",".join(allowed_operations)}]'))
                data_process_result &= True
                continue
        
        return data_process_result