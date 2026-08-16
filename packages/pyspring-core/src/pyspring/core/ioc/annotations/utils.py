"""
装饰器工具函数

提供通用的装饰器模式处理函数，用于简化装饰器的实现。
"""
import inspect
from abc import ABCMeta
from typing import Callable, TypeVar

T = TypeVar('T')


def is_abstract_type(target: type) -> bool:
    """
    检测一个类型是否为抽象类型（抽象类、协议类等）
    
    Args:
        target: 要检测的类型
        
    Returns:
        bool: 如果是抽象类型返回 True，否则返回 False
        
    示例:
        >>> from abc import ABC, abstractmethod
        >>> class IService(ABC):
        ...     @abstractmethod
        ...     def do_something(self): pass
        >>> is_abstract_type(IService)
        True
        >>> class ConcreteService:
        ...     pass
        >>> is_abstract_type(ConcreteService)
        False
    """
    return (
            inspect.isabstract(target) or
            isinstance(target, ABCMeta) or
            getattr(target, '_is_protocol', False)
    )


def set_pyspring_attribute(
        target: type[T] | Callable[..., object],
        attr_name: str,
        value: object
) -> None:
    """
    设置 PySpring 内部属性
    
    Args:
        target: 目标类或函数
        attr_name: 属性名（会自动添加 __pyspring_ 前缀）
        value: 属性值
        
    示例:
        >>> class MyService:
        ...     pass
        >>> set_pyspring_attribute(MyService, "component", True)
        >>> hasattr(MyService, "__pyspring_component__")
        True
    """
    full_name = f"__pyspring_{attr_name}__"
    setattr(target, full_name, value)


def create_flexible_decorator(
        attr_name: str,
        attr_value: object = True,
        support_params: bool = False,
        param_handlers: dict[str, str] | None = None
) -> Callable[..., object]:
    """
    创建支持有参/无参两种形式的装饰器
    
    Args:
        attr_name: PySpring 属性名（不含前后缀）
        attr_value: 属性默认值
        support_params: 是否支持参数
        param_handlers: 参数处理器字典 {param_name: attr_name}
        
    Returns:
        装饰器函数
        
    示例:
        >>> # 创建简单的标记装饰器
        >>> Primary = create_flexible_decorator("primary")
        >>> @Primary
        ... class MyService:
        ...     pass
        >>> @Primary()
        ... class AnotherService:
        ...     pass
        
        >>> # 创建带参数的装饰器
        >>> Component = create_flexible_decorator(
        ...     "component",
        ...     support_params=True,
        ...     param_handlers={"name": "name", "primary": "primary", "lazy": "lazy"}
        ... )
    """
    param_handlers = param_handlers or {}

    def decorator_impl(
            cls_or_none: type[T] | None = None,
            **kwargs: object
    ) -> type[T] | Callable[[type[T]], type[T]]:
        """实际的装饰器实现"""

        def apply_attributes(cls: type[T]) -> type[T]:
            """应用属性到类"""
            # 设置主属性
            set_pyspring_attribute(cls, attr_name, attr_value)

            # 处理额外参数
            if support_params and param_handlers:
                for param_name, pyspring_attr_name in param_handlers.items():
                    if param_name in kwargs and kwargs[param_name] is not None:
                        set_pyspring_attribute(cls, pyspring_attr_name, kwargs[param_name])

            return cls

        # 判断是否直接装饰（不带括号）
        if cls_or_none is not None:
            # @Decorator 形式
            return apply_attributes(cls_or_none)
        else:
            # @Decorator() 或 @Decorator(params) 形式
            return apply_attributes

    return decorator_impl


def create_component_decorator(
        component_type: str
) -> Callable[..., object]:
    """
    创建组件类型装饰器（Component, Service, Repository）
    
    这些装饰器都支持：
    1. 不带括号：@Component
    2. 带括号：@Component
    3. 带参数：@Component(name="xxx", primary=True, lazy=True)
    
    Args:
        component_type: 组件类型名称（用于文档和元数据）
        
    Returns:
        组件装饰器函数
    """

    def decorator(
            cls: type[T] | None = None,
            name: str | None = None,
            primary: bool = False,
            lazy: bool = False
    ) -> type[T] | Callable[[type[T]], type[T]]:

        def apply_decorator(target: type[T]) -> type[T]:
            set_pyspring_attribute(target, "component", True)
            if name:
                set_pyspring_attribute(target, "name", name)
            if primary:
                set_pyspring_attribute(target, "primary", True)
            if lazy:
                set_pyspring_attribute(target, "lazy", True)
            return target

        # 判断是否直接装饰（不带括号）
        if cls is not None:
            return apply_decorator(cls)
        else:
            return apply_decorator

    return decorator


__all__ = [
    'is_abstract_type',
    'set_pyspring_attribute',
    'create_flexible_decorator',
    'create_component_decorator',
]
