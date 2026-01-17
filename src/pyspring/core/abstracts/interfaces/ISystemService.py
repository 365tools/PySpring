from abc import ABC

from .ISingleton import ISingletonService


class ISystemService(ISingletonService, ABC):
    """
    系统管理服务接口
    """
