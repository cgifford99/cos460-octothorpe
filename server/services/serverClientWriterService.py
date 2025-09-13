from queue import Queue

from server.models.serverClientWriterEvent import ServerClientWriterEventBase


class ServerClientWriterService():
    '''This service does not inherit ServiceBase as it functions *like* a service, but should not be registered in the ServiceManager.
    Instances of this class are created by the ServerClientWriterManager.
    '''
    def __init__(self) -> None:
        self.queue: Queue[ServerClientWriterEventBase] = Queue()

    def dispatch_event(self, event: ServerClientWriterEventBase) -> None:
        self.queue.put(event)