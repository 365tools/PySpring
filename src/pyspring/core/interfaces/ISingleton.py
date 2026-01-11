from typing import Protocol
from typing_extensions import runtime_checkable

from pyspring.core.interfaces.IService import IService


@runtime_checkable
class ISingletonService(IService, Protocol):
    """
    单例模式
    """

    @staticmethod
    def single() -> bool:
        return True
