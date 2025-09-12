import json
import logging
import os
import uuid
from typing import Any

from common.models.user import OctothorpeUser
from common.services.serviceBase import ServiceBase
from common.services.serviceManager import ServiceManager
from constants import SERVER_NAME
from server.models.serverExceptions import UserRequestException
from server.services.serverClientManager import ServerClientManager
from server.services.serverCoreService import ServerCoreService
from server.services.serverGameLogicService import ServerGameLogicService
from server.utils.fileUtils import FileUtils

logger = logging.getLogger(SERVER_NAME)
logger.setLevel(logging.INFO)

class ServerUserManager(ServiceBase):
    def __init__(self, service_manager: ServiceManager):
        self.service_manager = service_manager
        self.server_core_service = service_manager.get_service(ServerCoreService)
        self.server_game_logic: ServerGameLogicService = self.service_manager.get_service(ServerGameLogicService)
        self.client_manager: ServerClientManager = self.service_manager.get_service(ServerClientManager)

        root_path: str = self.server_core_service.root_path
        self.userstore_filepath = FileUtils.get_userstore_filepath(root_path)

        self.users: dict[str, OctothorpeUser] = self.load_users() # persistent users, inactive included.
        self.active_users: dict[str, str] = {} # active, logged-in users (key: client_id, val: user_id)

    def load_users(self) -> dict[str, OctothorpeUser]:
        logger.info(f'Using data storage path: {self.userstore_filepath}')

        if not os.path.exists(self.userstore_filepath):
            return {}
        with open(self.userstore_filepath, 'r', encoding='utf-8') as user_f:
            serializable_users: dict[str, Any] = json.load(user_f)
            users: dict[str, OctothorpeUser] = {}
            for user_id in serializable_users:
                serializable_user: dict[str, str] = serializable_users[user_id]
                username = str(serializable_user['username'])
                score = int(serializable_user['score'])
                octo_user = OctothorpeUser(user_id, username, self.server_game_logic.spawnpoint, score)
                users[user_id] = octo_user
            return users
        
    def user_data_save(self) -> None:
        logger.info(f'Saving user data')
        with open(self.userstore_filepath, 'w', encoding='utf-8') as user_f:
            serializable_users: dict[str, dict[str, object]] = {}
            for user_id in self.users:
                user: OctothorpeUser = self.users[user_id]
                serializable_user: dict[str, object] = {
                    'username': user.username,
                    'score': user.score
                }
                serializable_users[user.user_id] = serializable_user
            user_f.seek(0)
            json.dump(serializable_users, user_f)

    def get_user_by_client_id(self, client_id: str) -> OctothorpeUser | None:
        if client_id in self.active_users.keys():
            active_client_user_id = self.active_users[client_id]
            return self.users[active_client_user_id]
        else:
            return None

    def get_user_by_username(self, username: str) -> OctothorpeUser | None:
        return next((u for u in self.users.values() if u.username == username), None)

    def register_new_user(self, username: str) -> OctothorpeUser:
        user_id: str = str(uuid.uuid4())
        self.users[user_id] = OctothorpeUser(user_id, username, self.server_game_logic.spawnpoint)

        return self.users[user_id]

    def login_user(self, client_id: str, username: str) -> tuple[OctothorpeUser, bool]:
        if not username:
            raise UserRequestException(f'Invalid username')
        if username in self.active_users.values():
            raise UserRequestException(f'Username [{username}] is already logged in')

        logger.debug(f'Client has logged in as user {username}')

        user: OctothorpeUser | None = self.get_user_by_username(username)
        new_user: bool = bool(not user)
        if not user:
            user = self.register_new_user(username)

        self.active_users[client_id] = user.user_id

        return (user, new_user)
    
    def logout_user(self, client_id: str):
        if client_id in self.active_users.keys():
            self.active_users.pop(client_id)
        self.client_manager.disconnect_client(client_id)
        self.user_data_save()