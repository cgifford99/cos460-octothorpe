from enum import Enum, auto

from common.models.comprehensiveSearchEnum import ComprehensiveSearchEnum
from common.models.game.treasure import Treasure
from common.models.user import OctothorpeUser


class ServerWriterEventEnum(Enum, metaclass=ComprehensiveSearchEnum):
    LOGIN = auto()
    LOGOUT = auto()
    MOVE = auto()
    TREASURE_FOUND = auto()


class ServerWriterEventBase():
    def __init__(self, key: ServerWriterEventEnum) -> None:
        self.key = key


class ServerWriterEventLogin(ServerWriterEventBase):
    def __init__(self, user: OctothorpeUser | None):
        super().__init__(ServerWriterEventEnum.LOGIN)
        self.user = user


class ServerWriterEventLogout(ServerWriterEventBase):
    def __init__(self, user: OctothorpeUser | None):
        super().__init__(ServerWriterEventEnum.LOGOUT)
        self.user = user


class ServerWriterEventMove(ServerWriterEventBase):
    def __init__(self, user: OctothorpeUser | None):
        super().__init__(ServerWriterEventEnum.MOVE)
        self.user = user


class ServerWriterEventTreasureFound(ServerWriterEventBase):
    def __init__(self, user: OctothorpeUser | None, treasure: Treasure):
        super().__init__(ServerWriterEventEnum.TREASURE_FOUND)
        self.user = user
        self.treasure = treasure