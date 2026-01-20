import importlib
import inspect
import re
import types as _types
import typing as _typing
from typing import Any, get_origin, get_args, get_type_hints, List, Dict, Set, cast

from pyspring.aop.core.models import Aspect
from pyspring.aop.proxy.factory import create_proxy
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
                                self.interface_impl_map.setdefault(obj, cast(Any, None))
                            continue

                        # 记录接口->实现映射
                        for base in obj.__mro__[1:]:
                            if isinstance(base, type) and inspect.isabstract(base):
                                if issubclass(base, IService):
                                    self.interface_impl_map.setdefault(base, obj)

                        logger.debug(f"🔍 Auto-registering: {name} (Module: {module.__name__})")
                        self.register_service(obj)

                        # 如果是配置类，处理其中的 @Bean 方法
                        if hasattr(obj, "__pyspring_configuration__"):
                            self.register_configuration_beans(obj)
                            
                        found_any = True
        except Exception as e:
            logger.error(f"Error scanning module {module.__name__}: {e}")

        return found_any

    def register_configuration_beans(self, config_class: type):
        """注册配置类中的 Bean"""
        # 确保配置类本身已被注册
        config_name = self.generate_name(config_class)
        # 获取配置类实例的 Provider (Dependency Injector 应该已经注册了它)
        config_provider = getattr(self.container, config_name, None)

        if not config_provider:
            logger.warning(f"Configuration class {config_class.__name__} not registered properly.")
            return

        # 遍历所有方法
        for name, method in config_class.__dict__.items():
            if hasattr(method, "__pyspring_bean__"):
                self._register_bean_method(config_class, config_name, method, name)

    def _register_bean_method(self, config_class, config_name, method, method_name):
        """注册单个 Bean 方法"""
        # Check @ConditionalOnMissingBean
        missing_bean_type = getattr(method, "__pyspring_conditional_on_missing_bean__", None)
        if missing_bean_type:
            # 简单检查：如果在 interface_impl_map 中已存在，则跳过
            # 注意：这里我们假设 missing_bean_type 是接口类
            if missing_bean_type in self.interface_impl_map:
                logger.debug(f"⏩ Skipping @Bean {method_name}: {missing_bean_type.__name__} already exists")
                return
            # 也可以检查具体类是否已注册 (通过类名)
            if hasattr(missing_bean_type, '__name__'):
                expected_name = self.generate_name(missing_bean_type)
                if expected_name in self.registered_services:
                    logger.debug(f"⏩ Skipping @Bean {method_name}: {expected_name} service exists")
                    return

        # 解析返回类型
        return_type = method.__annotations__.get('return')
        if not return_type:
            logger.warning(f"⚠️ @Bean method {method_name} missing return type annotation")
            # Fallback: 使用方法名作为 bean 名

        # 注册 Bean
        # 我们使用 Factory provider，它调用 config_instance.method(...)
        # 并需要手动解析 method 的依赖

        sig = inspect.signature(method)
        dependencies = {}

        # 解析依赖 (类似于 register_service，但 context 是 method 参数)
        # TODO: 这里应该复用 analyze_dependencies 逻辑，暂时简化
        # 为简化实现，假设 @Bean 方法参数名称与注册的服务名称一致，或者类型匹配

        # 暂时使用一个简单的 Provider 包装器
        from dependency_injector import providers

        # 构造依赖字典
        # 复杂性：我们需要为每个参数找到对应的 provider
        # 这里为了稳健性，我们需要一个 resolve_dependencies 方法
        bean_deps = self._resolve_method_dependencies(method)

        # 创建 Provider
        # method 是 unbound function，需要绑定到实例
        # providers.Method 或者是 Resource
        # 但 Dependency Injector 的 providers.Factory(config_inst_provider.provided.method, **deps)

        # 获取 Config 类的 singleton provider
        config_singleton = getattr(self.container, config_name)

        # 定义 Bean Provider
        # 注意: getattrOnProvider 可能是 provided.attribute
        bean_factory = providers.Factory(
            getattr(config_singleton.provided, method_name),
            **bean_deps
        )

        # 确定 Bean 名称
        bean_name = getattr(method, "__pyspring_bean_name__", None)
        if not bean_name:
            # 如果返回类型是类，使用类名
            if return_type and isinstance(return_type, type):
                bean_name = self.generate_name(return_type)
                # 更新 interface map
                if inspect.isabstract(return_type) or inspect.isclass(return_type):
                    self.interface_impl_map[return_type] = bean_factory  # 标记为已存在 (Value 不是类而是 Provider? 这里 Map 定义是 type->type)
                    # 这是一个问题: interface_impl_map 期望 type->type
                    # 但 Bean 方法产生的是实例，不是类。
                    # 为了兼容 Conditional check，我们可以放一个占位符或者伪造的 type
                    pass
            else:
                bean_name = method_name

        if bean_name in self.registered_services:
            return

        self.container.bind_provider(bean_name, bean_factory)
        self.registered_services.add(bean_name)

        # 更新接口映射以供后续 Conditional 检查
        if return_type and isinstance(return_type, type):
            self.interface_impl_map[return_type] = return_type  # 标记接口已有实现

        logger.info(f"🌱 Registered @Bean: {bean_name} (from {config_class.__name__})")

    def _resolve_method_dependencies(self, method) -> Dict[str, Any]:
        """简化的依赖解析"""
        sig = inspect.signature(method)
        deps = {}
        for param_name, param in sig.parameters.items():
            if param_name == 'self': continue

            # 1. 尝试通过名称匹配
            if hasattr(self.container.container, param_name):
                deps[param_name] = getattr(self.container.container, param_name)
                continue

            # 2. 尝试通过类型匹配
            ann = param.annotation
            raw_type = self.unwrap_annotation(ann)
            if raw_type and isinstance(raw_type, type):
                # 查找接口实现
                impl = self.interface_impl_map.get(raw_type)
                if impl:
                    impl_name = self.generate_name(impl)
                    if hasattr(self.container.container, impl_name):
                        deps[param_name] = getattr(self.container.container, impl_name)
                # 或者是具体类本身
                else:
                    type_name = self.generate_name(raw_type)
                    if hasattr(self.container.container, type_name):
                        deps[param_name] = getattr(self.container.container, type_name)

        return deps

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

            # 忽略 *args (VAR_POSITIONAL) 和 **kwargs (VAR_KEYWORD)
            if param.kind in (inspect.Parameter.VAR_POSITIONAL, inspect.Parameter.VAR_KEYWORD):
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

                    if is_pyspring_component and isinstance(raw, type) and not inspect.isabstract(raw):
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
                logger.debug(f"  - [{service_name}] Injected dependency '{param_name}': {resolved_name}")
            else:
                if param.default == inspect.Parameter.empty:
                    logger.warning(f"  ⚠️ [{service_name}] Missing dependency: '{param_name}'")

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
