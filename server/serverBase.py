import json
import logging
import os
import socket
import sys
import threading
from socket import socket
from types import FrameType
from typing import Any

from common.models.user import OctothorpeUser
from constants import SERVER_NAME, USER_AUTOSAVE_INTERVAL

from .serverClient import OctothorpeServerClient
from .serverGameLogic import OctothorpeServerGameLogic
from .serverWriter import OctothorpeServerWriter
from .utils.fileUtils import FileUtils

logger = logging.getLogger(SERVER_NAME)
logger.setLevel(logging.INFO)

class OctothorpeServer(object):
    '''The Server is responsible for managing all major resources on the server. It acts as a container for server resources including active and non-active users/clients.

    The Server is created once on the main thread and does not need a separate thread.
    '''
    def __init__(self, root_path: str):
        self.root_path = root_path
        self.userstore_filepath = FileUtils.get_userstore_filepath(self.root_path)
        self.game_logic = OctothorpeServerGameLogic(self.root_path)

        self.users: dict[str, OctothorpeUser] = self.load_users() # persistent users, inactive included.
        self.active_users: list[str] = [] # active, logged-in usernames
        self.active_clients: list[OctothorpeServerClient] = [] # active, connected clients

        self.start_save_timer()

        self.server_writer = OctothorpeServerWriter(self)
        new_serverwriter_thread = threading.Thread(target=self.server_writer.server_writer_handler)
        new_serverwriter_thread.start()

    def load_users(self) -> dict[str, OctothorpeUser]:
        logger.info(f'Using data storage path: {self.userstore_filepath}')

        if not os.path.exists(self.userstore_filepath):
            return {}
        with open(self.userstore_filepath, 'r', encoding='utf-8') as user_f:
            serializable_users: dict[str, Any] = json.load(user_f)
            users: dict[str, OctothorpeUser] = {}
            for user_key in serializable_users:
                serializable_user: dict[str, str] = serializable_users[user_key]
                octo_user = OctothorpeUser(user_key, self.game_logic.spawnpoint)
                octo_user.score = int(serializable_user['score'])
                users[user_key] = octo_user
            return users

    def start_save_timer(self) -> None:
        self.user_data_save()
        threading.Timer(USER_AUTOSAVE_INTERVAL, self.start_save_timer).start()

    def user_data_save(self) -> None:
        logger.info(f'Saving user data')
        with open(self.userstore_filepath, 'w', encoding='utf-8') as user_f:
            serializable_users: dict[str, dict[str, object]] = {}
            for user_key in self.users:
                user: OctothorpeUser = self.users[user_key]
                serializable_user: dict[str, object] = {'score': user.score}
                serializable_users[user.username] = serializable_user
            user_f.seek(0)
            json.dump(serializable_users, user_f)

    def sh_shutdown(self, signal: int, frame: FrameType | None) -> Any:
        for client in self.active_clients:
            client.conn.close()
        self.user_data_save()
        sys.exit()

    def initialize_client(self, conn: socket, addr: str) -> None:
        logger.info(f'Incoming client at addr: {addr}')

        client_main = OctothorpeServerClient(self, conn, addr)
        new_client_thread = threading.Thread(target=client_main.client_handler)
        new_client_thread.start()
        self.active_clients.append(client_main)