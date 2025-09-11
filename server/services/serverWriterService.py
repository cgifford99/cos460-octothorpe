from queue import Queue

from common.services.serviceBase import ServiceBase


class ServerWriterService(ServiceBase):
    def __init__(self) -> None:
        self.queue: Queue[tuple[str, object]] = Queue()