from blessed import Terminal

from common.models.user import OctothorpeUser
from common.services.serviceBase import ServiceBase


class ClientCoreService(ServiceBase):
    def __init__(self) -> None:
        self.term = Terminal()
        if not self.term.is_a_tty:
            raise Exception('A terminal is required to use this program')
        
        self.user_info = OctothorpeUser()


