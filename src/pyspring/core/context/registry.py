"""
核心上下文管理模块

提供统一的 ContextVar 注册与管理机制，供日志、认证、APM 等模块共享使用。
"""
from typing import Dict, Any, List, Tuple
from contextvars import ContextVar
import threading 

class ContextRegistry:
    """
    全局上下文注册表
    
    用于集中管理应用中的所有 ContextVar，主要用途：
    1. 日志系统自动注入：自动将注册的变量值注入到日志 extra 中
    2. 链路追踪/APM：统一获取当前上下文状态
    3. 上下文传播：在线程/任务切换时辅助传播上下文
    """
    
    # 存储注册的变量: key -> (context_var, default_value)
    _registry: Dict[str, Tuple[ContextVar, Any]] = {}
    _lock = threading.Lock()

    @classmethod
    def register(cls, key: str, context_var: ContextVar, default: Any = None) -> None:
        """
        注册一个上下文变量
        
        Args:
            key: 标识符 (也是日志 extra 中的字段名)
            context_var: ContextVar 对象
            default: 获取不到值时的默认值 (用于日志显示等)
        """
        with cls._lock:
            cls._registry[key] = (context_var, default)

    @classmethod
    def get_all(cls) -> List[Tuple[str, ContextVar, Any]]:
        """获取所有已注册的上下文变量"""
        with cls._lock:
            # 返回列表副本，避免迭代时修改
            return [(k, var, default) for k, (var, default) in cls._registry.items()]

    @classmethod
    def get_snapshot(cls) -> Dict[str, Any]:
        """
        获取当前时刻所有上下文变量的值快照
        (主要用于调试或错误报告)
        """
        snapshot = {}
        with cls._lock:
            items = cls._registry.items()
        
        for key, (var, default) in items:
            try:
                val = var.get()
                snapshot[key] = val
            except LookupError:
                snapshot[key] = default
        return snapshot
