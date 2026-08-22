"""
PySpring AOP Main Entry Point
"""

from typing import Any

from .core.decorators import after, around, aspect, before
from .core.models import Advice, Aspect, JoinPoint
from .proxy.factory import create_proxy as _create_proxy_func
from .proxy.wrapper import AopProxy


class Aop:
    """
    AOP Main Access Point
    Exposes all AOP functionality through a single class interface.
    """

    # Types
    JoinPoint = JoinPoint
    Aspect = Aspect
    Advice = Advice
    AopProxy = AopProxy

    # Decorators
    # using staticmethod to ensure they behave correctly when accessed on the class
    aspect = staticmethod(aspect)
    before = staticmethod(before)
    after = staticmethod(after)
    around = staticmethod(around)

    @staticmethod
    def create_proxy(target: Any, aspects: list[Any]) -> Any:
        """
        Create an AOP proxy for the target object
        """
        return _create_proxy_func(target, aspects)
