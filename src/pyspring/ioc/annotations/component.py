"""
组件类装饰器

定义用于标记组件的装饰器：Component, Service, Repository
这些是语义化的装饰器，用于不同的应用层。
"""
from typing import TypeVar, Type, Optional, Callable, Union, overload

T = TypeVar('T')


@overload
def Component(cls: Type[T]) -> Type[T]: ...


@overload
def Component(
        name: Optional[str] = None,
        primary: bool = False,
        lazy: bool = False
) -> Callable[[Type[T]], Type[T]]: ...


def Component(
        cls: Optional[Type[T]] = None,
        name: Optional[str] = None,
        primary: bool = False,
        lazy: bool = False
) -> Union[Type[T], Callable[[Type[T]], Type[T]]]:
    """
    组件装饰器
    
    标记一个类为IOC组件，将被自动扫描和注册。
    
    支持两种使用方式：
    1. 不带括号：@Component（使用默认参数）
    2. 带括号：@Component(name="xxx", primary=True)（自定义参数）
    
    Args:
        cls: 被装饰的类（内部使用，自动传入）
        name: 组件名称（可选，默认使用类名的snake_case形式）
        primary: 是否为主要候选者（当有多个实现时优先使用）
        lazy: 是否懒加载（延迟到第一次使用时才实例化）
    
    使用场景：
    - 业务服务类
    - 工具类
    - 管理器类
    
    示例：
        # 不带括号
        @Component
        @Singleton
        class UserService:
            def __init__(self, user_repo: IUserRepository):
                self.user_repo = user_repo
        
        # 带括号和参数
        @Component(name="custom_user_service", primary=True)
        @Singleton
        class UserService:
            pass
    """

    def decorator(cls: Type[T]) -> Type[T]:
        setattr(cls, "__pyspring_component__", True)
        if name:
            setattr(cls, "__pyspring_name__", name)
        if primary:
            setattr(cls, "__pyspring_primary__", True)
        if lazy:
            setattr(cls, "__pyspring_lazy__", True)
        return cls

    # 判断是否直接作为装饰器使用（不带括号）
    if cls is not None:
        # @Component 形式：直接装饰类
        return decorator(cls)
    else:
        # @Component 或 @Component(name="xxx") 形式：返回装饰器函数
        return decorator


@overload
def Service(cls: Type[T]) -> Type[T]: ...


@overload
def Service(
        name: Optional[str] = None,
        primary: bool = False,
        lazy: bool = False
) -> Callable[[Type[T]], Type[T]]: ...


def Service(
        cls: Optional[Type[T]] = None,
        name: Optional[str] = None,
        primary: bool = False,
        lazy: bool = False
) -> Union[Type[T], Callable[[Type[T]], Type[T]]]:
    """
    服务层组件装饰器
    
    等同于 @Component，但语义上表示服务层组件。
    
    支持两种使用方式：
    1. 不带括号：@Service
    2. 带括号：@Service(name="xxx")
    
    使用场景：
    - 业务逻辑层
    - 服务类
    
    示例：
        @Service
        @Singleton
        class OrderService:
            def __init__(self, order_repo: IOrderRepository):
                self.order_repo = order_repo
    """
    return Component(cls, name, primary, lazy)


@overload
def Repository(cls: Type[T]) -> Type[T]: ...


@overload
def Repository(
        name: Optional[str] = None,
        primary: bool = False,
        lazy: bool = False
) -> Callable[[Type[T]], Type[T]]: ...


def Repository(
        cls: Optional[Type[T]] = None,
        name: Optional[str] = None,
        primary: bool = False,
        lazy: bool = False
) -> Union[Type[T], Callable[[Type[T]], Type[T]]]:
    """
    数据访问层组件装饰器
    
    等同于 @Component，但语义上表示数据访问层组件。
    
    支持两种使用方式：
    1. 不带括号：@Repository
    2. 带括号：@Repository(name="xxx")
    
    使用场景：
    - 数据访问层
    - DAO类
    - Repository类
    
    示例：
        @Repository
        @Singleton
        class UserRepository(IUserRepository):
            def find_by_id(self, user_id: int) -> User:
                pass
    """
    return Component(cls, name, primary, lazy)


__all__ = [
    'Component',
    'Service',
    'Repository',
]
