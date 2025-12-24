from abc import ABC

from pyspring.interfaces.ISingleton import ISingletonService


class ISystemService(ISingletonService, ABC):
    """
    系统管理服务接口
    """
