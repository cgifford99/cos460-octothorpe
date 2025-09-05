from .serverClientInterface import OctothorpeServerClientInterface


class OctothorpeServerClientGameLogic(OctothorpeServerClientInterface):
    def __init__(self, server, conn, addr, queue, game_logic, user):
        super().__init__(conn, addr)
        self.server = server
        self.queue = queue
        self.game_logic = game_logic
        self.user = user

        self.valid_cmds = ['move', 'map', 'cheatmap']

    def execute_cmd(self, command_agg):
        operation = command_agg[0]
        if operation == 'move':
            return self.move(command_agg)
        elif operation == 'map':
            self.queue.put(('map', None))
            return True
        elif operation == 'cheatmap':
            self.queue.put(('cheatmap', None))
            return True
    
    def move(self, command_agg):
        if len(command_agg) != 2:
            return self.send_msg(400, f'Invalid login command. Use format: \'move [direction]\'')
        direction = command_agg[1]
        new_pos = self.user.position
        if direction == 'north':
            new_pos = (new_pos[0], new_pos[1] - 1)
        elif direction == 'south':
            new_pos = (new_pos[0], new_pos[1] + 1)
        elif direction == 'west':
            new_pos = (new_pos[0] - 1, new_pos[1])
        elif direction == 'east':
            new_pos = (new_pos[0] + 1, new_pos[1])
        else:
            return self.send_msg(400, f'invalid direction \'{direction}\'')
        if self.game_logic.map[new_pos[1]][new_pos[0]] in [' ', 'S']:
            self.user.position = new_pos
            nearby_treasures = self.game_logic.nearby_treasures(self.user.position)
            for treasure, dist in nearby_treasures:
                if dist == 0:
                    self.queue.put(('treasure-found', treasure))
                    self.user.score += treasure["score"]
                else:
                    self.queue.put(('treasure-nearby', treasure))
            self.queue.put(('move', None))
        self.send_msg(200, 'move ' + direction)
        return True