from queue import Queue

from client.models.clientWriterEvent import ClientWriterEventBase
from common.services.serviceBase import ServiceBase


class ClientWriterService(ServiceBase):
    def __init__(self) -> None:
        self.queue: Queue[ClientWriterEventBase] = Queue()

    def dispatch_event(self, event: ClientWriterEventBase) -> None:
        self.queue.put(event)