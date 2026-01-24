"""
IOC组件注解

定义组件的注册方式
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
        # @Component() 或 @Component(name="xxx") 形式：返回装饰器函数
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
    服务装饰器（@Component的语义化别名）
    
    功能与 @Component 完全相同，仅为了代码语义更清晰。
    
    支持两种使用方式：
    1. 不带括号：@Service
    2. 带括号：@Service(name="xxx", primary=True)
    
    示例：
        # 不带括号
        @Service
        @Singleton
        class AuthenticationService:
            pass
        
        # 带括号
        @Service(name="auth_service", primary=True)
        @Singleton
        class AuthenticationService:
            pass
    """
    return Component(cls=cls, name=name, primary=primary, lazy=lazy)


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
    仓储装饰器（@Component的语义化别名）
    
    专门用于标记Repository层的类。
    
    支持两种使用方式：
    1. 不带括号：@Repository
    2. 带括号：@Repository(name="xxx", primary=True)
    
    示例：
        # 不带括号
        @Repository
        @Singleton
        class UserRepository:
            pass
        
        # 带括号
        @Repository(name="user_repo", primary=True)
        @Singleton
        class UserRepository:
            pass
    """
    return Component(cls=cls, name=name, primary=primary, lazy=lazy)


def Configuration(cls: Type[T]) -> Type[T]:
    """
    配置类装饰器
    
    标记一个类为配置类，其中的 @Bean 方法将被扫描和注册。
    
    示例：
        @Configuration
        class SecurityConfig:
            @Bean
            def auth_provider(self) -> IAuthProvider:
                return JWTAuthProvider()
    """
    setattr(cls, "__pyspring_configuration__", True)
    setattr(cls, "__pyspring_component__", True)  # 配置类本身也是组件
    return cls


def Bean(
        func_or_name: Optional[Callable[..., T] | str] = None,
        *,
        name: Optional[str] = None,
        init_method: Optional[str] = None,
        destroy_method: Optional[str] = None
) -> Callable[[Callable[..., T]], Callable[..., T]] | Callable[..., T]:
    """
    Bean方法装饰器（支持有参和无参两种用法）
    
    标记配置类中的方法为Bean工厂方法。
    
    用法1: 无参数（像@staticmethod一样）:
        @Bean
        def data_source(self) -> DataSource:
            return PostgresDataSource()
    
    用法2: 带参数:
        @Bean(name="custom_cache")
        def cache_service(self) -> ICacheService:
            return RedisCache()
    
    Args:
        func_or_name: 如果直接装饰函数，这是函数对象；如果带参数调用，这是name参数
        name: Bean名称（可选，默认使用方法名）
        init_method: 初始化方法名（可选）
        destroy_method: 销毁方法名（可选）
    
    示例：
        @Configuration
        class AppConfig:
            @Bean  # 无括号
            def data_source(self) -> DataSource:
                return PostgresDataSource()
            
            @Bean()  # 空括号
            def another_source(self) -> DataSource:
                return MySQLDataSource()
            
            @Bean(name="custom_cache")  # 带参数
            def cache_service(self) -> ICacheService:
                return RedisCache()
    """

    # 检查是否是直接装饰（@Bean 不带括号）
    # 条件：第一个参数是可调用对象且没有通过name参数传值
    if callable(func_or_name) and name is None:
        # 直接装饰模式：@Bean
        func = func_or_name
        setattr(func, "__pyspring_bean__", True)
        return func

    # 带参数模式：@Bean() 或 @Bean(name=...)
    # 如果 func_or_name 是字符串，说明是位置参数传入的name
    actual_name = func_or_name if isinstance(func_or_name, str) else name
    
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        # 直接在原函数上设置属性，不使用wrapper
        # 因为@wraps会重置自定义属性
        setattr(func, "__pyspring_bean__", True)
        if actual_name:
            setattr(func, "__pyspring_bean_name__", actual_name)
        if init_method:
            setattr(func, "__pyspring_init_method__", init_method)
        if destroy_method:
            setattr(func, "__pyspring_destroy_method__", destroy_method)
        return func
    
    return decorator


def ConditionalOnMissingBean(bean_type: type) -> Callable[[Union[Type[T], Callable[..., T]]], Union[Type[T], Callable[..., T]]]:
    """
    条件Bean装饰器（支持装饰类和方法）
    
    仅当指定类型的Bean不存在时，才注册此Bean/组件。
    用于提供默认实现，允许用户覆盖。
    
    Args:
        bean_type: 检查的Bean类型
    
    使用场景1: 装饰 @Bean 方法（在配置类中）
        @Configuration
        class DefaultConfig:
            @Bean()
            @ConditionalOnMissingBean(IAuthProvider)
            def default_auth_provider(self) -> IAuthProvider:
                return DefaultAuthProvider()
    
    使用场景2: 装饰组件类（实现了 IManaged 的默认实现类）
        @ConditionalOnMissingBean(ILoginProvider)
        class DefaultPasswordLoginProvider(ILoginProvider):
            '''用户可以通过提供自己的 ILoginProvider 实现来替换此默认类'''
            pass
    """

    def decorator(target: Union[Type[T], Callable[..., T]]) -> Union[Type[T], Callable[..., T]]:
        setattr(target, "__pyspring_conditional_on_missing_bean__", bean_type)
        return target

    return decorator


def Primary(cls: Type[T]) -> Type[T]:
    """
    主要候选者装饰器
    
    当有多个相同类型的Bean时，标记为Primary的Bean将被优先使用。
    
    示例：
        @Component
        @Primary
        class PrimaryUserService(IUserService):
            pass
        
        @Component
        class SecondaryUserService(IUserService):
            pass
        
        # 当注入 IUserService 时，将使用 PrimaryUserService
    """
    setattr(cls, "__pyspring_primary__", True)
    return cls


def Lazy(cls: Type[T]) -> Type[T]:
    """
    懒加载装饰器
    
    标记Bean延迟到第一次使用时才实例化，而不是容器启动时立即实例化。
    
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
    """
    setattr(cls, "__pyspring_lazy__", True)
    return cls


__all__ = [
    'Component',
    'Service',
    'Repository',
    'Configuration',
    'Bean',
    'ConditionalOnMissingBean',
    'Primary',
    'Lazy'
]
