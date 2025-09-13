from queue import Queue

from common.services.serviceBase import ServiceBase
from server.models.serverWriterEvent import ServerWriterEventBase


class ServerWriterService(ServiceBase):
    def __init__(self) -> None:
        self.queue: Queue[ServerWriterEventBase] = Queue()

    def dispatch_event(self, event: ServerWriterEventBase) -> None:
        self.queue.put(event)