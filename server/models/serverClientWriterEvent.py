from enum import Enum, auto

from common.models.comprehensiveSearchEnum import ComprehensiveSearchEnum
from common.models.game.direction import Direction
from common.models.game.treasure import Treasure


class ServerClientWriterEventEnum(Enum, metaclass=ComprehensiveSearchEnum):
    LOGIN = auto()
    LOGOUT = auto()
    MOVE = auto()
    MAP = auto()
    CHEATMAP = auto()
    TREASURE_FOUND = auto()
    TREASURE_NEARBY = auto()
    INFO = auto()
    TREASURE_INFO = auto()
    SUCCESS = auto()
    USER_ERROR = auto()
    SERVER_ERROR = auto()


class ServerClientWriterEventBase():
    def __init__(self, key: ServerClientWriterEventEnum) -> None:
        self.key = key


class ServerClientWriterEventLogin(ServerClientWriterEventBase):
    def __init__(self):
        super().__init__(ServerClientWriterEventEnum.LOGIN)


class ServerClientWriterEventLogout(ServerClientWriterEventBase):
    def __init__(self):
        super().__init__(ServerClientWriterEventEnum.LOGOUT)


class ServerClientWriterEventMove(ServerClientWriterEventBase):
    def __init__(self, direction: Direction):
        super().__init__(ServerClientWriterEventEnum.MOVE)
        self.direction = direction


class ServerClientWriterEventMap(ServerClientWriterEventBase):
    def __init__(self):
        super().__init__(ServerClientWriterEventEnum.MAP)


class ServerClientWriterEventCheatmap(ServerClientWriterEventBase):
    def __init__(self):
        super().__init__(ServerClientWriterEventEnum.CHEATMAP)


class ServerClientWriterEventTreasureFound(ServerClientWriterEventBase):
    def __init__(self, treasure: Treasure):
        super().__init__(ServerClientWriterEventEnum.TREASURE_FOUND)
        self.treasure = treasure


class ServerClientWriterEventTreasureNearby(ServerClientWriterEventBase):
    def __init__(self, treasure: Treasure):
        super().__init__(ServerClientWriterEventEnum.TREASURE_NEARBY)
        self.treasure = treasure


class ServerClientWriterEventInfo(ServerClientWriterEventBase):
    def __init__(self, msg: str):
        super().__init__(ServerClientWriterEventEnum.INFO)
        self.msg = msg


class ServerClientWriterEventTreasureInfo(ServerClientWriterEventBase):
    def __init__(self, msg: str):
        super().__init__(ServerClientWriterEventEnum.TREASURE_INFO)
        self.msg = msg


class ServerClientWriterEventSuccess(ServerClientWriterEventBase):
    def __init__(self, msg: str):
        super().__init__(ServerClientWriterEventEnum.SUCCESS)
        self.msg = msg


class ServerClientWriterEventUserError(ServerClientWriterEventBase):
    def __init__(self, msg: str):
        super().__init__(ServerClientWriterEventEnum.USER_ERROR)
        self.msg = msg
        

class ServerClientWriterEventServerError(ServerClientWriterEventBase):
    def __init__(self, msg: str):
        super().__init__(ServerClientWriterEventEnum.SERVER_ERROR)
        self.msg = msg

