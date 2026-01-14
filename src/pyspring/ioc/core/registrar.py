import importlib
import inspect
import re
import types as _types
import typing as _typing
from typing import Any, get_origin, get_args, get_type_hints, List, Dict, Set

from pyspring.aop.core import Aspect
from pyspring.aop.proxy import create_proxy
from pyspring.core.abstracts.interfaces.IService import IService
from pyspring.log.instance import logger


class ServiceRegistrar:
    """服务注册器"""

    def __init__(self,
                 container: Any,
                 interface_impl_map: Dict[type, type],
                 registered_services: Set[str],
                 service_dependencies: Dict[str, List[str]],
                 aspects: List[Any]):
        self.container = container
        self.interface_impl_map = interface_impl_map
        self.registered_services = registered_services
        self.service_dependencies = service_dependencies
        self.aspects = aspects

    @staticmethod
    def generate_name(service_class: type):
        """生成服务名称 (CamelCase -> snake_case)"""
        return re.sub(r'(?<!^)(?=[A-Z])', '_', service_class.__name__).lower()

    @staticmethod
    def unwrap_annotation(ann: Any):
        """将 typing 注解还原为真实类型"""
        try:
            origin = get_origin(ann)
            if origin is None:
                if isinstance(ann, str):
                    return None
                return ann

            if str(origin).endswith('Annotated') or origin is getattr(_typing, 'Annotated', None):
                args = get_args(ann)
                return args[0] if args else None

            if origin is getattr(_typing, 'Union', None) or origin is getattr(_types, 'UnionType', None):
                args = [a for a in get_args(ann) if a is not type(None)]  # noqa: E721
                return args[0] if args else None

            return ann
        except Exception as e:
            logger.error(f"🚨 {e}")
            return ann

    def scan_module(self, module) -> bool:
        """扫描单个模块中的类"""
        found_any = False
        try:
            for name, obj in vars(module).items():
                if isinstance(obj, type) and obj.__module__ == module.__name__:
                    # --- 检测切面 ---
                    # 只要继承了 Aspect 或者是被 @aspect 装饰
                    if (issubclass(obj, Aspect) and obj is not Aspect) or hasattr(obj, "__pyspring_aspect__"):
                        try:
                            # 实例化切面
                            aspect_instance = obj()
                            self.aspects.append(aspect_instance)
                            logger.debug(f"📐 Found Aspect: {name}")
                            found_any = True
                        except Exception as e:
                            logger.error(f"Failed to instantiate aspect {name}: {e}")

                    is_decorated = hasattr(obj, "__pyspring_component__")

                    # 检查是否为 IService 子类
                    is_service_subclass = False
                    try:
                        if obj is not IService and issubclass(obj, IService):
                            is_service_subclass = True
                    except TypeError:
                        pass

                    if is_decorated or is_service_subclass:
                        if inspect.isabstract(obj):
                            if is_service_subclass:
                                self.interface_impl_map.setdefault(obj, None)
                            continue

                        # 记录接口->实现映射
                        for base in obj.__mro__[1:]:
                            if isinstance(base, type) and inspect.isabstract(base):
                                if issubclass(base, IService):
                                    self.interface_impl_map.setdefault(base, obj)

                        logger.debug(f"🔍 Auto-registering: {name} (Module: {module.__name__})")
                        self.register_service(obj)
                        found_any = True
        except Exception as e:
            logger.error(f"Error scanning module {module.__name__}: {e}")

        return found_any

    def register_service(self, service_class):
        """注册服务"""
        # Check for overrides from decorator
        override_name = getattr(service_class, "__pyspring_name__", None)
        service_name = override_name if override_name else self.generate_name(service_class)

        if service_name in self.registered_services:
            return

        self.registered_services.add(service_name)

        sig = inspect.signature(service_class.__init__)

        # 获取类型提示
        try:
            module_globals = vars(importlib.import_module(service_class.__module__))
            hints = get_type_hints(service_class.__init__, globalns=module_globals, include_extras=True)
        except Exception:
            module_globals = {}
            hints = {}

        dependencies = {}
        dep_names = []

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
                        impl = self.interface_impl_map.get(raw)
                        if impl:
                            impl_name = self.generate_name(impl)
                            if impl_name not in self.registered_services:
                                self.register_service(impl)
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
                        if raw_name not in self.registered_services:
                            self.register_service(raw)
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
                if param.default == inspect.Parameter.empty:
                    logger.warning(f"  ⚠️ Missing dependency for '{service_name}': {param_name}")

        self.service_dependencies[service_name] = dep_names

        # 绑定服务工厂
        def service_factory():
            # 1. 解析所有依赖
            resolved_deps = {k: v() for k, v in dependencies.items()}
            # 2. 创建实例
            instance = service_class(**resolved_deps)
            # 3. 创建代理 (AOP)
            if self.aspects:
                instance = create_proxy(instance, self.aspects)
            return instance

        self.container.bind_singleton(service_name, service_factory)
        logger.debug(f"✅ Registered service: {service_name}")
