"""
懒加载代理

用于解决循环依赖问题
"""
from typing import Any, TYPE_CHECKING

if TYPE_CHECKING:
    from pyspring.ioc.container.container import Container


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

    def __getattr__(self, name: str) -> Any:
        """代理属性访问"""
        if name.startswith('_'):
            # 访问代理自身的私有属性
            return object.__getattribute__(self, name)
        # 访问目标对象的属性
        instance = self._get_instance()
        return getattr(instance, name)

    def __setattr__(self, name: str, value: Any):
        """代理属性设置"""
        if name.startswith('_'):
            # 设置代理自身的私有属性
            object.__setattr__(self, name, value)
        else:
            # 设置目标对象的属性
            instance = self._get_instance()
            setattr(instance, name, value)

    def __call__(self, *args, **kwargs):
        """代理函数调用"""
        instance = self._get_instance()
        return instance(*args, **kwargs)

    def __repr__(self) -> str:
        """代理的字符串表示"""
        if self._initialized:
            return f"<LazyProxy of {self._service_type.__name__}: {repr(self._instance)}>"
        return f"<LazyProxy of {self._service_type.__name__}: not initialized>"

    def __str__(self) -> str:
        """代理的字符串表示"""
        instance = self._get_instance()
        return str(instance)

    def __bool__(self) -> bool:
        """代理的布尔值"""
        instance = self._get_instance()
        return bool(instance)

    def __len__(self) -> int:
        """代理的长度"""
        instance = self._get_instance()
        return len(instance)

    def __getitem__(self, key):
        """代理的索引访问"""
        instance = self._get_instance()
        return instance[key]

    def __setitem__(self, key, value):
        """代理的索引设置"""
        instance = self._get_instance()
        instance[key] = value

    def __iter__(self):
        """代理的迭代"""
        instance = self._get_instance()
        return iter(instance)

    def __contains__(self, item):
        """代理的包含检查"""
        instance = self._get_instance()
        return item in instance

    # 支持异步方法
    def __await__(self):
        """代理的异步等待"""
        instance = self._get_instance()
        return instance.__await__()

    async def __aenter__(self):
        """代理的异步上下文管理器入口"""
        instance = self._get_instance()
        return await instance.__aenter__()

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """代理的异步上下文管理器出口"""
        instance = self._get_instance()
        return await instance.__aexit__(exc_type, exc_val, exc_tb)


__all__ = ['LazyProxy']
