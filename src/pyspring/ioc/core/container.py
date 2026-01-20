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
        - 适用于: 业务服务(Service)、数据访问对象(Repository)等需要保持无状态或状态独立的组件
        
        Args:
            name: 服务名称
            class_or_factory: 类、工厂函数或模块路径字符串
        """
        if isinstance(class_or_factory, str):
            provider = providers.Factory(class_or_factory, **dependencies)
        elif callable(class_or_factory):
            provider = providers.Factory(class_or_factory, **dependencies)
        else:
            raise ValueError("class_or_factory must be a string path or callable")

        setattr(self.container, name, provider)
        self._bindings[name] = provider
        return self

    def get_provider(self, name):
        """获取服务的 Provider"""
        return getattr(self.container, name)

    def bind_provider(self, name, provider):
        """直接绑定 Provider 对象"""
        setattr(self.container, name, provider)
        self._bindings[name] = provider

    def get(self, name):
        """获取服务实例"""
        provider = getattr(self.container, name)
        return provider()

    def wire(self, modules):
        """将容器中的服务注入到指定模块"""
        self.container.wire(modules=modules)

    def unwire(self):
        """取消注入"""
        self.container.unwire()

    def has_binding(self, name: str) -> bool:
        """检查是否已绑定指定名称的服务"""
        return name in self._bindings

    def get_instances_of_type(self, interface_type: type) -> list:
        """获取所有实现了指定接口的服务实例
        
        遍历当前容器中所有的 provider，检查其产生的对象是否是 interface_type 的实例
        注意：这会实例化所有尚未实例化的单例，请谨慎使用
        """
        instances = []
        for name, provider in self._bindings.items():
            try:
                # 获取实例（如果已经初始化，或者是单例）
                # 注意：对于 Factory，这将创建一个新实例，这可能不是预期的行为
                # 我们这里主要针对 Singleton 进行扫描
                if isinstance(provider, providers.Singleton):
                    instance = provider()
                    if isinstance(instance, interface_type):
                        instances.append(instance)
            except Exception:
                # 忽略实例化失败的服务
                pass
        return instances
