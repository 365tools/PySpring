"""
Dependency Injector 使用说明

dependency_injector 是一个用于 Python 的依赖注入框架，主要包含以下组件：

1. containers: 容器模块，用于定义和组织 providers
   - DeclarativeContainer: 声明式容器，用于定义静态依赖关系
   - DynamicContainer: 动态容器，可在运行时添加/删除 providers

2. providers: 提供者模块，用于创建和管理对象实例
   - Singleton: 单例模式，整个应用中只创建一次实例
   - Factory: 工厂模式，每次请求都创建新实例
   - Configuration: 配置提供者，用于管理配置项
   - Callable: 可调用对象提供者
   - Object: 对象提供者，直接提供已有对象实例
"""
from dependency_injector import containers, providers


class Container(containers.DeclarativeContainer):
    """
    声明式容器示例
    
    适用于依赖关系相对固定的应用，所有 providers 在类定义时就确定下来
    """
    # # 1. 容器配置
    # config = providers.Configuration(pydantic_settings=[settings])
    #
    # # 2. 数据库连接 (使用 Singleton 模式)
    # # Singleton: 整个应用程序生命周期中只会创建一次实例，之后的所有请求都会返回同一个实例
    # # 适用于: 数据库连接、配置对象、日志记录器等只需要一个实例的场景
    # db_session = providers.Singleton(
    #     'SessionMaker',  # 使用字符串引用以便动态导入
    #     url=config.database_url
    # )
    #
    # # 3. Repository Bean (使用 Factory 模式)
    # # Factory: 每次请求都会创建一个新的实例
    # # 适用于: 业务服务、仓库等需要独立状态或每次都需要新实例的场景
    # chat_repository = providers.Factory(
    #     'app.repositories.ChatRepository',  # 使用字符串引用
    #     session_factory=db_session
    # )
    #
    # # 4. Service Bean (使用 Factory 模式)
    # # Factory: 保证每次获取服务时都能得到一个干净的实例，避免状态污染
    # chat_service = providers.Factory(
    #     'app.services.ChatService',  # 使用字符串引用
    #     repo=chat_repository
    # )
    pass


# 完全动态绑定版本
class DynamicContainer:
    """
    动态容器示例
    
    适用于依赖关系在运行时才能确定的应用，可以动态添加 providers
    """

    def __init__(self):
        self.container = containers.DynamicContainer()
        self._bindings = {}

    def bind_singleton(self, name, class_or_factory, **dependencies):
        """绑定单例服务
        
        Singleton 特点:
        - 整个应用程序中只有一个实例
        - 第一次请求时创建实例，后续请求都返回同一实例
        - 适用于: 数据库连接、配置管理、缓存、日志记录器等全局唯一资源
        
        Args:
            name: 服务名称
            class_or_factory: 类、工厂函数或模块路径字符串
            **dependencies: 依赖项
        """
        # ✅ 防止重复绑定：如果已存在，直接返回（保护单例）
        if name in self._bindings:
            return self
            
        if isinstance(class_or_factory, str):
            # 字符串形式的类路径
            provider = providers.Singleton(class_or_factory, **dependencies)
        elif callable(class_or_factory):
            # 可调用对象（类或函数）
            provider = providers.Singleton(class_or_factory, **dependencies)
        else:
            raise ValueError("class_or_factory must be a string path or callable")

        # 将提供者添加到容器
        setattr(self.container, name, provider)
        self._bindings[name] = provider
        return self

    def bind_factory(self, name, class_or_factory, **dependencies):
        """绑定工厂服务
        
        Factory 特点:
        - 每次请求都会创建一个新的实例
        - 适用于: 业务服务、控制器、需要独立状态的对象等
        - 确保每次使用时都是干净的状态，避免副作用
        
        Args:
            name: 服务名称
            class_or_factory: 类、工厂函数或模块路径字符串
            **dependencies: 依赖项
        """
        # ✅ 防止重复绑定
        if name in self._bindings:
            return self
            
        if isinstance(class_or_factory, str):
            # 字符串形式的类路径
            provider = providers.Factory(class_or_factory, **dependencies)
        elif callable(class_or_factory):
            # 可调用对象（类或函数）
            provider = providers.Factory(class_or_factory, **dependencies)
        else:
            raise ValueError("class_or_factory must be a string path or callable")

        # 将提供者添加到容器
        setattr(self.container, name, provider)
        self._bindings[name] = provider
        return self

    def get(self, name):
        """动态获取服务实例
        
        Args:
            name: 服务名称
            
        Returns:
            服务实例 (根据绑定时的类型决定是单例还是工厂模式)
        """
        if name not in self._bindings:
            raise KeyError(f"Service '{name}' not bound")

        provider = self._bindings[name]
        return provider()

    def get_instances_of_type(self, interface_type: type) -> list:
        """获取所有实现了指定接口/基类的服务实例
        
        类似 Java 的反射机制，根据基类/接口获取所有实现类实例
        
        Args:
            interface_type: 接口或基类类型
            
        Returns:
            实现了该接口的所有服务实例列表
            
        Example:
            # 获取所有 IShutdownHandler 实现
            handlers = container.get_instances_of_type(IShutdownHandler)
            for handler in handlers:
                handler.shutdown()
        """
        instances = []
        # 创建键的副本，避免迭代时字典大小改变
        binding_names = list(self._bindings.keys())
        for name in binding_names:
            try:
                instance = self.get(name)
                # 检查实例是否是指定类型的子类
                if isinstance(instance, interface_type):
                    instances.append(instance)
            except Exception:
                # 跳过获取失败的服务
                continue
        return instances

    def get_container(self):
        """获取底层容器"""
        return self.container

# 使用示例:
# dynamic_container = DynamicContainer()
# # 绑定单例服务（如数据库连接）
# dynamic_container.bind_singleton('db_session', SessionMaker, url=settings.DATABASE_URL)
# # 绑定工厂服务（如业务服务）
# dynamic_container.bind_factory('chat_repository', ChatRepository, session_factory=dynamic_container.get('db_session'))
# dynamic_container.bind_factory('chat_service', ChatService, repo=dynamic_container.get('chat_repository'))
#
# # 动态获取服务
# service_name = "chat_service"  # 可以来自配置文件或运行时决定
# chat_service = dynamic_container.get(service_name)
