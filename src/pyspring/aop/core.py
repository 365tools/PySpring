from typing import Any


class JoinPoint:
    def __init__(self, target: Any, method_name: str, args: tuple, kwargs: dict):
        self.target = target
        self.method_name = method_name
        self.args = args
        self.kwargs = kwargs

    def proceed(self):
        """执行原始方法"""
        method = getattr(self.target, self.method_name)
        # 这里需要注意，如果是通过代理调用的，target 可能是原始对象
        # 在 AOP 代理中，proceed 通常意味着继续调用链或调用目标
        # 简单实现直接调用目标方法
        return method(*self.args, **self.kwargs)


class Aspect:
    """切面基类"""
    pass


class Advice:
    """通知基类"""

    def __init__(self, pointcut: str):
        self.pointcut = pointcut


class Before(Advice):
    pass


class After(Advice):
    pass


class Around(Advice):
    pass


def aspect(cls):
    """标记类为切面"""
    setattr(cls, "__pyspring_aspect__", True)
    return cls


def before(pointcut: str):
    def decorator(func):
        setattr(func, "__pyspring_advice__", Before(pointcut))
        return func

    return decorator


def after(pointcut: str):
    def decorator(func):
        setattr(func, "__pyspring_advice__", After(pointcut))
        return func

    return decorator


def around(pointcut: str):
    def decorator(func):
        setattr(func, "__pyspring_advice__", Around(pointcut))
        return func

    return decorator
