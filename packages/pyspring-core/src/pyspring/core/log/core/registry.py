from pyspring.core.context.registry import ContextRegistry


def register_context_var(key: str, context_var, default: object = None) -> None:
    """
    注册一个上下文变量到全局注册表中。
    
    日志系统会自动从全局注册表中读取这些变量并注入到日志记录中。
    其他模块(如Auth)也可以通过 core.context 访问统一管理的上下文。

    Args:
        key: 上下文标识符 (同时作为日志 extra 字段名)
        context_var: contextvars.ContextVar 对象实例
        default: 当 ContextVar 为空时的默认值
    
    Example:
        from contextvars import ContextVar
        from pyspring.core.log import register_context_var

        request_id_ctx = ContextVar("request_id", default=None)
        register_context_var("request_id", request_id_ctx, default="N/A")
    """
    ContextRegistry.register(key, context_var, default)
