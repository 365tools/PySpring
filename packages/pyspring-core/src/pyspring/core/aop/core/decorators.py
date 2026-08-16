from .models import After, Around, Before


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
