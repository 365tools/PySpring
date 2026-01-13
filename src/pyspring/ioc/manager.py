import importlib
import inspect
import json
import pkgutil
import re
import types as _types
import typing as _typing
from pathlib import Path
from typing import Any, get_origin, get_args, get_type_hints, List, Dict

import yaml

from pyspring.aop.core import Aspect
from pyspring.aop.proxy import create_proxy
from pyspring.core.interfaces.IService import IService
from pyspring.ioc.container import DynamicContainer
from pyspring.ioc.validator import IoCValidator
from pyspring.log.instance import logger


class AppContainerManager:
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
        # 加载配置（只加载一次）
        self._config = self._load_config()
        self._initialized = True

    @staticmethod
    def generate_name(service_class: type):
        return re.sub(r'(?<!^)(?=[A-Z])', '_', service_class.__name__).lower()

    @staticmethod
    def _load_config() -> Dict[str, Any]:
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
                    'pyspring.repositories',
                    'pyspring.security',
                    'pyspring.log',
                ],
                'recursive': True,
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
            self.scan_and_register_services(package_path)

        # 检测循环依赖
        try:
            IoCValidator.validate_dependencies(self._service_dependencies)
        except Exception as e:
            # 严重错误，直接抛出，阻止容器启动
            logger.error(f"❌ Circular dependency detected: {e}")
            raise e

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

    CACHE_DIR = Path(".pyspring_cache")

    @staticmethod
    def get_package_mtime(package_path_list: List[str]) -> float:
        """获取包路径下最新的修改时间"""
        max_mtime = 0.0
        for path_str in package_path_list:
            path = Path(path_str)
            if not path.exists(): continue
            if path.is_file():
                mtime = path.stat().st_mtime
                if mtime > max_mtime: max_mtime = mtime
            else:
                for p in path.rglob("*.py"):
                    mtime = p.stat().st_mtime
                    if mtime > max_mtime:
                        max_mtime = mtime
        return max_mtime

    def scan_and_register_services(self, base_package: str = "pyspring"):
        """
        扫描并注册服务

        扫描规则：
        - 类被 @Component (或 @Service, @Repository) 装饰
        - 类实现了 IService 接口
        - 跳过抽象类（用于接口映射）
        
        Args:
            base_package: 基础包名，如 "pyspring.repositories"
        """
        try:
            # 导入基础包
            package = importlib.import_module(base_package)

            # --- 缓存逻辑 ---
            cache_enabled = self._config.get('container', {}).get('scan_cache', True)
            path_list = getattr(package, '__path__', [])
            if not path_list and getattr(package, '__file__', None):
                # 处理单文件模块的情况
                path_list = [package.__file__]

            cache_modules = None
            current_mtime = 0.0

            if cache_enabled and path_list:
                try:
                    current_mtime = self.get_package_mtime(path_list)
                    cache_file = self.CACHE_DIR / f"{base_package}.json"
                    if cache_file.exists():
                        with open(cache_file, 'r') as f:
                            data = json.load(f)
                            if abs(data.get('mtime', 0) - current_mtime) < 0.001:
                                cache_modules = data.get('modules')
                                logger.debug(f"🚀 Using scan cache for {base_package}")
                except Exception as e:
                    logger.warning(f"Cache load failed: {e}")

            # 命中缓存：直接加载指定模块
            if cache_modules is not None:
                for modname in cache_modules:
                    try:
                        m = importlib.import_module(modname)
                        self._scan_module(m)
                    except Exception:
                        pass
                return

            # --- 未命中缓存：执行完整扫描 ---
            useful_modules = []

            # 如果是单个模块文件而不是包，直接扫描该模块
            if not hasattr(package, '__path__'):
                if self._scan_module(package):
                    useful_modules.append(package.__name__)
            else:
                # 使用pkgutil递归扫描所有子模块
                for importer, modname, ispkg in pkgutil.walk_packages(
                        path=package.__path__,
                        prefix=package.__name__ + ".",
                        onerror=lambda x: None
                ):
                    try:
                        # 导入模块
                        module = importlib.import_module(modname)
                        if self._scan_module(module):
                            useful_modules.append(modname)
                    except Exception as e:
                        logger.error(f"Warning: Could not process module {modname}: {e}")

            # --- 保存缓存 ---
            if cache_enabled and path_list and useful_modules:
                try:
                    self.CACHE_DIR.mkdir(exist_ok=True)
                    with open(self.CACHE_DIR / f"{base_package}.json", 'w') as f:
                        json.dump({'mtime': current_mtime, 'modules': useful_modules}, f)
                        logger.debug(f"💾 Saved scan cache for {base_package}")
                except Exception:
                    pass

        except ImportError as e:
            logger.debug(f"Error importing base package {base_package}: {e}")

    def _scan_module(self, module) -> bool:
        """扫描单个模块中的类
        Returns:
            bool: 是否发现了有效的组件（Service/Aspect等）
        """
        found_any = False
        try:
            # 查找服务类
            from pyspring.core.interfaces.IService import IService

            for name, obj in vars(module).items():
                # 检查是否为类，且在当前模块定义
                if isinstance(obj, type) and obj.__module__ == module.__name__:
                    # --- 检测切面 ---
                    # 只要继承了 Aspect 或者是被 @aspect 装饰
                    if (issubclass(obj, Aspect) and obj is not Aspect) or hasattr(obj, "__pyspring_aspect__"):
                        try:
                            # 实例化切面
                            aspect_instance = obj()
                            self._aspects.append(aspect_instance)
                            logger.debug(f"📐 Found Aspect: {name}")
                            found_any = True
                        except Exception as e:
                            logger.error(f"Failed to instantiate aspect {name}: {e}")
                        
                        
                    is_decorated = hasattr(obj, "__pyspring_component__")

                    # 判定逻辑：
                    # 1. 有装饰器
                    # 2. 是 IService 的子类 (但排除 IService 本身)

                    # 检查是否为 IService 子类 (需要处理 Protocol 的特殊性)
                    is_service_subclass = False
                    try:
                        # 排除 IService 本身
                        if obj is not IService and issubclass(obj, IService):
                            is_service_subclass = True
                    except TypeError:
                        pass

                    if is_decorated or is_service_subclass:
                        # 仅跳过抽象接口类（不注册），但用于接口->实现映射
                        if inspect.isabstract(obj):
                            # 对抽象类也进行接口映射检查（如果它继承了 IService）
                            if is_service_subclass:
                                self._interface_impl_map.setdefault(obj, None)  # 仅作为一种标记或者后续扩展，目前逻辑主要在子类注册时查找基类
                            continue

                        # 记录接口->实现映射（基于 MRO 查找抽象父类）
                        for base in obj.__mro__[1:]:
                            if isinstance(base, type) and inspect.isabstract(base):
                                # 映射抽象基类到实现类 - 只要是实现了 IService 的抽象类都作为接口处理
                                if issubclass(base, IService):
                                    self._interface_impl_map.setdefault(base, obj)
                        # 根据类的特征决定注册方式
                        self.register_service_by_convention(obj)
                        found_any = True
        except Exception as e:
            logger.error(f"Error scanning module {module.__name__}: {e}")

        return found_any

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
        # Check for overrides from decorator
        override_name = getattr(service_class, "__pyspring_name__", None)
        service_name = override_name if override_name else self.generate_name(service_class)

        # 检查是否已经注册过，避免重复注册
        if service_name in self._registered_services:
            return

        # ✅ 立即标记为已注册，防止递归依赖解析时重复注册
        self._registered_services.add(service_name)

        sig = inspect.signature(service_class.__init__)

        # 获取类型提示
        try:
            module_globals = vars(importlib.import_module(service_class.__module__))
            hints = get_type_hints(service_class.__init__, globalns=module_globals, include_extras=True)
        except Exception:
            module_globals = {}
            hints = {}

        dependencies = {}
        dep_names = []  # 用于循环依赖检测

        for param_name, param in sig.parameters.items():
            if param_name == 'self':
                continue

            ann = hints.get(param_name, param.annotation)
            raw = None
            if ann != inspect.Parameter.empty:
                raw = self.unwrap_annotation(ann)
                if raw is None and isinstance(param.annotation, str):
                    raw = module_globals.get(param.annotation)

            # --- 依赖解析逻辑 ---
            resolved_name = None
            provider = None

            # 1) 接口/抽象 -> 实现
            if not resolved_name:
                try:
                    if isinstance(raw, type) and (inspect.isabstract(raw) or 'interfaces' in getattr(raw, '__module__', '')):
                        impl = self._interface_impl_map.get(raw)
                        if impl:
                            impl_name = self.generate_name(impl)
                            if impl_name not in self._registered_services:
                                self.register_service_by_convention(impl)
                            if self.container.has_binding(impl_name):
                                resolved_name = impl_name
                                provider = self.container.get_provider(impl_name)
                except Exception:
                    pass

            # 2) 具体 Service 类型
            if not resolved_name:
                try:
                    is_pyspring_component = False
                    if isinstance(raw, type):
                        if hasattr(raw, "__pyspring_component__"):
                            is_pyspring_component = True
                        elif raw is not IService and issubclass(raw, IService):
                            is_pyspring_component = True

                    if is_pyspring_component and not inspect.isabstract(raw):
                        raw_name = getattr(raw, "__pyspring_name__", None) or self.generate_name(raw)
                        if raw_name not in self._registered_services:
                            self.register_service_by_convention(raw)
                        if self.container.has_binding(raw_name):
                            resolved_name = raw_name
                            provider = self.container.get_provider(raw_name)
                except Exception:
                    pass

            # 3) 参数名
            if not resolved_name:
                try:
                    if self.container.has_binding(param_name):
                        resolved_name = param_name
                        provider = self.container.get_provider(param_name)
                except Exception:
                    pass

            if resolved_name and provider:
                dependencies[param_name] = provider
                dep_names.append(resolved_name)
                logger.debug(f"  - Injected dependency '{param_name}': {resolved_name}")
            else:
                # Optional parameters logic could go here
                if param.default == inspect.Parameter.empty:
                    logger.warning(f"  ⚠️ Missing dependency for '{service_name}': {param_name}")

        # 记录依赖关系
        self._service_dependencies[service_name] = dep_names

        # 绑定服务工厂
        # 使用闭包捕获 dependencies 和切面
        def service_factory():
            # 1. 解析所有依赖
            resolved_deps = {k: v() for k, v in dependencies.items()}
            # 2. 创建实例
            instance = service_class(**resolved_deps)
            # 3. 创建代理 (AOP)
            if self._aspects:
                instance = create_proxy(instance, self._aspects)
            return instance

        # 判断作用域 (默认为 Singleton)
        # TODO: 支持 Prototype scope if needed via decorator? 
        # For now assume Singleton for all Services as per PySpring design usually
        self.container.bind_factory(service_name, service_factory, cache_result=True)
        logger.debug(f"✅ Registered service: {service_name}")


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
        from pyspring.core.interfaces.initializer.startup import IStartupInitializer, StartupInitializerManager

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
        from pyspring.core.interfaces.handler.shutdown import IShutdownHandler, ShutdownHandlerManager

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
