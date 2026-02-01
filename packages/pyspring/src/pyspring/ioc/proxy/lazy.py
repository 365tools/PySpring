"""
懒加载代理

用于解决循环依赖问题
"""
from typing import Any


class LazyProxy:
    """
    懒加载代理
    
    延迟服务的实例化，直到真正访问其属性或方法时才从容器中获取实例。
    用于解决循环依赖问题。
    
    工作原理：
    1. 代理对象在注入时立即创建，但不实例化目标服务
    2. 当访问代理的属性或方法时，才从容器获取真实实例
    3. 真实实例会被缓存，后续访问直接返回缓存的实例
    
    示例：
        # ServiceA 依赖 ServiceB
        # ServiceB 依赖 ServiceA
        # 使用代理解决循环依赖
        
        class ServiceA:
            def __init__(self, service_b):  # service_b 是 LazyProxy
                self.service_b = service_b
        
        class ServiceB:
            def __init__(self, service_a):  # service_a 是 LazyProxy
                self.service_a = service_a
    """

    def __init__(self, container: 'Container', service_name: str, service_type: type):
        """
        初始化代理
        
        Args:
            container: IOC容器
            service_name: 服务名称
            service_type: 服务类型（用于类型检查）
        """
        # 使用 object.__setattr__ 避免触发 __setattr__
        object.__setattr__(self, '_container', container)
        object.__setattr__(self, '_service_name', service_name)
        object.__setattr__(self, '_service_type', service_type)
        object.__setattr__(self, '_instance', None)
        object.__setattr__(self, '_initialized', False)

    def _get_instance(self) -> Any:
        """获取真实实例（懒加载）"""
        if not self._initialized:
            instance = self._container.get(self._service_name)
            object.__setattr__(self, '_instance', instance)
            object.__setattr__(self, '_initialized', True)
        return self._instance


def get_lazy_proxy_class():
    """获取懒加载代理类"""
    return LazyProxy


def get_container_class():
    """获取容器类"""
    # 为了避免循环导入，动态导入
    from ..container.container import Container
    return Container