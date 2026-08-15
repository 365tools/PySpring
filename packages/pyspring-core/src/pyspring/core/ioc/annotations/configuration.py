"""
配置类装饰器

定义用于配置类和Bean工厂方法的装饰器：Configuration, Bean
"""
from typing import TypeVar, Callable, Union

T = TypeVar('T')


def Configuration(cls: (type[T]) | None = None) -> Union[type[T], Callable[[type[T]], type[T]]]:
    """
    配置类装饰器
    
    标记一个类为配置类，其中的 @Bean 方法将被扫描和注册。
    
    支持两种使用方式：
    1. 不带括号：@Configuration
    2. 带括号：@Configuration()
    
    使用场景：
    - 定义Bean的工厂类
    - 集中管理应用配置
    
    示例：
        @Configuration
        class DatabaseConfig:
            @Bean
            def data_source(self) -> DataSource:
                return PostgresDataSource()
            
            @Bean
            def session_factory(self, data_source: DataSource) -> SessionFactory:
                return SessionFactory(data_source)
    """

    def decorator(target: type[T]) -> type[T]:
        setattr(target, "__pyspring_configuration__", True)
        return target

    # 判断是否直接作为装饰器使用（不带括号）
    if cls is not None:
        # @Configuration 形式：直接装饰类
        return decorator(cls)
    else:
        # @Configuration() 形式：返回装饰器函数
        return decorator


def Bean(
        func_or_name: (Callable[..., T] | str) | None = None,
        *,
        name: (str) | None = None,
        init_method: (str) | None = None,
        destroy_method: (str) | None = None
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


__all__ = [
    'Configuration',
    'Bean',
]
