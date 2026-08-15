"""
IOC核心接口定义

新的设计理念：
1. IManaged - 纯标记接口，表示类由IOC容器管理
2. 作用域通过装饰器声明，而不是通过接口继承
3. 生命周期钩子是可选的，不强制实现
"""
from typing import Protocol, runtime_checkable


@runtime_checkable
class IManaged(Protocol):
    """
    标记接口：表示该类由IOC容器管理
    
    这是一个纯标记接口，不包含任何方法。
    任何希望被IOC容器管理的类都应该实现此接口或使用 @Component 装饰器。
    
    设计理念：
    - 最小化接口：不强制实现任何方法
    - 显式标记：明确表明类需要被IOC管理
    - 类型安全：支持类型检查和IDE提示
    """
    pass


@runtime_checkable
class ILifecycle(Protocol):
    """
    生命周期接口（可选）
    
    如果服务需要在应用启动后和关闭前执行特定操作，可以实现此接口。
    
    注意：这是可选接口，只有需要生命周期管理的类才实现。
    """

    async def on_startup(self) -> None:
        """
        应用启动回调
        
        在依赖注入完成后、应用正式启动时调用。
        可以在此进行资源初始化、连接建立等操作。
        
        注意：
        - 不要在构造函数中进行耗时操作
        - 构造函数只应接收依赖注入，不应有业务逻辑
        - 耗时的初始化操作应该在此方法中进行
        """
        ...

    async def on_shutdown(self) -> None:
        """
        应用关闭回调
        
        在容器关闭或应用停止前调用。
        可以在此进行资源清理、连接关闭等操作。
        """
        ...


__all__ = ['IManaged', 'ILifecycle']
