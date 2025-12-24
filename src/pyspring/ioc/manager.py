import importlib
import inspect
import pkgutil
import re
import types as _types
import typing as _typing
import yaml
from pathlib import Path
from pyspring.interfaces.ISingleton import ISingletonService
from pyspring.ioc.container import DynamicContainer
from pyspring.log.loguru.ins import logger
from typing import Any, get_origin, get_args, get_type_hints, List, Dict


class AppContainerManager(ISingletonService):
    """
    应用容器管理器（即 IoC 容器管理单例）
    负责注入src/ref/repositories和src/ref/services下的所有服务
    """
    logger = None
    _initialized = False
    _config_cache = None  # 类级别配置缓存
    _instance = None  # 单例实例

    def __new__(cls):
        """确保单例模式"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        """
        初始化容器管理器（只执行一次）
        """
        if not AppContainerManager._initialized:
            self.container = DynamicContainer()
            # 接口到实现的映射（扫描阶段填充）
            self._interface_impl_map: dict[type, type] = {}
            # 已注册的服务名称集合（避免重复注册）
            self._registered_services: set[str] = set()
            # 加载配置（只加载一次）
            self._config = self._load_config()
            AppContainerManager._initialized = True

    @staticmethod
    def generate_name(service_class: type):
        return re.sub(r'(?<!^)(?=[A-Z])', '_', service_class.__name__).lower()

    def _load_config(self) -> Dict[str, Any]:
        """
        加载 IoC 容器配置文件（带缓存）
        
        Returns:
            配置字典，如果配置文件不存在则返回默认配置
        """
        # ✅ 如果已有缓存，直接返回
        if AppContainerManager._config_cache is not None:
            return AppContainerManager._config_cache
            
        # 查找配置文件路径
        possible_paths = [
            Path.cwd() / 'config' / 'container.yaml',
            Path(__file__).parent.parent.parent.parent / 'config' / 'container.yaml',
            Path.cwd() / 'container.yaml',
        ]

        for config_path in possible_paths:
            if config_path.exists():
                try:
                    with open(config_path, 'r', encoding='utf-8') as f:
                        config = yaml.safe_load(f) or {}
                        logger.debug(f"✅ 已加载 IoC 容器配置: {config_path}")
                        AppContainerManager._config_cache = config  # ✅ 缓存配置
                        return config
                except Exception as e:
                    logger.error(f"❌ 加载配置文件失败: {config_path}, 错误: {e}")

        # 返回默认配置
        logger.debug("⚠️ 未找到配置文件，使用默认配置")
        default_config = {
            'scan': {
                'packages': [
                    'src.pyspring.repositories',
                    'src.pyspring.security',
                    'src.pyspring.system',
                    'src.pyspring.log',
                ],
                'recursive': True,
                'service_suffix': 'Service'
            },
            'container': {
                'lazy_loading': True,
                'auto_interface_mapping': True,
                'debug': False
            }
        }
        AppContainerManager._config_cache = default_config  # ✅ 缓存默认配置
        return default_config

    def get_scan_packages(self) -> List[str]:
        """
        获取需要扫描的包路径列表
        
        自动标准化包路径：
        - 如果配置中是 'src.pyspring.*'，会尝试导入
        - 如果失败，自动转换为 'pyspring.*'（适用于已安装的包）
        
        Returns:
            包路径列表
        """
        packages = self._config.get('scan', {}).get('packages', [])
        normalized_packages = []

        for pkg in packages:
            # 先尝试导入完整的包路径（至少前两级，如 src.pyspring）
            try:
                # 尝试导入包的前两级（如 src.pyspring）
                test_pkg = '.'.join(pkg.split('.')[:2]) if '.' in pkg else pkg
                importlib.import_module(test_pkg)
                normalized_packages.append(pkg)
                logger.debug(f"✅ 路径有效: {pkg}")
            except ImportError as e:
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
                        logger.debug(f"⚠️ 路径无法标准化: {pkg} (原因: {e}, {e2})")
                        normalized_packages.append(pkg)
                else:
                    logger.debug(f"⚠️ 路径导入失败: {pkg} (原因: {e})")
                    normalized_packages.append(pkg)

        return normalized_packages

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
            self.scan_and_register_services(package_path)

        logger.debug("🔧 所有服务注册完成")
        return self.container

        # # 将容器管理器本身注册到容器中，确保一致性
        # self.container.bind_singleton(self.generate_name(AppContainerManager), AppContainerManager)
        #
        # # 注册系统服务（单例模式）
        # # SystemService管理环境变量等全局状态，应保持单例
        # self.container.bind_singleton(self.generate_name(SystemService), SystemService)
        #
        # # 注册基础缓存服务（单例）
        # # CacheManagerService管理重量级资源（Redis连接等），应保持单例
        # self.container.bind_singleton(self.generate_name(CacheManagerService), CacheManagerService)
        #
        # # 注册样式服务（工厂模式，因为它需要缓存服务依赖）
        # # StyleService是无状态服务，每次请求创建新实例更安全
        # self.container.bind_factory(self.generate_name(StyleService), StyleService,
        #                             cache=lambda: self.service(CacheManagerService))
        #
        # return self.container

    def scan_and_register_services(self, base_package: str):
        """
        扫描并注册服务

        扫描规则：
        - 扫描以 'Service' 结尾的类（如 DBManagerService）
        - 扫描以 'Handler' 结尾的类（如 DBShutdownHandler、CacheShutdownHandler）        - 扫描以 'Initializer' 结尾的类（如 CacheInitializer、DBInitializer）        - 跳过抽象类（用于接口映射）
        
        Args:
            base_package: 基础包名，如 "src.pyspring.repositories"
        """
        try:
            # 导入基础包
            package = importlib.import_module(base_package)

            # 使用pkgutil递归扫描所有子模块
            for importer, modname, ispkg in pkgutil.walk_packages(
                    path=package.__path__,
                    prefix=package.__name__ + ".",
                    onerror=lambda x: None
            ):
                try:
                    # 导入模块
                    module = importlib.import_module(modname)

                    # 查找服务类、处理器类和初始化器类
                    for name, obj in vars(module).items():
                        # 检查是否为类，且以 Service/Handler/Initializer 结尾，且在当前模块定义
                        if isinstance(obj, type) and obj.__module__ == modname:
                            # 匹配 Service/Handler/Initializer 结尾的类
                            if name.endswith('Service') or name.endswith('Handler') or name.endswith('Initializer'):
                                # 仅跳过抽象接口类（不注册），但用于接口->实现映射
                                if inspect.isabstract(obj):
                                    continue
                                # 记录接口->实现映射（基于 MRO 查找抽象父类）
                                for base in obj.__mro__[1:]:
                                    if isinstance(base, type) and inspect.isabstract(base):
                                        # 映射抽象基类到实现类
                                        if base.__name__.endswith('Service') or base.__name__.endswith('Handler') or base.__name__.endswith('Initializer'):
                                            self._interface_impl_map.setdefault(base, obj)
                                # 根据类的特征决定注册方式
                                self.register_service_by_convention(obj)
                except Exception as e:
                    logger.debug(f"Warning: Could not process module {modname}: {e}")
        except ImportError as e:
            logger.debug(f"Error importing base package {base_package}: {e}")

    @staticmethod
    def unwrap_annotation(ann: Any):
        """将 typing 注解还原为真实类型（支持 Annotated、Optional/Union、ForwardRef）。
        安全实现：不做任何奇怪的 get_args 非法用法，避免 list index out of range。
        """
        try:
            origin = get_origin(ann)
            if origin is None:
                # 可能是 ForwardRef 或已是类型
                if isinstance(ann, str):
                    # 留给调用方用 module_globals 解析或按名称兜底
                    return None
                return ann

            # Annotated[T, ...]
            # 在 3.12 中，origin 可能是 typing.Annotated
            if str(origin).endswith('Annotated') or origin is getattr(_typing, 'Annotated', None):
                args = get_args(ann)
                return args[0] if args else None

            # Union[...] / Optional[T]，支持 typing.Union 和 PEP604 的 X | Y
            if origin is getattr(_typing, 'Union', None) or origin is getattr(_types, 'UnionType', None):
                args = [a for a in get_args(ann) if a is not type(None)]  # noqa: E721
                return args[0] if args else None

            # 其他泛型原样返回（如 List[T] 等），由上层按类型名/接口映射处理
            return ann
        except Exception as e:
            logger.error(f"🚨 {e}")
            return ann

    def register_service_by_convention(self, service_class):
        """
        根据约定注册服务

        Args:
            service_class: 服务类
        """
        service_name = self.generate_name(service_class)

        # 检查是否已经注册过，避免重复注册
        if service_name in self._registered_services:
            # logger.debug(f"Service {service_name} already registered, skipping...")
            return

        # ✅ 立即标记为已注册，防止递归依赖解析时重复注册
        self._registered_services.add(service_name)

        sig = inspect.signature(service_class.__init__)
        try:
            module_globals = vars(importlib.import_module(service_class.__module__))
            hints = get_type_hints(service_class.__init__, globalns=module_globals, include_extras=True)
        except Exception as e:
            # 类型解析失败不是致命错误，我们可以通过参数名来匹配依赖
            logger.debug(f"Type hints resolution failed for {service_class.__name__}: {e}")
            module_globals = {}
            hints = {}
        dependencies = {}

        for param_name, param in sig.parameters.items():
            if param_name == 'self':
                continue

            ann = hints.get(param_name, param.annotation)
            raw = None
            if ann != inspect.Parameter.empty:
                raw = self.unwrap_annotation(ann)
                if raw is None and isinstance(param.annotation, str):
                    raw = module_globals.get(param.annotation)
            type_name = raw.__name__ if hasattr(raw, '__name__') else (str(raw) if raw is not None else str(param.annotation))
            logger.debug(f"Parameter: {param_name}, Type: {type_name}")

            injected = False

            # 1) 接口/抽象 -> 实现 映射（优先）
            try:
                if isinstance(raw, type) and (inspect.isabstract(raw) or 'interfaces' in getattr(raw, '__module__', '')):
                    impl = self._interface_impl_map.get(raw)
                    if impl:
                        impl_name = self.generate_name(impl)
                        # ✅ 确保实现类已注册（内部有重复检查保护）
                        if impl_name not in self._registered_services:
                            self.register_service_by_convention(impl)
                        # ✅ 获取 provider（延迟解析）
                        if impl_name in self.container._bindings:
                            dependencies[param_name] = self.container._bindings[impl_name]
                            injected = True
            except Exception as e:
                logger.debug(f"Interface mapping inject failed for {type_name}: {e}")

            if injected:
                continue

            # 2) 具体 Service 类型直接注入
            try:
                if isinstance(raw, type) and raw.__name__.endswith('Service') and not inspect.isabstract(raw):
                    raw_name = self.generate_name(raw)
                    # ✅ 确保服务已注册（内部有重复检查保护）
                    if raw_name not in self._registered_services:
                        self.register_service_by_convention(raw)
                    # ✅ 获取 provider（延迟解析）
                    if raw_name in self.container._bindings:
                        dependencies[param_name] = self.container._bindings[raw_name]
                        injected = True
            except Exception as e:
                logger.debug(f"Direct inject failed for {type_name}: {e}")

            if injected:
                continue

            # 3) 无注解或解析失败：按参数名从容器解析同名 provider
            try:
                # ✅ 从 _bindings 获取 provider
                if param_name in self.container._bindings:
                    dependencies[param_name] = self.container._bindings[param_name]
                    injected = True
            except Exception as e:
                logger.debug(f"Name-based inject failed for {param_name}: {e}")

            if injected:
                continue

            # 4) 尝试按参数名模糊匹配 Service（如 db_manager -> d_b_manager_service）
            try:
                # 参数名可能是 db_manager、cache_manager 等
                # 尝试转换为 service 名称：db_manager -> d_b_manager_service
                service_name_candidate = param_name + "_service"
                if service_name_candidate in self._registered_services:
                    # ✅ 从 _bindings 获取 provider
                    if service_name_candidate in self.container._bindings:
                        dependencies[param_name] = self.container._bindings[service_name_candidate]
                        injected = True
                        logger.debug(f"Fuzzy match inject success: {param_name} -> {service_name_candidate}")
            except Exception as e:
                logger.debug(f"Fuzzy match inject failed for {param_name}: {e}")

        # 单例/工厂注册
        if issubclass(service_class, ISingletonService):
            self.container.bind_singleton(service_name, service_class, **dependencies)
            logger.debug(f"Registered {service_name} as singleton service with dependencies: {list(dependencies.keys())}.")
        else:
            self.container.bind_factory(service_name, service_class, **dependencies)
            logger.debug(f"Registered {service_name} as factory service with dependencies: {list(dependencies.keys())}.")

        # 注意：服务已在方法开头标记为已注册，这里无需重复

    def register_service(self, service_class: type):
        """
        注册服务（按约定）
        """
        self.register_service_by_convention(service_class)

    # def register_service(self, service_class: type, name: str = None, dependencies: dict = None, singleton: bool = False):
    #     """
    #     注册自定义服。
    #
    #     Args:
    #         service_class: 服务类
    #         name: 服务名称，如果不提供则默认使用类名转换（驼峰转下划线小写。
    #         dependencies: 依赖项字。
    #         singleton: 是否为单例模。
    #     """
    #     # 如果没有提供名称，则根据类名自动生成
    #     if name is None:
    #         # 将类名从驼峰命名转换为下划线命名
    #         import re
    #         name = re.sub(r'(?<!^)(?=[A-Z])', '_', service_class.__name__).lower()
    #         # 移除可能的Service后缀，暂不需。
    #         # if name.endswith('_service'):
    #         #     name = name[:-8]
    #
    #     deps = dependencies or {}
    #     if singleton:
    #         self.container.bind_singleton(name, service_class, **deps)
    #     else:
    #         self.container.bind_factory(name, service_class, **deps)

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
        from pyspring.interfaces.IStartupInitializer import IStartupInitializer, StartupInitializerManager

        logger.info("🚀 开始执行启动初始化器...")

        try:
            # 创建初始化器管理器
            manager = StartupInitializerManager()

            # 自动发现所有实现了 IStartupInitializer 接口的服务
            # 类似 Java: List<IStartupInitializer> initializers = applicationContext.getBeansOfType(IStartupInitializer.class)
            startup_initializers = self.get_all_instances_of(IStartupInitializer)

            if not startup_initializers:
                logger.info("ℹ️  未发现任何启动初始化器")
                return True

            logger.info(f"🔍 发现 {len(startup_initializers)} 个启动初始化器")

            # 注册所有发现的初始化器
            for initializer in startup_initializers:
                manager.register(initializer)
                logger.debug(f"📝 已注册启动初始化器: {initializer.get_name()}")

            # 执行所有初始化器（失败时停止）
            success = await manager.execute_all(stop_on_failure=True)

            if not success:
                logger.error("❌ 启动初始化失败")
                raise RuntimeError("Startup initialization failed")

            logger.info("✅ 所有启动初始化器执行成功")
            return True

        except Exception as e:
            logger.error(f"🚨 启动初始化异常: {e}", exc_info=True)
            raise

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
        from pyspring.interfaces.IShutdownHandler import IShutdownHandler, ShutdownHandlerManager

        logger.info("🔄 开始执行关闭处理器...")

        try:
            # 创建关闭处理器管理器
            manager = ShutdownHandlerManager()

            # 自动发现所有实现了 IShutdownHandler 接口的服务
            # 类似 Java: List<IShutdownHandler> handlers = applicationContext.getBeansOfType(IShutdownHandler.class)
            shutdown_handlers = self.get_all_instances_of(IShutdownHandler)

            if not shutdown_handlers:
                logger.info("ℹ️  未发现任何关闭处理器")
                return True

            logger.info(f"🔍 发现 {len(shutdown_handlers)} 个关闭处理器")

            # 注册所有发现的处理器
            for handler in shutdown_handlers:
                manager.register(handler)
                logger.debug(f"📝 已注册关闭处理器: {handler.get_name()}")

            # 执行所有关闭处理器（不停止，确保所有资源都能清理）
            success = await manager.execute_all(stop_on_failure=False)

            if success:
                logger.info("✅ 所有关闭处理器执行成功")
            else:
                logger.warning("⚠️  部分关闭处理器执行失败")

            return success

        except Exception as e:
            logger.error(f"🚨 关闭处理异常: {e}", exc_info=True)
            return False
