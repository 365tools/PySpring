"""
服务注册表

维护所有已注册服务的信息
"""
from dataclasses import dataclass, field
from typing import Dict, Set, Optional, List, Callable, Any

from pyspring.ioc.annotations.scope import Scope


@dataclass
class ServiceDefinition:
    """服务定义"""
    name: str  # 服务名称
    service_type: type  # 服务类型
    scope: Scope  # 作用域
    factory: Callable[..., Any]  # 工厂函数
    dependencies: List[str] = field(default_factory=list)  # 依赖的服务名称
    is_lazy: bool = False  # 是否懒加载
    is_primary: bool = False  # 是否主要候选者
    module: str = ""  # 所属模块

    # Bean相关
    is_bean: bool = False  # 是否来自@Bean方法
    config_class: Optional[type] = None  # 配置类（仅Bean）
    bean_method: Optional[str] = None  # Bean方法名（仅Bean）
    is_conditional: bool = False  # 是否是@ConditionalOnMissingBean（可被替换）
    replaces: Optional[str] = None  # 替换的服务名称（用于子类替换父类）


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
            # 如果新的是Bean，旧的是普通组件，则Bean优先（覆盖）
            elif definition.is_bean and not existing.is_bean:
                from pyspring.log.instance import logger
                logger.debug(f"📝 Bean覆盖组件注册: '{name}' (组件 → Bean)")
                pass  # 继续注册，Bean覆盖组件
            # 👉 关键：如果旧的是 @ConditionalOnMissingBean，允许用户的实现替换
            elif existing.is_conditional:
                from pyspring.log.instance import logger
                if definition.is_bean and existing.is_bean:
                    logger.debug(f"🔄 用户Bean替换条件Bean: '{name}' ({existing.service_type.__name__} → {service_type.__name__})")
                    logger.debug(f"   旧实现: {existing.config_class.__name__ if existing.config_class else 'Unknown'}.{existing.bean_method}() [框架默认]")
                    logger.debug(f"   新实现: {definition.config_class.__name__ if definition.config_class else 'Unknown'}.{definition.bean_method}() [用户自定义]")
                else:
                    logger.debug(f"🔄 用户组件替换条件组件: '{name}' ({existing.service_type.__name__} → {service_type.__name__})")
                pass  # 继续注册，用户实现覆盖框架条件注册
            else:
                from pyspring.log.instance import logger
                logger.warning(f"⚠️ 服务 '{name}' 重复注册: 已存在={existing.service_type}, 新={service_type}, 旧is_conditional={existing.is_conditional}, 新is_conditional={definition.is_conditional}")
                raise ValueError(f"服务 '{name}' 已注册: {existing.service_type}")

        # 注册服务
        self._services[name] = definition
        self._type_to_name[service_type] = name
        self._registered_names.add(name)

        # 更新接口映射
        self._register_interface_mapping(service_type)

    def unregister(self, name: str) -> bool:
        """
        注销服务（用于替换注册）
        
        Args:
            name: 服务名称
            
        Returns:
            是否成功注销
        """
        if name not in self._services:
            return False

        definition = self._services[name]
        service_type = definition.service_type

        # 移除服务定义
        del self._services[name]
        self._registered_names.discard(name)

        # 移除类型映射（如果指向此服务）
        if self._type_to_name.get(service_type) == name:
            del self._type_to_name[service_type]

        # 移除接口映射
        import inspect
        for base in service_type.__mro__[1:]:
            if inspect.isabstract(base) or getattr(base, '_is_protocol', False):
                if base in self._interface_to_impls:
                    if service_type in self._interface_to_impls[base]:
                        self._interface_to_impls[base].remove(service_type)

        return True

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

    def get_implementations_of_base(self, base_type: type) -> List[ServiceDefinition]:
        """
        获取指定基类的所有实现（包括直接实现和子类）
        
        用于 @ConditionalOnMissingBean 检查：
        - 如果容器里已有此基类的任何实现，跳过注册框架的默认实现
        
        Args:
            base_type: 基类类型
            
        Returns:
            所有继承自此基类的服务定义列表
        """
        implementations = []

        for service_type, name in self._type_to_name.items():
            # 检查是否是 base_type 的子类（或就是 base_type 本身）
            try:
                if issubclass(service_type, base_type):
                    definition = self._services.get(name)
                    if definition:
                        implementations.append(definition)
            except TypeError:
                # 某些类型（如泛型）可能无法用 issubclass 检查，跳过
                continue

        return implementations

    def all_names(self) -> Set[str]:
        """获取所有服务名称"""
        return self._registered_names.copy()

    def all_definitions(self) -> List[ServiceDefinition]:
        """获取所有服务定义"""
        return list(self._services.values())

    def all_types(self) -> List[type]:
        """获取所有已注册的服务类型"""
        return list(self._type_to_name.keys())

    def clear(self):
        """清空注册表"""
        self._services.clear()
        self._type_to_name.clear()
        self._interface_to_impls.clear()
        self._registered_names.clear()


__all__ = ['ServiceRegistry', 'ServiceDefinition']
