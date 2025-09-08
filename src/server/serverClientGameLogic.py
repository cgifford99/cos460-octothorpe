from ..models.game.treasure import Treasure
from ..models.user import OctothorpeUser
from .serverBase import OctothorpeServer
from .serverClientWriter import OctothorpeServerClientWriter
from .serverGameLogic import OctothorpeServerGameLogic


class OctothorpeServerClientGameLogic():
    '''The Server Client Game Logic class is responsible for performing game logic functions for a client.
    
    This object gets player commands executed by the Server Client. Then, those commands will place events into the Server Client Writer queue.
    One instance of this object is created for each Server Client and does not need its own thread.
    '''
    def __init__(self, server: OctothorpeServer, client_writer: OctothorpeServerClientWriter, game_logic: OctothorpeServerGameLogic, user: OctothorpeUser):
        self.server: OctothorpeServer = server
        self.client_writer: OctothorpeServerClientWriter = client_writer
        self.game_logic: OctothorpeServerGameLogic = game_logic
        self.user: OctothorpeUser = user

        self.valid_cmds: list[str] = ['move', 'map', 'cheatmap']

    def execute_cmd(self, command_agg: list[str]) -> bool:
        operation: str = command_agg[0]
        if operation == 'move':
            return self.move(command_agg)
        elif operation == 'map':
            self.client_writer.queue.put(('map', None))
            return True
        elif operation == 'cheatmap':
            self.client_writer.queue.put(('cheatmap', None))
            return True
        
        self.client_writer.queue.put(('server-error', f'Internal error while processing your request: Operation \'{operation}\' given, but only {self.valid_cmds} are processed here'))
        return False
    
    def move(self, command_agg: list[str]) -> bool:
        if len(command_agg) != 2:
            self.client_writer.queue.put(('user-error', f'Invalid move command. Use format: \'move [direction]\''))
            return True
        direction: str = command_agg[1]
        new_pos: tuple[int, int] = self.user.position or (-1, -1)
        if direction == 'north':
            new_pos = (new_pos[0], new_pos[1] - 1)
        elif direction == 'south':
            new_pos = (new_pos[0], new_pos[1] + 1)
        elif direction == 'west':
            new_pos = (new_pos[0] - 1, new_pos[1])
        elif direction == 'east':
            new_pos = (new_pos[0] + 1, new_pos[1])
        else:
            self.client_writer.queue.put(('user-error', f'invalid direction \'{direction}\''))
            return True
        if self.game_logic.map[new_pos[1]][new_pos[0]] in [' ', 'S']:
            self.user.position = new_pos
            nearby_treasures: list[tuple[Treasure, float]] = self.game_logic.nearby_treasures(self.user.position)
            for treasure, dist in nearby_treasures:
                if dist == 0:
                    self.client_writer.queue.put(('treasure-found', treasure))
                    self.user.score += treasure.score
                else:
                    self.client_writer.queue.put(('treasure-nearby', treasure))
            self.client_writer.queue.put(('move', direction))
        else:
            # user cannot navigate in their desired direction due to a barrier
            self.client_writer.queue.put(('user-error', f'move {direction} unsuccessful'))

        return True