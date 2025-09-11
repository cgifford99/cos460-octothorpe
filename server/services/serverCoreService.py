from common.services.serviceBase import ServiceBase


class ServerCoreService(ServiceBase):
    def __init__(self, root_path: str):
        self.root_path = root_path