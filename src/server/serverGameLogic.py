import math
import random

from ..models.game.treasure import Treasure
from ..utils.fileUtils import FileUtils


class OctothorpeServerGameLogic(object):
    '''The Server Game Logic class is responsible for managing all server-wide, non-client-specific game logic.
    
    Only one instance of this class is created for the server and does not need its own thread.
    '''
    NUM_TREASURES: int = 15
    TREASURE_BOUNDARY: int = 3
    TREASURE_FOW: int = 5

    def __init__(self, root_path: str):
        self.map_filepath: str = FileUtils.get_map_filepath(root_path)

        self.map: list[str] = self._load_map_from_file(self.map_filepath)
        self.spawnpoint: tuple[int, int] = (1,1)
        for line_idx in range(len(self.map)):
            if 'S' in self.map[line_idx]:
                sp_pos = self.map[line_idx].index('S')
                self.spawnpoint = (sp_pos, line_idx)

        self.treasures: list[Treasure] = self._generate_treasures()

    def _load_map_from_file(self, filename: str) -> list[str]:
        with open(filename, 'r', encoding='utf-8') as map_f:
            return map_f.readlines()

    def _generate_treasures(self) -> list[Treasure]:
        new_treasures: list[Treasure] = []
        for _ in range(self.NUM_TREASURES):
            x: int = random.randrange(1, len(self.map[0])-1)
            y: int = random.randrange(1, len(self.map)-1)
            distance_to_nearest_treasure: float = self.distance_nearest_treasure((x,y))
            if self.map[y][x] == ' ' and (distance_to_nearest_treasure > self.TREASURE_BOUNDARY or distance_to_nearest_treasure == -1):
                new_treasure = Treasure(
                    len(self.treasures), (x,y), random.randint(1, self.NUM_TREASURES)
                )
                new_treasures.append(new_treasure)
        return new_treasures

    def nearby_treasures(self, position: tuple[int, int]) -> list[tuple[Treasure, float]]:
        nearby_treasure: list[tuple[Treasure, float]] = []
        for treasure in self.treasures:
            dist: float = self.distance_to_treasure(treasure, position)
            if dist < self.TREASURE_FOW:
                nearby_treasure.append((treasure, dist))
        return nearby_treasure

    def distance_nearest_treasure(self, position: tuple[int, int]):
        min_distance: float = -1
        for treasure in self.treasures:
            distance = self.distance_to_treasure(treasure, position)
            if min_distance < 0 or distance < min_distance:
                min_distance = distance
        return min_distance

    def distance_to_treasure(self, treasure: Treasure, position: tuple[int, int]) -> float:
        x0, y0 = position
        x1, y1 = treasure.position
        return round(math.sqrt((x1-x0)**2+(y1-y0)**2), 2)