from typing import Any, TypeVar, cast

from common.services.serviceBase import ServiceBase


class ServiceManager():
    def __init__(self) -> None:
        self.services: dict[type, ServiceBase] = {}

    _svcT = TypeVar("_svcT", bound=ServiceBase)
    def register(self, svc_cls: type[_svcT], **svc_kwargs: Any) -> None:
        new_svc: ServiceBase = svc_cls(**svc_kwargs)
        self.services[svc_cls] = new_svc

    def get_service[_svcT](self, svc_cls: type[_svcT]) -> _svcT:
        if svc_cls in self.services.keys():
            return cast(_svcT, self.services[svc_cls])
        else:
            raise ValueError(f'Service with type \'{svc_cls.__name__}\' is not registered as a service')