"""
服务注册表

维护所有已注册服务的信息
"""
from dataclasses import dataclass, field
from typing import Dict, Set, Optional, List

from pyspring.ioc.annotations.scope import Scope


@dataclass
class ServiceDefinition:
    """服务定义"""
    name: str  # 服务名称
    service_type: type  # 服务类型
    scope: Scope  # 作用域
    factory: callable  # 工厂函数
    dependencies: List[str] = field(default_factory=list)  # 依赖的服务名称
    is_lazy: bool = False  # 是否懒加载
    is_primary: bool = False  # 是否主要候选者
    module: str = ""  # 所属模块

    # Bean相关
    is_bean: bool = False  # 是否来自@Bean方法
    config_class: Optional[type] = None  # 配置类（仅Bean）
    bean_method: Optional[str] = None  # Bean方法名（仅Bean）


class ServiceRegistry:
    """
    服务注册表
    
    职责：
    1. 维护所有已注册服务的定义
    2. 提供服务查询功能
    3. 管理接口到实现的映射
    """

    def __init__(self):
        # 服务名称 -> 服务定义
        self._services: Dict[str, ServiceDefinition] = {}

        # 服务类型 -> 服务名称（用于类型查询）
        self._type_to_name: Dict[type, str] = {}

        # 接口类型 -> 实现类型列表（支持多个实现）
        self._interface_to_impls: Dict[type, List[type]] = {}

        # 已注册的服务名称集合（快速查询）
        self._registered_names: Set[str] = set()

    def register(self, definition: ServiceDefinition):
        """
        注册服务
        
        Args:
            definition: 服务定义
        """
        name = definition.name
        service_type = definition.service_type

        # 检查重复注册
        if name in self._services:
            existing = self._services[name]
            # 如果新的是primary，替换旧的
            if definition.is_primary and not existing.is_primary:
                pass  # 继续注册，覆盖旧的
            else:
                raise ValueError(f"服务 '{name}' 已注册: {existing.service_type}")

        # 注册服务
        self._services[name] = definition
        self._type_to_name[service_type] = name
        self._registered_names.add(name)

        # 更新接口映射
        self._register_interface_mapping(service_type)

    def _register_interface_mapping(self, impl_type: type):
        """注册接口到实现的映射"""
        import inspect

        # 遍历所有基类（跳过自己）
        for base in impl_type.__mro__[1:]:
            # 只映射抽象基类和Protocol
            if inspect.isabstract(base) or getattr(base, '_is_protocol', False):
                if base not in self._interface_to_impls:
                    self._interface_to_impls[base] = []

                if impl_type not in self._interface_to_impls[base]:
                    self._interface_to_impls[base].append(impl_type)

    def get(self, name: str) -> Optional[ServiceDefinition]:
        """根据名称获取服务定义"""
        return self._services.get(name)

    def get_by_type(self, service_type: type) -> Optional[ServiceDefinition]:
        """根据类型获取服务定义"""
        name = self._type_to_name.get(service_type)
        if name:
            return self._services.get(name)
        return None

    def get_implementations(self, interface_type: type) -> List[ServiceDefinition]:
        """获取接口的所有实现"""
        impl_types = self._interface_to_impls.get(interface_type, [])
        definitions = []
        for impl_type in impl_types:
            name = self._type_to_name.get(impl_type)
            if name:
                definition = self._services.get(name)
                if definition:
                    definitions.append(definition)
        return definitions

    def get_primary_implementation(self, interface_type: type) -> Optional[ServiceDefinition]:
        """获取接口的主要实现"""
        impls = self.get_implementations(interface_type)

        # 查找标记为primary的实现
        for impl in impls:
            if impl.is_primary:
                return impl

        # 如果只有一个实现，返回它
        if len(impls) == 1:
            return impls[0]

        # 多个实现且没有primary
        return None

    def has(self, name: str) -> bool:
        """检查服务是否已注册"""
        return name in self._registered_names

    def has_type(self, service_type: type) -> bool:
        """检查类型是否已注册"""
        return service_type in self._type_to_name

    def all_names(self) -> Set[str]:
        """获取所有服务名称"""
        return self._registered_names.copy()

    def all_definitions(self) -> List[ServiceDefinition]:
        """获取所有服务定义"""
        return list(self._services.values())

    def clear(self):
        """清空注册表"""
        self._services.clear()
        self._type_to_name.clear()
        self._interface_to_impls.clear()
        self._registered_names.clear()


__all__ = ['ServiceRegistry', 'ServiceDefinition']
