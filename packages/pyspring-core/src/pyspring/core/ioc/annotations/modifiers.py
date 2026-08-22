"""
修饰器

定义用于修饰组件行为的装饰器：Primary, Lazy
这些装饰器通常与其他组件装饰器组合使用。
"""

from typing import Callable, TypeVar, Union

T = TypeVar("T")


def Primary(cls: (type[T]) | None = None) -> Union[type[T], Callable[[type[T]], type[T]]]:
    """
    主要候选者装饰器

    当有多个相同类型的Bean时，标记为Primary的Bean将被优先使用。

    支持两种使用方式：
    1. 不带括号：@Primary
    2. 带括号：@Primary()

    示例：
        @Component
        @Primary
        class PrimaryUserService(IUserService):
            pass

        @Component
        @Primary()
        class AnotherPrimaryService(IService):
            pass

        @Component
        class SecondaryUserService(IUserService):
            pass

        # 当注入 IUserService 时，将使用 PrimaryUserService
    """

    def decorator(target: type[T]) -> type[T]:
        setattr(target, "__pyspring_primary__", True)
        return target

    # 判断是否直接作为装饰器使用（不带括号）
    if cls is not None:
        # @Primary 形式：直接装饰类
        return decorator(cls)
    else:
        # @Primary() 形式：返回装饰器函数
        return decorator


def Lazy(cls: (type[T]) | None = None) -> Union[type[T], Callable[[type[T]], type[T]]]:
    """
    懒加载装饰器

    标记Bean延迟到第一次使用时才实例化，而不是容器启动时立即实例化。

    支持两种使用方式：
    1. 不带括号：@Lazy
    2. 带括号：@Lazy()

    使用场景：
    - 启动时间敏感的应用
    - 可能不会被使用的Bean
    - 实例化成本高的Bean

    示例：
        @Component
        @Singleton
        @Lazy
        class ExpensiveService:
            def __init__(self):
                # 耗时的初始化操作
                pass

        @Component
        @Lazy()
        class AnotherLazyService:
            pass
    """

    def decorator(target: type[T]) -> type[T]:
        setattr(target, "__pyspring_lazy__", True)
        return target

    # 判断是否直接作为装饰器使用（不带括号）
    if cls is not None:
        # @Lazy 形式：直接装饰类
        return decorator(cls)
    else:
        # @Lazy() 形式：返回装饰器函数
        return decorator


__all__ = [
    "Primary",
    "Lazy",
]
