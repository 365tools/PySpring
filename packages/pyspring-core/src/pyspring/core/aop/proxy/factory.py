from typing import Any

from .wrapper import AopProxy


def create_proxy(target: Any, aspects: list[Any]) -> Any:
    """
    为目标对象创建代理
    """
    advices = []

    for aspect_inst in aspects:
        # 扫描 aspect 实例的方法
        for name in dir(aspect_inst):
            method = getattr(aspect_inst, name)
            advice_meta = getattr(method, "__pyspring_advice__", None)
            if advice_meta:
                if advice_meta.__class__.__name__ == 'Before':
                    advices.append({'type': 'before', 'pointcut': advice_meta.pointcut, 'func': method})
                elif advice_meta.__class__.__name__ == 'After':
                    advices.append({'type': 'after', 'pointcut': advice_meta.pointcut, 'func': method})
                elif advice_meta.__class__.__name__ == 'Around':
                    advices.append({'type': 'around', 'pointcut': advice_meta.pointcut, 'func': method})

    if not advices:
        return target

    return AopProxy(target, advices)
