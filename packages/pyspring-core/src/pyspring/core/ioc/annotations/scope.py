"""
IOC作用域注解

定义服务的生命周期作用域
"""

from enum import Enum
from typing import TypeVar

T = TypeVar("T")


class Scope(Enum):
    """服务作用域枚举"""

    SINGLETON = "singleton"  # 单例：整个应用生命周期只有一个实例
    PROTOTYPE = "prototype"  # 原型：每次请求都创建新实例
    REQUEST = "request"  # 请求：每个HTTP请求一个实例（未来实现）
    SESSION = "session"  # 会话：每个会话一个实例（未来实现）


def Singleton(cls: type[T]) -> type[T]:
    """
    单例作用域装饰器

    标记此类为单例模式，IOC容器将在整个应用生命周期中只创建一个实例。

    使用场景：
    - 无状态的服务类
    - 配置管理器
    - 缓存管理器
    - 数据库连接池

    示例：
        @Component
        @Singleton
        class UserService:
            pass
    """
    setattr(cls, "__pyspring_scope__", Scope.SINGLETON)
    return cls


def Prototype(cls: type[T]) -> type[T]:
    """
    原型作用域装饰器

    标记此类为原型模式，IOC容器每次请求都会创建新实例。

    使用场景：
    - 有状态的服务类
    - 需要保持独立状态的对象
    - 临时使用的对象

    示例：
        @Component
        @Prototype
        class TaskProcessor:
            pass
    """
    setattr(cls, "__pyspring_scope__", Scope.PROTOTYPE)
    return cls


def get_scope(cls: type) -> Scope:
    """
    获取类的作用域

    Args:
        cls: 类型

    Returns:
        作用域，默认为 SINGLETON
    """
    return getattr(cls, "__pyspring_scope__", Scope.SINGLETON)


__all__ = ["Scope", "Singleton", "Prototype", "get_scope"]
