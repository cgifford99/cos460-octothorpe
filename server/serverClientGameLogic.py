from typing import TYPE_CHECKING

from common.models.game.direction import Direction
from common.models.game.treasure import Treasure
from common.models.user import OctothorpeUser
from common.services.serviceManager import ServiceManager
from server.services.serverClientWriterManager import ServerClientWriterManager
from server.services.serverClientWriterService import ServerClientWriterService
from server.services.serverGameLogicService import ServerGameLogicService
from server.services.userService import UserManager

if TYPE_CHECKING:
    from server.serverClient import OctothorpeServerClient

class OctothorpeServerClientGameLogic():
    '''The Server Client Game Logic class is responsible for performing game logic functions for a client.
    
    This object gets player commands executed by the Server Client. Then, those commands will place events into the Server Client Writer queue.
    One instance of this object is created for each Server Client and does not need its own thread.
    '''
    def __init__(self, service_manager: ServiceManager, user: OctothorpeUser, client: 'OctothorpeServerClient'):
        self.service_manager: ServiceManager = service_manager
        self.user_manager: UserManager = self.service_manager.get_service(UserManager)
        self.server_game_logic: ServerGameLogicService = self.service_manager.get_service(ServerGameLogicService)
        self.server_client_writer_manager: ServerClientWriterManager = self.service_manager.get_service(ServerClientWriterManager)

        self.server_client_writer_service: ServerClientWriterService = self.server_client_writer_manager.get_writer_service(client)

        self.user_info: OctothorpeUser = user

        self.valid_cmds: list[str] = ['move', 'map', 'cheatmap']

    def execute_cmd(self, command_agg: list[str]) -> bool:
        operation: str = command_agg[0]
        if operation == 'move':
            return self.move(command_agg)
        elif operation == 'map':
            self.server_client_writer_service.queue.put(('map', None))
            return True
        elif operation == 'cheatmap':
            self.server_client_writer_service.queue.put(('cheatmap', None))
            return True
        
        self.server_client_writer_service.queue.put(('server-error', f'Internal error while processing your request: Operation \'{operation}\' given, but only {self.valid_cmds} are processed here'))
        return False
    
    def move(self, command_agg: list[str]) -> bool:
        if len(command_agg) != 2:
            self.server_client_writer_service.queue.put(('user-error', f'Invalid move command. Use format: \'move [direction]\''))
            return True
        
        raw_direction = command_agg[1]
        try:
            direction: Direction = Direction[raw_direction]
        except KeyError:
            self.server_client_writer_service.queue.put(('user-error', f'invalid direction \'{raw_direction}\''))
            return True

        new_pos: tuple[int, int] = self.user_info.position or (-1, -1)
        if direction == Direction.NORTH:
            new_pos = (new_pos[0], new_pos[1] - 1)
        elif direction == Direction.SOUTH:
            new_pos = (new_pos[0], new_pos[1] + 1)
        elif direction == Direction.WEST:
            new_pos = (new_pos[0] - 1, new_pos[1])
        elif direction == Direction.EAST:
            new_pos = (new_pos[0] + 1, new_pos[1])
            
        if self.server_game_logic.map[new_pos[1]][new_pos[0]] in [' ', 'S']:
            self.user_info.position = new_pos
            nearby_treasures: list[tuple[Treasure, float]] = self.server_game_logic.nearby_treasures(self.user_info.position)
            for treasure, dist in nearby_treasures:
                if dist == 0:
                    self.server_client_writer_service.queue.put(('treasure-found', treasure))
                    self.user_info.score += treasure.score
                else:
                    self.server_client_writer_service.queue.put(('treasure-nearby', treasure))
            self.server_client_writer_service.queue.put(('move', direction))
        else:
            # user cannot navigate in their desired direction due to a barrier
            self.server_client_writer_service.queue.put(('user-error', f'move {direction} unsuccessful'))

        return True