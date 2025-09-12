import copy

from common.services.serviceBase import ServiceBase


class ClientMapService(ServiceBase):
    def __init__(self):
        self.map: list[str] = []
        self.map_dimensions: tuple[int, int] | None = None
        # map_mask using array of tuple
        # where tuple = (entity_abbr, x, y)
        # and entity_abbr is preferably a single char
        self.map_mask: list[tuple[str, int, int]] = []
        self.treasure_mask: list[tuple[str, int, int]] = []

    def has_valid_map(self) -> bool:
        return bool(self.map and self.map_mask)

    def build_map(self) -> list[str]:
        # add map and map_mask to build string/ascii map with mask
        temp_map: list[str] = copy.deepcopy(self.map)
        masks: list[tuple[str, int, int]] = self.treasure_mask + self.map_mask
        for entity_abbr, x, y in masks:
            temp_map[y] = temp_map[y][:x] + entity_abbr + temp_map[y][x+1:]
        return temp_map
    
    def update_player_position(self, entity_abbr: str, x: int, y: int) -> None:
        if not self.map:
            return

        entity_idx: int = -1
        for index, item in enumerate(self.map_mask):
            if item[0] == entity_abbr:
                entity_idx = index
                break
        if entity_idx != -1:
            self.map_mask[entity_idx] = (entity_abbr, x, y)
        else:
            self.map_mask.append((entity_abbr, x, y))

    def update_treasure_position(self, x: int, y: int) -> None:
        self.treasure_mask.append(('#', x, y))