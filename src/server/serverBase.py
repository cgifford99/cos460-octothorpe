import json
import os
import sys
import threading
from queue import Queue

from .serverClient import OctothorpeServerClient
from .serverClientWriter import OctothorpeServerClientWriter
from .serverGameLogic import OctothorpeServerGameLogic
from .serverWriter import OctothorpeServerWriter

from ..models.user import OctothorpeUser

from constants import SERVER_NAME

import logging
logger = logging.getLogger(SERVER_NAME)
logger.setLevel(logging.INFO)

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