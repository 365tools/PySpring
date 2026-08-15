from typing import Any


class JoinPoint:
    def __init__(self, target: Any, method_name: str, args: tuple[object, ...], kwargs: dict[str, object]):
        self.target = target
        self.method_name = method_name
        self.args = args
        self.kwargs = kwargs

    def proceed(self):
        """执行原始方法"""
        method = getattr(self.target, self.method_name)
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
