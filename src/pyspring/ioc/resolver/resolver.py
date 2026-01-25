"""
依赖解析器

负责解析服务的依赖关系并构造实例
"""
import importlib
import inspect
from dataclasses import dataclass
from typing import Dict, Any, List, Optional, get_type_hints, get_origin, get_args

from pyspring.ioc.proxy.lazy import LazyProxy
from pyspring.ioc.registry.registry import ServiceRegistry, ServiceDefinition
from pyspring.log.instance import logger


@dataclass
class DependencyInfo:
    """依赖信息"""
    param_name: str  # 参数名
    param_type: type  # 参数类型
    service_name: str  # 解析到的服务名称
    use_proxy: bool = False  # 是否使用代理（循环依赖）


class DependencyResolver:
    """
    依赖解析器
    
    职责：
    1. 分析服务的构造函数，识别依赖
    2. 解析依赖的服务名称
    3. 检测循环依赖
    4. 在必要时使用懒加载代理
    """

    def __init__(self, registry: ServiceRegistry):
        self.registry = registry
        # 当前正在实例化的服务栈（用于检测循环依赖）
        self._instantiation_stack: List[str] = []

    def resolve_dependencies(
            self,
            service_def: ServiceDefinition,
            container: Any
    ) -> Dict[str, Any]:
        """
        解析服务的所有依赖
        
        Args:
            service_def: 服务定义
            container: IOC容器实例
            
        Returns:
            依赖字典 {参数名: 实例/代理}
        """
        service_name = service_def.name
        service_type = service_def.service_type

        # 检查循环依赖
        if service_name in self._instantiation_stack:
            cycle = ' -> '.join(self._instantiation_stack + [service_name])
            raise RuntimeError(f"检测到循环依赖: {cycle}")

        # 进入实例化栈
        self._instantiation_stack.append(service_name)

        try:
            # 分析依赖
            dependencies_info = self._analyze_dependencies(service_type)

            # 解析依赖实例
            resolved = {}
            for dep_info in dependencies_info:
                resolved[dep_info.param_name] = self._resolve_dependency(
                    dep_info,
                    container,
                    service_name
                )

            return resolved

        finally:
            # 离开实例化栈
            self._instantiation_stack.pop()

    def _analyze_dependencies(self, service_type: type) -> List[DependencyInfo]:
        """
        分析服务的构造函数，提取依赖信息
        
        Args:
            service_type: 服务类型
            
        Returns:
            依赖信息列表
        """
        dependencies = []

        try:
            # 获取构造函数签名
            sig = inspect.signature(service_type.__init__)

            # 获取类型注解
            try:
                module_globals = vars(importlib.import_module(service_type.__module__))
                hints = get_type_hints(service_type.__init__, globalns=module_globals, include_extras=True)
            except Exception:
                hints = {}

            # 遍历参数
            for param_name, param in sig.parameters.items():
                if param_name == 'self':
                    continue

                # 跳过可变参数
                if param.kind in (inspect.Parameter.VAR_POSITIONAL, inspect.Parameter.VAR_KEYWORD):
                    continue

                # 获取参数类型
                param_type = hints.get(param_name, param.annotation)
                if param_type == inspect.Parameter.empty:
                    logger.warning(f"⚠️ 参数 '{param_name}' 缺少类型注解，跳过注入")
                    continue

                # 🔧 跳过有默认值的参数（除非是 IManaged 实例需要注入）
                # 如果参数有默认值，通常表示这是一个可选的配置参数，不需要从容器注入
                if param.default != inspect.Parameter.empty:
                    # 检查是否是基本类型
                    basic_types = (bool, int, str, float, type(None), type)
                    if param_type in basic_types:
                        # logger.debug(f"⏩ 跳过有默认值的基本类型参数: '{param_name}'")
                        continue

                    # 检查是否是 Type[...] 泛型（如 Type[BaseUserTable]）
                    # 这些通常是类型参数，不是需要注入的服务
                    origin = getattr(param_type, '__origin__', None)
                    if origin is type:
                        # logger.debug(f"⏩ 跳过有默认值的类型参数: '{param_name}'")
                        continue

                    # 如果不是 IManaged 的子类，也跳过
                    # 只有明确需要注入的服务类型才应该被注入
                    try:
                        from pyspring.ioc.interfaces.core import IManaged
                        if isinstance(param_type, type) and not issubclass(param_type, IManaged):
                            logger.debug(f"⏩ 跳过有默认值的非服务类型参数: '{param_name}'")
                            continue
                    except (TypeError, ImportError):
                        # 如果无法检查，默认跳过有默认值的参数
                        logger.debug(f"⏩ 跳过有默认值的参数: '{param_name}'")
                        continue

                # 解析依赖服务名称
                service_name = self._resolve_service_name(param_name, param_type)
                if service_name:
                    dependencies.append(DependencyInfo(
                        param_name=param_name,
                        param_type=param_type,
                        service_name=service_name
                    ))
                else:
                    logger.warning(f"⚠️ 无法解析参数 '{param_name}' 的依赖")

        except Exception as e:
            logger.error(f"❌ 分析依赖失败: {service_type.__name__}: {e}")

        return dependencies

    def _resolve_service_name(self, param_name: str, param_type: type) -> Optional[str]:
        """
        解析参数对应的服务名称
        
        优先级：
        1. 接口类型匹配（抽象类/Protocol）
        2. 具体类型匹配
        3. 参数名匹配
        
        Args:
            param_name: 参数名
            param_type: 参数类型
            
        Returns:
            服务名称，如果无法解析则返回None
        """
        # 处理泛型（如 List[T]）
        origin = get_origin(param_type)
        if origin is list or origin is List:
            # 对于 List[T] 类型，尝试通过参数名匹配Bean
            # 例如：auth_providers: List[ILoginProvider] -> 查找名为 "auth_providers" 的Bean
            if self.registry.has(param_name):
                return param_name

            # 如果没有找到精确匹配的Bean，尝试获取List的元素类型
            # 然后查找所有该类型的实例并返回列表
            # 注意：这里返回参数名是为了后续在 _resolve_dependency 中特殊处理
            type_args = get_args(param_type)
            if type_args:
                # 标记这是一个需要收集的List类型
                # 使用特殊前缀标识
                return f"__list_collection__:{param_name}"
            
            return None

        # 展开Annotated等类型
        raw_type = self._unwrap_annotation(param_type)
        if not raw_type or not isinstance(raw_type, type):
            return None

        # 1. 尝试接口类型匹配
        if inspect.isabstract(raw_type) or getattr(raw_type, '_is_protocol', False):
            impl_def = self.registry.get_primary_implementation(raw_type)
            if impl_def:
                return impl_def.name

        # 2. 尝试具体类型匹配
        type_def = self.registry.get_by_type(raw_type)
        if type_def:
            return type_def.name

        # 3. 尝试参数名匹配
        if self.registry.has(param_name):
            return param_name

        return None

    def _resolve_dependency(
            self,
            dep_info: DependencyInfo,
            container: Any,
            current_service: str
    ) -> Any:
        """
        解析单个依赖，返回实例或代理
        
        Args:
            dep_info: 依赖信息
            container: 容器
            current_service: 当前正在实例化的服务名称
            
        Returns:
            依赖实例或代理
        """
        service_name = dep_info.service_name

        # 检查是否是List类型的集合注入
        if service_name.startswith("__list_collection__:"):
            # 提取原始参数名
            param_name = service_name.split(":", 1)[1]

            # 获取List的元素类型
            origin = get_origin(dep_info.param_type)
            type_args = get_args(dep_info.param_type)

            if type_args:
                element_type = type_args[0]
                # 获取所有该类型的实例
                instances = container.get_all_of_type(element_type)
                logger.debug(f"📦 为参数 '{param_name}' 收集了 {len(instances)} 个 {element_type.__name__} 实例")
                return instances

            # 如果无法获取元素类型，返回空列表
            logger.warning(f"⚠️ 无法解析 List 参数 '{param_name}' 的元素类型")
            return []

        # 检查是否会造成循环依赖
        if service_name in self._instantiation_stack:
            # 使用懒加载代理
            logger.debug(f"🔄 检测到潜在循环依赖 {current_service} -> {service_name}，使用代理")
            service_def = self.registry.get(service_name)
            return LazyProxy(container, service_name, service_def.service_type)

        # 正常获取实例
        return container.get(service_name)

    @staticmethod
    def _unwrap_annotation(ann: Any) -> Optional[type]:
        """展开类型注解，提取真实类型"""
        import typing

        try:
            origin = get_origin(ann)
            if origin is None:
                return ann if isinstance(ann, type) else None

            # 处理 Annotated[T, ...]
            if str(origin).endswith('Annotated') or origin is getattr(typing, 'Annotated', None):
                args = get_args(ann)
                return args[0] if args else None

            # 处理 Optional[T] / Union[T, None]
            if origin is getattr(typing, 'Union', None):
                args = [a for a in get_args(ann) if a is not type(None)]  # noqa: E721
                return args[0] if args else None

            return ann
        except Exception:
            return None


__all__ = ['DependencyResolver', 'DependencyInfo']
