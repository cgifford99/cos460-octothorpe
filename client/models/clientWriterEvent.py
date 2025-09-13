from enum import Enum, auto

from common.models.comprehensiveSearchEnum import ComprehensiveSearchEnum


class ClientWriterEventEnum(Enum, metaclass=ComprehensiveSearchEnum):
    PRINT_INPUT_LINE = auto()
    PRINT_SCROLLING = auto()
    UPDATE_SCREEN = auto()

class ClientWriterEventBase():
    def __init__(self, key: ClientWriterEventEnum) -> None:
        self.key = key


class ClientWriterEventPrintInputLine(ClientWriterEventBase):
    def __init__(self, line: str):
        super().__init__(ClientWriterEventEnum.PRINT_INPUT_LINE)
        self.line = line


class ClientWriterEventPrintScrolling(ClientWriterEventBase):
    def __init__(self, line: str):
        super().__init__(ClientWriterEventEnum.PRINT_SCROLLING)
        self.line = line


class ClientWriterEventUpdateScreen(ClientWriterEventBase):
    def __init__(self):
        super().__init__(ClientWriterEventEnum.UPDATE_SCREEN)
