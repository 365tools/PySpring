"""
代理生成器，用于创建 AOP 代理对象
"""
import functools
import re
from typing import Any, List, Callable


class AopProxy:
    """AOP 代理包装器"""

    def __init__(self, target: Any, advices: List[dict]):
        self._target = target
        self._advices = advices  # List of {'type': 'before', 'method': func, 'pointcut': pattern}

    def __getattr__(self, name):
        # 获取目标属性/方法
        attr = getattr(self._target, name)

        # 如果不是方法，直接返回
        if not callable(attr) or name.startswith('_'):
            return attr

        # 生成包装方法
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
                # 3. After Throwing (Future Feature)
                raise e

            # 4. After Advice
            for advice in self._advices:
                if advice['type'] == 'after' and self._match(advice['pointcut'], method_name):
                    advice['func'](self._target, method_name, result)

            return result

        return wrapper

    @staticmethod
    def _match(pattern: str, method_name: str) -> bool:
        # 简单通配符匹配
        # 将 * 转换为 .*
        regex = pattern.replace("*", ".*")
        try:
            return re.match(f"^{regex}$", method_name) is not None
        except re.error:
            return False
