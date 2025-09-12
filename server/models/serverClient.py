import uuid
from socket import socket


class ServerClient():
    def __init__(self, conn: socket, addr: str) -> None:
        self.client_id = str(uuid.uuid4())
        self.conn: socket = conn
        self.addr: str = addr