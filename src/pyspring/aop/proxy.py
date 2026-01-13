"""
代理生成器，用于创建 AOP 代理对象
"""
import functools
from typing import Any, List, Callable


class AopProxy:
    """AOP 代理包装器"""

    def __init__(self, target: Any, advices: List[dict]):
        self._target = target
        self._advices = advices  # List of {'type': 'before', 'method': func, 'regex': pattern}

    def __getattr__(self, name):
        # 获取目标属性/方法
        attr = getattr(self._target, name)

        # 如果不是方法，直接返回
        if not callable(attr) or name.startswith('_'):
            return attr

        # 如果是方法，检查是否需要拦截
        # 这里做一个简单的匹配逻辑，实际应该更复杂
        return self._create_wrapper(name, attr)

    def _create_wrapper(self, method_name: str, original_method: Callable):
        @functools.wraps(original_method)
        def wrapper(*args, **kwargs):
            # 1. Before Advice
            for advice in self._advices:
                if advice['type'] == 'before' and self._match(advice['pointcut'], method_name):
                    advice['func'](self._target, method_name, args, kwargs)

            result = None
            try:
                # 2. Around & Execution
                # 简化实现：Around 暂时仅作为 Around-Execute
                # 实际 Around 应该控制是否 proceed
                executed = False
                for advice in self._advices:
                    if advice['type'] == 'around' and self._match(advice['pointcut'], method_name):
                        # Around 通知需要接收 proceed 回调
                        def proceed():
                            return original_method(*args, **kwargs)

                        result = advice['func'](proceed, self._target, method_name, args, kwargs)
                        executed = True
                        break  # 只执行第一个匹配的 around

                if not executed:
                    result = original_method(*args, **kwargs)

            except Exception as e:
                # 3. After Throwing (TODO)
                raise e

            # 4. After Advice
            for advice in self._advices:
                if advice['type'] == 'after' and self._match(advice['pointcut'], method_name):
                    advice['func'](self._target, method_name, result)

            return result

        return wrapper

    def _match(self, pattern: str, method_name: str) -> bool:
        # 简单通配符匹配
        import re
        # 将 * 转换为 .*
        regex = pattern.replace("*", ".*")
        return re.match(f"^{regex}$", method_name) is not None


def create_proxy(target: Any, aspects: List[Any]) -> Any:
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
