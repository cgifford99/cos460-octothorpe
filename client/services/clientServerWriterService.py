from queue import Queue

from common.services.serviceBase import ServiceBase


class ClientServerWriterService(ServiceBase):
    def __init__(self) -> None:
        self.queue: Queue[str] = Queue()

    def dispatch_request(self, req: str) -> None:
        self.queue.put(req)