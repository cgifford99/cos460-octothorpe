from queue import Queue

from common.services.serviceBase import ServiceBase


class ClientWriterService(ServiceBase):
    def __init__(self) -> None:
        self.queue: Queue[tuple[str, object]] = Queue()