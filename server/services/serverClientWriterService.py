from queue import Queue


class ServerClientWriterService():
    def __init__(self) -> None:
        self.queue: Queue[tuple[str, object]] = Queue()