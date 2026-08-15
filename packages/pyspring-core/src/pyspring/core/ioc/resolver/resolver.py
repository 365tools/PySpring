"""
模块依赖解析器

负责解析服务之间的依赖关系，支持类型提示、命名注入和集合注入。
"""
import inspect
from typing import Any, get_type_hints, get_origin, get_args
from dataclasses import dataclass
from ..registry.registry import ServiceRegistry, ServiceDefinition
from ...log.instance import logger
from ..dependency import DependencyInfo


# 特殊标记：表示应该使用参数的默认值
class _UseDefaultValue:
    """标记类，表示参数应使用其默认值"""
    pass

_USE_DEFAULT_VALUE = _UseDefaultValue()


class DependencyResolver:
    """
    依赖解析器
    
    负责解析服务的依赖关系，支持：
    - 类型注入
    - 命名注入
    - list[Type] 集合注入
    - 循环依赖检测与处理
    """
    def __init__(self, registry: ServiceRegistry):
        self.registry = registry
        self._instantiation_stack = []

    def _generate_service_name(self, param_type: type) -> str:
        """
        根据类型生成服务名称
        
        Args:
            param_type: 参数类型
            
        Returns:
            服务名称
        """
        if hasattr(param_type, '__name__'):
            # 将驼峰命名转为蛇形命名
            import re
            name = param_type.__name__
            # 将驼峰命名转换为蛇形命名
            name = re.sub(r'(?<!^)(?=[A-Z])', '_', name).lower()
            return name
        elif hasattr(param_type, '_name') and param_type._name:
            # 对于一些特殊类型如List[int]等
            import re
            name = param_type._name
            name = re.sub(r'(?<!^)(?=[A-Z])', '_', name).lower()
            return name
        else:
            # 如果类型没有 __name__ 属性，返回基于类型的唯一标识
            return f"type_{abs(hash(str(param_type))) % 10000}"

    def resolve_dependencies(self, service_def: ServiceDefinition, container: Any) -> dict[str, Any]:
        """
        解析服务定义的所有依赖
        
        Args:
            service_def: 服务定义
            container: 容器实例
            
        Returns:
            依赖字典
        """
        # 获取构造函数参数类型
        init_signature = get_type_hints(service_def.service_type.__init__)
        
        # 获取构造函数的签名（用于获取默认值）
        sig = inspect.signature(service_def.service_type.__init__)
        
        # 移除self参数
        if 'return' in init_signature:
            del init_signature['return']
        if 'self' in init_signature:
            del init_signature['self']
            
        dependencies = {}
        for param_name, param_type in init_signature.items():
            # 获取参数的默认值
            param = sig.parameters[param_name]
            has_default = param is not None and param.default != inspect.Parameter.empty
            
            dep_info = self._create_dependency_info(service_def, param_name, param_type)
            
            # 尝试解析依赖，传入是否有默认值的信息
            resolved_value = self._resolve_dependency(dep_info, container, service_def.name, has_default)
            
            # 如果返回了特殊标记表示"使用默认值"，则跳过此参数
            if resolved_value is _USE_DEFAULT_VALUE:
                logger.debug(f"📌 参数 '{param_name}' 使用构造函数默认值: {param.default}")
                continue
                
            dependencies[param_name] = resolved_value
            
        return dependencies

    def _create_dependency_info(self, service_def, param_name: str, param_type: type) -> DependencyInfo:
        """
        创建依赖信息对象
        
        Args:
            service_def: 服务定义
            param_name: 参数名称
            param_type: 参数类型
            
        Returns:
            依赖信息
        """
        # 检查是否是List注入
        origin = get_origin(param_type)
        if origin is list:
            type_args = get_args(param_type)
            if type_args:
                element_type = type_args[0]
                # 使用特殊前缀标记List注入
                service_name = f"__list_collection__:{param_name}"
                return DependencyInfo(
                    param_name=param_name,
                    param_type=param_type,
                    service_name=service_name,
                    is_list=True,
                    element_type=element_type
                )
        
        # 检查是否有@inject注解
        annotations = getattr(service_def.service_type, '__annotations__', {})
        inject_config = annotations.get(f"_{param_name}_inject", None)
        if inject_config:
            return DependencyInfo(
                param_name=param_name,
                param_type=param_type,
                service_name=inject_config.service_name,
                qualifier=inject_config.qualifier
            )
            
        # 默认按类型查找
        # 使用类型名称生成服务名称
        service_name = self._generate_service_name(param_type)
        return DependencyInfo(
            param_name=param_name,
            param_type=param_type,
            service_name=service_name,  # 使用类型生成的服务名
            qualifier=None
        )

    def _resolve_dependency(
            self,
            dep_info: DependencyInfo,
            container: Any,
            current_service: str,
            has_default: bool = False
    ) -> Any:
        """
        解析单个依赖，返回实例或代理
        
        Args:
            dep_info: 依赖信息
            container: 容器
            current_service: 当前正在实例化的服务名称
            has_default: 该参数是否有默认值
            
        Returns:
            依赖实例、代理或 _USE_DEFAULT_VALUE 标记
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
        # 注意：现在循环依赖检测主要在容器层面处理，这里作为辅助检测
        if service_name in self._instantiation_stack:
            # 使用懒加载代理
            logger.debug(f"[cycle] Detected potential circular dependency {current_service} -> {service_name}, using proxy")
            service_def = self.registry.get(service_name)
            if service_def is None:
                raise ValueError(f"Service not found for lazy proxy: {service_name}")
            # 局部导入：避免模块级循环依赖（resolver -> proxy.lazy）
            from ..proxy.lazy import get_lazy_proxy_class
            LazyProxy = get_lazy_proxy_class()
            return LazyProxy(container, service_name, service_def.service_type)

        # 正常获取实例
        try:
            return container.get(service_name)
        except ValueError:
            # 如果按名称找不到服务，则尝试按类型查找
            try:
                return container.get_by_type(dep_info.param_type)
            except ValueError:
                # 如果是特殊类型（如 typing.Any 或 Optional[T]），即使返回 None 也应该静默处理
                import typing
                if dep_info.param_type is typing.Any:
                    return None
                
                # 检查是否是 Optional 类型
                if self._is_optional_type(dep_info.param_type):
                    return None
                
                # 尝试获取内置类型默认值
                builtin_default = self._get_builtin_type_default(dep_info.param_type)
                
                # 🔑 关键修改：如果参数有默认值，且是基本类型，则使用构造函数的默认值而不是类型的默认值
                if builtin_default is not None and has_default:
                    # 返回特殊标记，表示应该使用构造函数的默认值
                    return _USE_DEFAULT_VALUE
                
                if builtin_default is not None:
                    # 没有默认值时，才使用类型的默认值
                    return builtin_default
                
                # 尝试处理泛型类型
                generic_default = self._get_generic_type_default(dep_info.param_type)
                if generic_default is not None:
                    return generic_default
                
                # 对于其他无法处理的类型，如果有默认值则使用默认值
                if has_default:
                    return _USE_DEFAULT_VALUE
                
                # 对于其他无法处理的类型，记录警告并返回None
                logger.warning(f"⚠️ 无法解析依赖 {dep_info.param_name} 的类型 {dep_info.param_type}，返回 None")
                return None

    def _is_optional_type(self, param_type: type) -> bool:
        """
        检查是否是Optional类型 (Union[X, None] 或 X | None)
            
        Args:
            param_type: 参数类型
                
        Returns:
            是否是Optional类型
        """
        import typing
        # 检查 Union[X, None] 形式
        if hasattr(param_type, '__origin__'):
            try:
                param_origin = getattr(param_type, '__origin__', None)
                if param_origin is getattr(typing, 'Union', None):
                    args = get_args(param_type)
                    if len(args) == 2 and type(None) in args:
                        return True
            except Exception:
                pass
            
        # 检查新的联合类型语法 (如 str | None)
        try:
            if hasattr(param_type, '__args__'):
                args = getattr(param_type, '__args__', ())
                if len(args) == 2 and type(None) in args:
                    return True
        except Exception:
            pass
            
        # 检查新语法的联合类型 (T | None)，通过字符串表示
        type_str = str(param_type)
        if '|' in type_str and 'None' in type_str:
            # 检查是否是 T | None 的形式
            parts = [part.strip() for part in type_str.split('|')]
            if len(parts) == 2 and 'None' in parts:
                return True
            
        return False
        
    def _get_builtin_type_default(self, param_type: type):
        """
        获取内置类型的默认值
            
        Args:
            param_type: 参数类型
                
        Returns:
            默认值, 如果类型不是内置类型则返回None
        """
        # 内置类型映射
        builtin_defaults = {
            bool: False,
            str: "",
            int: 0,
            float: 0.0,
            list: [],
            dict: {},
            tuple: (),
            set: set(),
            bytes: b"",
            bytearray: bytearray(),
            complex: complex(0, 0),
            frozenset: frozenset(),
            type: type,
        }
            
        # 检查是否是内置类型
        if param_type in builtin_defaults:
            return builtin_defaults[param_type]
            
        # 检查是否是typing模块的特殊类型
        import typing
        # 检查 typing.Any 类型 - 这是最重要的检查
        if param_type is typing.Any:
            return None  # typing.Any 类型返回 None
        elif getattr(param_type, '__name__', None) == 'Any' or str(param_type).endswith('.Any'):
            return None  # 其他 Any 类型的变体
        elif hasattr(typing, 'NoReturn') and param_type == typing.NoReturn:
            return None
        elif param_type is type(None):
            return None
            
        # 检查是否是Optional类型
        if self._is_optional_type(param_type):
            return None
            
        # 不是内置类型
        return None
    
    def _get_generic_type_default(self, param_type: type):
        """
        获取泛型类型的默认值
        
        Args:
            param_type: 参数类型
            
        Returns:
            默认值, 如果类型不是泛型类型则返回None
        """
        # 检查是否是typing.Any类型（需要优先处理）
        import typing
        if param_type is typing.Any:
            return None
        elif getattr(param_type, '__name__', None) == 'Any' or str(param_type).endswith('.Any'):
            return None  # 其他 Any 类型的变体
        
        # 检查是否是Optional类型 (Union[X, None] 或 X | None)
        if hasattr(param_type, '__origin__'):
            try:
                param_origin = getattr(param_type, '__origin__', None)
                
                # 检查是否是 Union 类型 (适用于 Optional[T] = Union[T, None])
                if param_origin is getattr(typing, 'Union', None):
                    args = get_args(param_type)
                    if len(args) == 2 and type(None) in args:
                        # Optional[X] 类型，返回None
                        return None
            except Exception:
                pass
        
        # 检查是否是新的联合类型语法 (如 str | None)
        try:
            if hasattr(param_type, '__args__'):
                args = getattr(param_type, '__args__', ())
                if len(args) == 2 and type(None) in args:
                    # 这是类似 T | None 的类型，返回None
                    return None
        except Exception:
            pass
        
        # 检查是否是新语法的联合类型 (T | None)，通过字符串表示
        type_str = str(param_type)
        if '|' in type_str and 'None' in type_str:
            # 检查是否是 T | None 的形式
            parts = [part.strip() for part in type_str.split('|')]
            if len(parts) == 2 and 'None' in parts:
                return None  # 视为 object | None 类型
        
        # 检查是否是泛型类型
        origin = get_origin(param_type)
        if origin is not None:
            # 处理常见的泛型类型
            if origin == list:
                return []
            elif origin == dict:
                return {}
            elif origin == tuple:
                return ()
            elif origin == set:
                return set()
            elif origin == frozenset:
                return frozenset()
            elif origin == type(None):
                return None
            elif origin == (getattr(__builtins__, 'tuple', None) or tuple):  # typing.Tuple
                return ()
            elif hasattr(origin, '__origin__'):  # 更多泛型类型
                # 对于其他泛型类型，尝试返回其原始类型的空实例
                if hasattr(origin, '__call__'):
                    try:
                        return origin()
                    except Exception:
                        pass
        

        
        return None