"""
新版IOC容器

清晰、解耦、最佳实践的实现
"""
import inspect
from typing import Dict, Any, List, Callable, Optional

from pyspring.ioc.annotations.scope import Scope, get_scope
from pyspring.ioc.interfaces.core import ILifecycle
from pyspring.ioc.registry.registry import ServiceRegistry, ServiceDefinition
from pyspring.ioc.scanner.scanner import ComponentScanner, ComponentMetadata
from pyspring.log.instance import logger


class Container:
    """
    IOC容器
    
    新的设计理念：
    1. 职责单一：容器只负责协调，具体工作委托给专门模块
    2. 清晰分层：扫描 -> 注册 -> 解析 -> 实例化
    3. 可扩展：每个模块都可以独立扩展和替换
    
    工作流程：
    1. 扫描阶段（Scanner）：发现所有组件
    2. 注册阶段（Registry）：注册组件定义
    3. 实例化阶段（Resolver + Container）：解析依赖并创建实例
    """

    def __init__(self, enable_aop: bool = True):
        # 核心组件
        self.registry = ServiceRegistry()
        self._resolver = None  # 延迟初始化
        self.scanner = ComponentScanner()

        # 实例缓存（Singleton）
        self._singleton_instances: Dict[str, Any] = {}

        # 生命周期管理
        self._lifecycle_services: List[Any] = []
        self._initializer_manager: Optional[Any] = None
        self._shutdown_manager: Optional[Any] = None

        # AOP集成
        self._enable_aop = enable_aop
        self._aop_integration = None
        if enable_aop:
            from pyspring.ioc.aop.integration import AopIntegration
            self._aop_integration = AopIntegration(self)

        # Initializer/Shutdown管理器
        self._initializer_manager = None
        self._shutdown_manager = None

        # 状态标记
        self._initialized = False

    @property
    def resolver(self):
        if self._resolver is None:
            # 延迟导入解决循环依赖
            from pyspring.ioc.resolver.resolver import DependencyResolver
            self._resolver = DependencyResolver(self.registry)
        return self._resolver

    def scan(self, base_packages: List[str]):
        """
        扫描并注册组件
        
        Args:
            base_packages: 要扫描的包路径列表
        """
        logger.debug("🚀 启动IOC容器...")

        # 1. 扫描组件
        components = self.scanner.scan(base_packages)

        # 2. 输出所有被替换的组件（统一显示）
        skipped_count = 0
        for cls, metadata in components.items():
            if metadata.replaced_by:
                logger.info(
                    f"⏩ 跳过条件组件 {metadata.name} ({cls.__name__}): "
                    f"已被 {metadata.replaced_by} 替换"
                )
                skipped_count += 1

        if skipped_count > 0:
            logger.debug(f"已跳过 {skipped_count} 个被替换的条件组件\n")

        # 3. 注册组件
        logger.debug(f"📝 注册组件...")
        for cls, metadata in components.items():
            self._register_component(metadata)

        # 3. 注册Bean
        for cls, metadata in components.items():
            if metadata.is_configuration:
                self._register_beans(metadata)

        logger.debug(f"✅ IOC容器初始化完成，已注册 {len(self.registry.all_names())} 个服务")
        self._initialized = True

    def _register_component(self, metadata: ComponentMetadata):
        """注册普通组件"""
        cls = metadata.cls
        scope = get_scope(cls)

        # 检查是否被其他组件替换（基于继承的替换）
        if metadata.replaced_by:
            # 已在 scan() 方法中统一输出，这里直接跳过
            return

        # 获取条件类型（用于判断是否是条件组件）
        conditional_type = getattr(cls, "__pyspring_conditional_on_missing_bean__", None)
        is_conditional = conditional_type is not None

        # 如果当前组件替换了其他组件，输出替换日志（紧接着注册日志）
        if metadata.replaces:
            logger.info(
                f"  🔄 组件替换: {metadata.name} ({cls.__name__}) "
                f"替换 {metadata.replaces}"
            )

        # 创建工厂函数
        def factory():
            return self._create_instance(metadata.name)

        # 创建服务定义
        definition = ServiceDefinition(
            name=metadata.name,
            service_type=cls,
            scope=scope,
            factory=factory,
            is_lazy=metadata.is_lazy,
            is_primary=metadata.is_primary,
            is_conditional=is_conditional,
            replaces=metadata.replaces,  # 🆕 传递替换信息
            module=metadata.module
        )

        # 注册
        self.registry.register(definition)

        # 注册成功日志（紧跟在替换日志后面）
        logger.debug(f"  ✅ {metadata.name} ({scope.value}){' [conditional]' if is_conditional else ''}")

    def _register_beans(self, config_metadata: ComponentMetadata):
        """注册配置类中的Bean"""
        config_cls = config_metadata.cls
        config_name = config_metadata.name

        logger.debug(f"📦 注册配置类 {config_cls.__name__} 的Bean (共{len(config_metadata.bean_methods)}个)")

        # 先确保配置类自己被注册
        if not self.registry.has(config_name):
            self._register_component(config_metadata)

        # 注册每个Bean方法
        for method_name in config_metadata.bean_methods:
            logger.debug(f"  🌱 注册Bean方法: {method_name}")
            self._register_bean_method(config_cls, config_name, method_name)

    def _register_bean_method(self, config_cls: type, config_name: str, method_name: str):
        """注册单个Bean方法"""
        method = getattr(config_cls, method_name)

        # 获取返回类型
        return_type = method.__annotations__.get('return')
        if not return_type:
            logger.warning(f"⚠️ Bean方法 {method_name} 缺少返回类型注解")
            return

        # 确定Bean名称
        bean_name = getattr(method, "__pyspring_bean_name__", None)
        if not bean_name:
            if isinstance(return_type, type):
                bean_name = self._generate_name(return_type)
            else:
                bean_name = method_name

        # logger.debug(f"📝 准备注册Bean: {bean_name} (方法: {method_name}, 返回类型: {return_type})")

        # 检查条件注册
        conditional_type = getattr(method, "__pyspring_conditional_on_missing_bean__", None)
        if conditional_type:
            if self.registry.has_type(conditional_type):
                logger.debug(f"⏩ 跳过Bean {bean_name}：{conditional_type.__name__} 已存在")
                return

        # 创建Bean工厂
        def bean_factory():
            # 1. 获取配置类实例
            config_instance = self.get(config_name)

            # 2. 解析Bean方法的依赖
            bean_method = getattr(config_instance, method_name)
            bean_deps = self._resolve_bean_method_dependencies(bean_method)

            # 3. 调用Bean方法
            return bean_method(**bean_deps)

        # 创建服务定义
        definition = ServiceDefinition(
            name=bean_name,
            service_type=return_type if isinstance(return_type, type) else object,
            scope=Scope.SINGLETON,  # Bean默认是单例
            factory=bean_factory,
            is_bean=True,
            config_class=config_cls,
            bean_method=method_name
        )

        # 注册
        self.registry.register(definition)
        logger.debug(f"  🌱 Bean: {bean_name} (from {config_cls.__name__}.{method_name})")

    def _resolve_bean_method_dependencies(self, method: Callable[..., Any]) -> Dict[str, Any]:
        """解析Bean方法的依赖"""
        sig = inspect.signature(method)
        dependencies = {}

        for param_name, param in sig.parameters.items():
            if param_name == 'self':
                continue

            # 尝试通过参数名获取服务
            if self.registry.has(param_name):
                dependencies[param_name] = self.get(param_name)
                continue

            # 尝试通过类型获取服务
            param_type = param.annotation
            if param_type != inspect.Parameter.empty:
                service_def = self.registry.get_by_type(param_type)
                if service_def:
                    dependencies[param_name] = self.get(service_def.name)

        return dependencies

    def get(self, name: str) -> Any:
        """
        获取服务实例
        
        Args:
            name: 服务名称
            
        Returns:
            服务实例
        """
        # 检查是否已注册
        service_def = self.registry.get(name)
        if not service_def:
            raise ValueError(f"服务 '{name}' 未注册")

        # 单例模式：检查缓存
        if service_def.scope == Scope.SINGLETON:
            if name in self._singleton_instances:
                return self._singleton_instances[name]

        # 创建实例
        instance = self._create_instance(name)

        # 缓存单例
        if service_def.scope == Scope.SINGLETON:
            self._singleton_instances[name] = instance

        return instance

    def _create_instance(self, name: str) -> Any:
        """
        创建服务实例
        
        Args:
            name: 服务名称
            
        Returns:
            服务实例
        """
        service_def = self.registry.get(name)
        if not service_def:
            raise ValueError(f"服务 '{name}' 未注册")

        try:
            # 如果是Bean，直接调用工厂
            if service_def.is_bean:
                instance = service_def.factory()
            else:
                # 解析依赖
                from pyspring.ioc.resolver.resolver import DependencyResolver
                dependencies = DependencyResolver(self.registry).resolve_dependencies(service_def, self)

                # 实例化
                instance = service_def.service_type(**dependencies)

            # AOP代理
            if self._aop_integration:
                instance = self._aop_integration.create_proxy(instance, service_def.service_type)

            # 生命周期回调
            if isinstance(instance, ILifecycle):
                self._lifecycle_services.append(instance)

            return instance

        except Exception as e:
            logger.error(f"❌ 实例化服务失败 {name}: {e}")
            raise

    def get_by_type(self, service_type: type) -> Any:
        """根据类型获取服务实例"""
        service_def = self.registry.get_by_type(service_type)
        if service_def:
            return self.get(service_def.name)

        # 尝试接口查询
        impl_def = self.registry.get_primary_implementation(service_type)
        if impl_def:
            return self.get(impl_def.name)

        raise ValueError(f"未找到类型 '{service_type.__name__}' 的服务")

    def get_all_of_type(self, service_type: type) -> List[Any]:
        """获取某类型的所有实现"""
        impl_defs = self.registry.get_implementations(service_type)
        return [self.get(impl_def.name) for impl_def in impl_defs]

    def get_all_instances_of(self, service_type: type) -> List[Any]:
        """获取某类型的所有实例（别名方法）"""
        return self.get_all_of_type(service_type)

    def has(self, name: str) -> bool:
        """检查服务是否已注册"""
        return self.registry.has(name)

    def get_service(self, service_type: type) -> Any:
        """
        根据类型获取服务实例（用于HealthCheckManager）
        
        Args:
            service_type: 服务类型
            
        Returns:
            服务实例
        """
        return self.get_by_type(service_type)

    def get_all_registered_types(self) -> List[type]:
        """
        获取所有已注册的服务类型（用于自动发现）
        
        Returns:
            服务类型列表
        """
        return self.registry.all_types()

    async def initialize_lifecycle_services(self):
        """初始化所有实现了ILifecycle的服务"""
        logger.debug("🔧 初始化生命周期服务...")

        # 1. 初始化Initializer管理器
        from pyspring.ioc.lifecycle.initializer import StartupInitializerManager
        self._initializer_manager = StartupInitializerManager(self)
        self._initializer_manager.discover()

        # 2. 执行所有Initializer
        await self._initializer_manager.execute_all()

        # 3. 初始化其他生命周期服务
        for service in self._lifecycle_services:
            # 跳过Initializer（已经执行过）
            from pyspring.ioc.lifecycle.initializer import IStartupInitializer
            if isinstance(service, IStartupInitializer):
                continue
                
            try:
                await service.on_startup()
                logger.debug(f"  ✅ {service.__class__.__name__}")
            except Exception as e:
                logger.error(f"  ❌ {service.__class__.__name__}: {e}")

    async def shutdown_lifecycle_services(self):
        """关闭所有实现了ILifecycle的服务"""
        logger.debug("🔄 关闭生命周期服务...")

        # 1. 初始化Shutdown管理器
        from pyspring.ioc.lifecycle.shutdown import ShutdownHandlerManager
        self._shutdown_manager = ShutdownHandlerManager(self)
        self._shutdown_manager.discover()

        # 2. 先关闭其他生命周期服务
        for service in reversed(self._lifecycle_services):  # 反向关闭
            # 跳过ShutdownHandler（最后执行）
            from pyspring.ioc.lifecycle.shutdown import IShutdownHandler
            if isinstance(service, IShutdownHandler):
                continue
                
            try:
                await service.on_shutdown()
                logger.debug(f"  ✅ {service.__class__.__name__}")
            except Exception as e:
                logger.error(f"  ❌ {service.__class__.__name__}: {e}")

        # 3. 最后执行所有ShutdownHandler
        await self._shutdown_manager.execute_all()

    @staticmethod
    def _generate_name(cls: type) -> str:
        """生成服务名称（CamelCase -> snake_case）"""
        import re
        name = cls.__name__
        name = re.sub(r'(?<!^)(?=[A-Z])', '_', name).lower()
        return name


__all__ = ['Container']
