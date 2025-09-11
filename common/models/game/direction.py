from enum import Enum, unique

from common.models.comprehensiveSearchEnum import ComprehensiveSearchEnum


@unique
class Direction(Enum, metaclass=ComprehensiveSearchEnum):
    NORTH = 1
    EAST = 2
    SOUTH = 3
    WEST = 4

    def __str__(self) -> str:
        return self.name.lower()



