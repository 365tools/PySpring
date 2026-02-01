"""
模块依赖解析器

负责解析服务之间的依赖关系，支持类型提示、命名注入和集合注入。
"""
from typing import Dict, Any, List, get_type_hints, get_origin, get_args
from dataclasses import dataclass
from ..registry.registry import ServiceRegistry, ServiceDefinition
from ..proxy.lazy import get_lazy_proxy_class
from ..container.container import get_container_class
from ...log.instance import logger
from ..dependency import DependencyInfo


class DependencyResolver:
    """
    依赖解析器
    
    负责解析服务的依赖关系，支持：
    - 类型注入
    - 命名注入
    - List[Type] 集合注入
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

    def resolve_dependencies(self, service_def: ServiceDefinition, container: Any) -> Dict[str, Any]:
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
        
        # 移除self参数
        if 'return' in init_signature:
            del init_signature['return']
        if 'self' in init_signature:
            del init_signature['self']
            
        dependencies = {}
        for param_name, param_type in init_signature.items():
            dep_info = self._create_dependency_info(service_def, param_name, param_type)
            dependencies[param_name] = self._resolve_dependency(dep_info, container, service_def.name)
            
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
            LazyProxy = get_lazy_proxy_class()
            Container = get_container_class()
            return LazyProxy(container, service_name, service_def.service_type)

        # 正常获取实例
        try:
            return container.get(service_name)
        except ValueError:
            # 如果按名称找不到服务，则尝试按类型查找
            try:
                return container.get_by_type(dep_info.param_type)
            except ValueError:
                # 对于某些原生类型如bool, str, int等，返回默认值
                # 或者对于typing.Any等通用类型，返回None
                if dep_info.param_type == bool:
                    return False
                elif dep_info.param_type == str:
                    return ""
                elif dep_info.param_type == int:
                    return 0
                elif dep_info.param_type == float:
                    return 0.0
                elif dep_info.param_type == list:
                    return []
                elif dep_info.param_type == dict:
                    return {}
                elif dep_info.param_type == tuple:
                    return ()
                else:
                    # 对于其他无法处理的类型，抛出异常
                    # 但对于typing模块的特殊类型如Any，返回None
                    import typing
                    if hasattr(typing, 'Any') and dep_info.param_type == typing.Any:
                        return None
                    # 尝试检查是否是通用类型
                    origin = get_origin(dep_info.param_type)
                    if origin is not None:
                        # 处理Generic、Union等类型
                        if origin == list:
                            return []
                        elif origin == dict:
                            return {}
                        elif origin == tuple:
                            return ()
                        elif origin == type(None):
                            return None
                    # 对于其他情况，记录警告并返回None
                    logger.warning(f"⚠️ 无法解析依赖 {dep_info.param_name} 的类型 {dep_info.param_type}，返回 None")
                    return None