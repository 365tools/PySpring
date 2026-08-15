"""
服务注册表

维护所有已注册服务的信息
"""
from dataclasses import dataclass, field
from typing import Set, Callable, Any

from pyspring.core.ioc.annotations.scope import Scope


@dataclass
class ServiceDefinition:
    """服务定义"""
    name: str  # 服务名称
    service_type: type  # 服务类型
    scope: Scope  # 作用域
    factory: Callable[..., Any]  # 工厂函数
    dependencies: list[str] = field(default_factory=list)  # 依赖的服务名称
    is_lazy: bool = False  # 是否懒加载
    is_primary: bool = False  # 是否主要候选者
    module: str = ""  # 所属模块

    # Bean相关
    is_bean: bool = False  # 是否来自@Bean方法
    config_class: (type) | None = None  # 配置类（仅Bean）
    bean_method: (str) | None = None  # Bean方法名（仅Bean）
    is_conditional: bool = False  # 是否是@ConditionalOnMissingBean（可被替换）
    replaces: (str) | None = None  # 替换的服务名称（用于子类替换父类）


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
        self._services: dict[str, ServiceDefinition] = {}

        # 服务类型 -> 服务名称（用于类型查询）
        self._type_to_name: dict[type, str] = {}

        # 接口类型 -> 实现类型列表（支持多个实现）
        self._interface_to_impls: dict[type, list[type]] = {}

        # 已注册的服务名称集合（快速查询）
        self._registered_names: Set[str] = set()

    def _is_interface_type(self, base_type: type) -> bool:
        """
        判断是否是接口类型
        
        Args:
            base_type: 待检查的类型
            
        Returns:
            是否是接口类型
        """
        import inspect
        from typing import Protocol
        
        # 检查是否是抽象基类
        if inspect.isabstract(base_type):
            return True
        
        # 检查是否是Protocol
        if getattr(base_type, '_is_protocol', False):
            return True
        
        # 检查是否是 typing.Protocol
        if base_type is Protocol:
            return True
        
        # 检查是否是 ABC 的子类（Abstract Base Classes）
        try:
            import abc
            if issubclass(base_type, abc.ABC):
                # 额外检查是否确实有抽象方法
                return hasattr(base_type, '__abstractmethods__') and len(base_type.__abstractmethods__) > 0
        except (TypeError, AttributeError):
            pass
        
        return False

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
                from pyspring.core.log.instance import logger
                logger.debug(f"📝 Bean覆盖组件注册: '{name}' (组件 → Bean)")
                pass  # 继续注册，Bean覆盖组件
            else:
                from pyspring.core.log.instance import logger
                logger.warning(f"⚠️ 服务 '{name}' 重复注册: {existing.service_type.__name__} → {service_type.__name__}")
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
            if self._is_interface_type(base):
                if base not in self._interface_to_impls:
                    self._interface_to_impls[base] = []

                if impl_type not in self._interface_to_impls[base]:
                    self._interface_to_impls[base].append(impl_type)

    def get(self, name: str) -> (ServiceDefinition) | None:
        """根据名称获取服务定义"""
        return self._services.get(name)

    def get_by_type(self, service_type: type) -> (ServiceDefinition) | None:
        """
        根据类型获取服务定义
        
        支持继承查询：
        - 精确类型匹配：直接返回
        - 未找到：查找是否有子类被注册（父类被子类替换的场景）
        """
        # 1. 精确类型匹配
        name = self._type_to_name.get(service_type)
        if name:
            return self._services.get(name)

        # 2. 查找子类（替换场景）
        # 遍历所有已注册的服务，找到继承自 service_type 的子类
        for definition in self._services.values():
            # 检查是否是子类（且不是自己）
            try:
                if (definition.service_type != service_type and
                        issubclass(definition.service_type, service_type)):
                    # 找到了一个子类，返回它
                    # 注意：如果有多个子类，返回第一个（一般场景下应该只有一个）
                    return definition
            except TypeError:
                # issubclass 可能抛异常（如果类型不是类）
                continue
        
        return None

    def get_implementations(self, interface_type: type) -> list[ServiceDefinition]:
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

    def get_primary_implementation(self, interface_type: type) -> (ServiceDefinition) | None:
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

    def all_definitions(self) -> list[ServiceDefinition]:
        """获取所有服务定义"""
        return list(self._services.values())

    def all_types(self) -> list[type]:
        """获取所有已注册的服务类型"""
        return list(self._type_to_name.keys())

    def clear(self):
        """清空注册表"""
        self._services.clear()
        self._type_to_name.clear()
        self._interface_to_impls.clear()
        self._registered_names.clear()


__all__ = ['ServiceRegistry', 'ServiceDefinition']
