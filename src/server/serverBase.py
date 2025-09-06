import json
import logging
import os
import sys
import threading
from queue import Queue

from constants import SERVER_NAME, USER_AUTOSAVE_INTERVAL

from ..models.user import OctothorpeUser
from ..utils.fileUtils import FileUtils
from .serverClient import OctothorpeServerClient
from .serverClientWriter import OctothorpeServerClientWriter
from .serverGameLogic import OctothorpeServerGameLogic
from .serverWriter import OctothorpeServerWriter

logger = logging.getLogger(SERVER_NAME)
logger.setLevel(logging.INFO)

class OctothorpeServer(object):
    '''The Server is responsible for managing all major resources on the server. It acts as a container for server resources including active and non-active users/clients.

    The Server is created once on the main thread and does not need a separate thread.
    '''
    def __init__(self, root_path):
        self.root_path = root_path
        self.userstore_filepath = FileUtils.get_userstore_filepath(self.root_path)
        self.game_logic = OctothorpeServerGameLogic(self.root_path)

        self.users = self.load_users() # persistent users, inactive included.
        self.active_users = [] # active, logged-in usernames
        self.active_clients = [] # active, connected clients

        self.start_save_timer()

        self.writer_queue = Queue()
        serverwriter = OctothorpeServerWriter(self, self.writer_queue)
        new_serverwriter_thread = threading.Thread(target=serverwriter.server_writer_handler)
        new_serverwriter_thread.start()

    def load_users(self):
        logger.info(f'Using data storage path: {self.userstore_filepath}')

        if not os.path.exists(self.userstore_filepath):
            return {}
        with open(self.userstore_filepath, 'r', encoding='utf-8') as user_f:
            serializable_users = json.load(user_f)
            users = {}
            for user_key in serializable_users:
                serializable_user = serializable_users[user_key]
                octo_user = OctothorpeUser(user_key, self.game_logic.spawnpoint)
                octo_user.score = serializable_user['score']
                users[user_key] = octo_user
            return users

    def start_save_timer(self):
        self.user_data_save()
        threading.Timer(USER_AUTOSAVE_INTERVAL, self.start_save_timer).start()

    def user_data_save(self):
        logger.info(f'Saving user data')
        with open(self.userstore_filepath, 'w', encoding='utf-8') as user_f:
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