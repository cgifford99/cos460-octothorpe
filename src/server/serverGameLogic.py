import math
import random

from ..utils.fileUtils import FileUtils


class OctothorpeServerGameLogic(object):
    '''The Server Game Logic class is responsible for managing all server-wide, non-client-specific game logic.
    
    Only one instance of this class is created for the server and does not need its own thread.
    '''
    NUM_TREASURES = 15
    TREASURE_BOUNDARY = 3
    TREASURE_FOW = 5

    def __init__(self, root_path):
        self.map_filepath = FileUtils.get_map_filepath(root_path)

        self._load_map(self.map_filepath)
        self.spawnpoint = (1,1)
        for line_idx in range(len(self.map)):
            if 'S' in self.map[line_idx]:
                sp_pos = self.map[line_idx].index('S')
                self.spawnpoint = (sp_pos, line_idx)

        self.treasures = []
        self._generate_treasures()

    def _load_map(self, filename):
        with open(filename, 'r', encoding='utf-8') as map_f:
            self.map = map_f.readlines()

    def _generate_treasures(self):
        num_treasure = 0
        while num_treasure < self.NUM_TREASURES:
            x = random.randrange(1, len(self.map[0])-1)
            y = random.randrange(1, len(self.map)-1)
            distance_to_nearest_treasure = self.distance_nearest_treasure((x,y))
            if self.map[y][x] == ' ' and (distance_to_nearest_treasure > self.TREASURE_BOUNDARY or distance_to_nearest_treasure == -1):
                self.treasures.append({'id':len(self.treasures), 'position':(x,y), 'score':random.randint(1, 20)})
                num_treasure += 1

    def nearby_treasures(self, position):
        nearby_treasure = []
        for treasure in self.treasures:
            dist = self.distance_to_treasure(treasure, position)
            if dist < self.TREASURE_FOW:
                nearby_treasure.append((treasure, dist))
        return nearby_treasure

    def distance_nearest_treasure(self, position):
        min_distance = -1
        for treasure in self.treasures:
            distance = self.distance_to_treasure(treasure, position)
            if min_distance < 0 or distance < min_distance:
                min_distance = distance
        return min_distance

    def distance_to_treasure(self, treasure, position):
        x0, y0 = position
        x1, y1 = treasure['position']
        return round(math.sqrt((x1-x0)**2+(y1-y0)**2), 2)