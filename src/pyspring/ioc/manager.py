import importlib
import re
from typing import Any, List, Dict

from pyspring.core.interfaces.ISingleton import ISingletonService
from pyspring.ioc.core.config import IoCConfigLoader
from pyspring.ioc.core.container import DynamicContainer
from pyspring.ioc.core.lifecycle import LifecycleManager
from pyspring.ioc.core.registrar import ServiceRegistrar
from pyspring.ioc.core.scanner import ModuleScanner
from pyspring.ioc.core.validator import IoCValidator
from pyspring.log.instance import logger


class AppContainerManager(ISingletonService):
    """
    应用容器管理器（即 IoC 容器管理单例）
    负责注入src/ref/repositories和src/ref/services下的所有服务
    """
    logger = None
    _config_cache = None  # 类级别配置缓存
    _instance = None      # 单例实例

    # 框架核心包列表 (始终扫描)
    FRAMEWORK_PACKAGES = [
        'pyspring.core',
        'pyspring.ioc',
        'pyspring.log',
        'pyspring.repositories',
        'pyspring.security',
    ]

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(AppContainerManager, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        """
        初始化容器管理器
        """
        if getattr(self, '_initialized', False):
            return

        self.container = DynamicContainer()
        # 接口到实现的映射（扫描阶段填充）
        self._interface_impl_map: dict[type, type] = {}
        # 已注册的服务名称集合（避免重复注册）
        self._registered_services: set[str] = set()
        # 服务依赖关系图 (name -> [dep_name])，用于检测循环依赖
        self._service_dependencies: Dict[str, List[str]] = {}
        # 已注册的切面
        self._aspects: List[Any] = []

        # 初始化核心组件
        self.registrar = ServiceRegistrar(
            container=self.container,
            interface_impl_map=self._interface_impl_map,
            registered_services=self._registered_services,
            service_dependencies=self._service_dependencies,
            aspects=self._aspects
        )
        self.scanner = ModuleScanner(self.registrar)
        self.lifecycle_manager = LifecycleManager(self.container)
        
        # 加载配置（只加载一次）
        self._config = IoCConfigLoader.load_config()
        self._initialized = True

    @staticmethod
    def generate_name(service_class: type):
        return re.sub(r'(?<!^)(?=[A-Z])', '_', service_class.__name__).lower()

    def get_scan_packages(self) -> List[str]:
        """
        获取需要扫描的包路径列表
        会自动合并 框架核心包 + 用户配置包
        
        自动标准化包路径：
        - 如果配置中是 'src.pyspring.*'，会尝试导入
        - 如果失败，自动转换为 'pyspring.*'（适用于已安装的包）
        
        Returns:
            包路径列表
        """
        # 1. 获取用户配置的包
        config_packages = self._config.get('scan', {}).get('packages') or []

        # 2. 合并框架核心包 (去重)
        all_packages = list(set(config_packages + self.FRAMEWORK_PACKAGES))
        
        normalized_packages = []

        for pkg in all_packages:
            # 先尝试导入完整的包路径（至少前两级，如 src.pyspring）
            try:
                # 尝试导入包的前两级（如 src.pyspring）
                # 只有当包名包含点时才分割，否则直接导入
                test_pkg = '.'.join(pkg.split('.')[:2]) if '.' in pkg else pkg
                importlib.import_module(test_pkg)
                normalized_packages.append(pkg)
                logger.debug(f"✅ 路径有效: {pkg}")
            except ImportError:
                # 框架包本身容错：如果是框架包且导入失败（可能模块不存在，如 pyspring.system），尝试忽略或记录
                # 但如果是用户包，或者是 src. 开头的，尝试标准化
                if pkg in self.FRAMEWORK_PACKAGES:
                    # 框架包如果导人失败，可能是因为项目结构调整或者该模块确实不存在
                    # 尝试检查是否是 'src.pyspring' 开发环境结构
                    try:
                        dev_pkg = f"src.{pkg}"
                        importlib.import_module('.'.join(dev_pkg.split('.')[:2]))
                        normalized_packages.append(dev_pkg)
                        logger.debug(f"✅ 框架开发环境路径有效: {dev_pkg}")
                        continue
                    except ImportError:
                        pass
                
                # 如果以 'src.' 开头且导入失败，尝试去掉 'src.' 前缀
                if pkg.startswith('src.'):
                    normalized_pkg = pkg[4:]  # 去掉 'src.'
                    try:
                        # 测试标准化后的路径
                        test_pkg = '.'.join(normalized_pkg.split('.')[:1])
                        importlib.import_module(test_pkg)
                        normalized_packages.append(normalized_pkg)
                        logger.debug(f"📝 路径标准化: {pkg} -> {normalized_pkg}")
                    except ImportError as e2:
                        # 两种方式都失败，保留原路径（稍后会记录错误）
                        logger.debug(f"⚠️ 路径无法标准化: {pkg} (原因: {e2})")
                        normalized_packages.append(pkg)
                else:
                    # 尝试加上 src. 前缀 (作为 fallback)
                    try:
                        normalized_pkg = f"src.{pkg}"
                        test_pkg = '.'.join(normalized_pkg.split('.')[:2]) if '.' in normalized_pkg else normalized_pkg
                        importlib.import_module(test_pkg)
                        normalized_packages.append(normalized_pkg)
                        logger.debug(f"📝 自动添加src前缀: {pkg} -> {normalized_pkg}")
                    except ImportError as e:
                        logger.debug(f"⚠️ 路径导入失败: {pkg} (原因: {e})")
                        # 如果是框架核心包且真的不存在，则不添加，避免扫描报错
                        if pkg not in self.FRAMEWORK_PACKAGES:
                            normalized_packages.append(pkg)

        return list(set(normalized_packages))

    def register_all_services(self):
        """
        注册所有服务到容器中
        """
        # 获取logger实例用于记录初始化过程
        logger.debug("Initializing AppContainerManager...")

        # 从配置文件获取扫描路径
        scan_packages = self.get_scan_packages()

        if not scan_packages:
            logger.warning("⚠️ 配置文件中未指定扫描包路径，将不会自动注册任何服务")
            return self.container

        logger.debug(f"📦 将扫描以下包路径: {scan_packages}")

        # 自动扫描并注册服务
        for package_path in scan_packages:
            logger.debug(f"🔍 扫描中: {package_path}")
            self.scanner.scan_and_register_services(package_path, self._config)

        # 检测循环依赖
        try:
            IoCValidator.validate_dependencies(self._service_dependencies)
        except Exception as e:
            # 严重错误，直接抛出，阻止容器启动
            logger.error(f"❌ Circular dependency detected: {e}")
            raise e

        logger.debug("🔧 所有服务注册完成")
        return self.container

    @staticmethod
    def service(service_class: type) -> Any:
        """
        获取指定名称的服务实例；若首次获取失败（依赖未就绪），则动态重解析依赖并刷新绑定后重试。
        同时支持接口解析：当传入抽象/接口类时，优先通过接口->实现映射解析为具体实现。
        """
        manager = AppContainerManager()

        # 若是接口/抽象，尝试解析到实现类
        target_class = service_class
        try:
            if inspect.isabstract(service_class) or 'interfaces' in getattr(service_class, '__module__', ''):
                impl = manager._interface_impl_map.get(service_class)
                if impl:
                    target_class = impl
        except Exception as e:
            logger.error(f"🚨 {e}")
            pass

        name = AppContainerManager.generate_name(target_class)

        # ✅ 首先检查是否已注册
        if name in manager._registered_services:
            try:
                return manager.container.get(name)
            except Exception as e:
                # 如果已注册但获取失败，说明有其他问题，直接抛出
                logger.error(f"🚨 Service {name} is registered but failed to get: {e}")
                raise

        # ✅ 未注册时才进行注册
        try:
            logger.debug(f"Service {name} not registered yet, registering now...")
            manager.register_service_by_convention(target_class)
            ser = manager.container.get(name)
            logger.debug(f"Get service {name} after registration: {ser}")
            return ser
        except Exception as e2:
            # 兼容接口名到实现 provider 名（如 i_stop_service -> stop_service）
            if name.startswith('i_'):
                alt_name = name[2:]
                try:
                    ser = manager.container.get(alt_name)
                    logger.debug(f"Get service alt {alt_name}: {ser}")
                    return ser
                except Exception as e:
                    logger.error(f"🚨 {e}")
                    pass
            logger.error(f"🚨 Failed to register and get service {name}: {e2}")
            raise

    def get(self, service_class_or_name):
        """
        获取服务实例（覆盖 IService.get，提供同步方法）
        支持接口解析：当传入抽象/接口类时，优先通过接口->实现映射解析为具体实现。
        
        Args:
            service_class_or_name: 服务类（支持接口类）或服务名称
            
        Returns:
            服务实例
        """
        manager = AppContainerManager()

        # 支持类或字符串
        if isinstance(service_class_or_name, str):
            name = service_class_or_name
            target_class = None
        else:
            # 若是接口/抽象，尝试解析到实现类
            target_class = service_class_or_name
            try:
                if inspect.isabstract(service_class_or_name) or 'interfaces' in getattr(service_class_or_name, '__module__', ''):
                    impl = manager._interface_impl_map.get(service_class_or_name)
                    if impl:
                        target_class = impl
            except Exception as e:
                logger.error(f"🚨 Interface resolution error: {e}")
                pass

            name = self.generate_name(target_class)

        # ✅ 如果已注册，直接获取
        if name in manager._registered_services:
            try:
                return manager.container.get(name)
            except Exception as e:
                logger.error(f"🚨 Service {name} is registered but failed to get: {e}")
                raise

        # ✅ 未注册时才进行注册
        if target_class is None:
            raise KeyError(f"Service '{name}' not registered and no class provided")

        try:
            logger.debug(f"Service {name} not registered yet, registering now...")
            manager.register_service_by_convention(target_class)
            ser = manager.container.get(name)
            logger.debug(f"Get service {name} after registration: {ser}")
            return ser
        except Exception as e2:
            # 兼容接口名到实现 provider 名（如 i_stop_service -> stop_service）
            if name.startswith('i_'):
                alt_name = name[2:]
                try:
                    ser = manager.container.get(alt_name)
                    logger.debug(f"Get service alt {alt_name}: {ser}")
                    return ser
                except Exception as e:
                    logger.error(f"🚨 {e}")
                    pass
            logger.error(f"🚨 Failed to register and get service {name}: {e2}")
            raise

    def get_container(self):
        """
        获取底层容器

        Returns:
            DynamicContainer: 动态容器实例
        """
        return self.container

    def get_all_instances_of(self, interface_type: type) -> list:
        """获取所有实现了指定接口的服务实例
        
        类似 Java 的反射机制，根据基类/接口获取所有实现类实例
        这是对 container.get_instances_of_type() 的便捷封装
        
        Args:
            interface_type: 接口或基类类型
            
        Returns:
            实现了该接口的所有服务实例列表
            
        Example:
            # 获取所有 IShutdownHandler 实现
            handlers = ioc_manager.get_all_instances_of(IShutdownHandler)
            for handler in handlers:
                await handler.shutdown()
        """
        return self.container.get_instances_of_type(interface_type)

    async def run_startup_initializers(self):
        """
        在 IoC 扫描完成后，执行所有启动初始化器
        
        使用自动发现机制，无需手动注册每个具体的 Initializer
        只要服务实现了 IStartupInitializer 接口并注册到 IoC 容器，就会被自动发现和执行
        
        这种方式类似 Java 的反射机制：
        - 添加新的 Initializer 时，只需要实现接口并注册到容器
        - 不需要修改此方法的代码
        
        Returns:
            bool: 是否所有初始化器都成功
            
        Raises:
            RuntimeError: 如果关键初始化器失败
        """
        return await self.lifecycle_manager.run_startup_initializers()

    async def run_shutdown_handlers(self):
        """
        在应用关闭时，执行所有关闭处理器
        
        使用自动发现机制，无需手动注册每个具体的 ShutdownHandler
        只要服务实现了 IShutdownHandler 接口并注册到 IoC 容器，就会被自动发现和执行
        
        这种方式类似 Java 的反射机制：
        - 添加新的 ShutdownHandler 时，只需要实现接口并注册到容器
        - 不需要修改此方法的代码
        
        Returns:
            bool: 是否所有关闭处理器都成功
        """
        return await self.lifecycle_manager.run_shutdown_handlers()
