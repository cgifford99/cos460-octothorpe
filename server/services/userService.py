import json
import logging
import os
from typing import TYPE_CHECKING, Any

from common.models.user import OctothorpeUser
from common.services.serviceBase import ServiceBase
from common.services.serviceManager import ServiceManager
from constants import SERVER_NAME
from server.services.serverCoreService import ServerCoreService
from server.services.serverGameLogicService import ServerGameLogicService
from server.utils.fileUtils import FileUtils

if TYPE_CHECKING:
    from server.serverClient import OctothorpeServerClient

logger = logging.getLogger(SERVER_NAME)
logger.setLevel(logging.INFO)

class UserManager(ServiceBase):
    def __init__(self, service_manager: ServiceManager):
        self.service_manager = service_manager
        self.server_core_service = service_manager.get_service(ServerCoreService)
        self.server_game_logic: ServerGameLogicService = self.service_manager.get_service(ServerGameLogicService)

        root_path: str = self.server_core_service.root_path
        self.userstore_filepath = FileUtils.get_userstore_filepath(root_path)

        self.users: dict[str, OctothorpeUser] = self.load_users() # persistent users, inactive included.
        self.active_users: list[str] = [] # active, logged-in usernames
        self.active_clients: list['OctothorpeServerClient'] = [] # active, connected clients

    def load_users(self) -> dict[str, OctothorpeUser]:
        logger.info(f'Using data storage path: {self.userstore_filepath}')

        if not os.path.exists(self.userstore_filepath):
            return {}
        with open(self.userstore_filepath, 'r', encoding='utf-8') as user_f:
            serializable_users: dict[str, Any] = json.load(user_f)
            users: dict[str, OctothorpeUser] = {}
            for user_key in serializable_users:
                serializable_user: dict[str, str] = serializable_users[user_key]
                octo_user = OctothorpeUser(user_key, self.server_game_logic.spawnpoint)
                octo_user.score = int(serializable_user['score'])
                users[user_key] = octo_user
            return users
        
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
        
    def initialize_client(self, client: 'OctothorpeServerClient') -> None:
        self.active_clients.append(client)

    def disconnect_all_clients(self) -> bool:
        try:
            for client in self.active_clients:
                client.conn.close()
        except Exception as ex:
            logger.error(f'Failed to close all clients: {ex}')
            return False

        return True