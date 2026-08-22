"""
条件装饰器

定义用于条件注册的装饰器：ConditionalOnMissingBean
这些装饰器用于实现条件化的组件注册。
"""

from typing import Callable, TypeVar

T = TypeVar("T")


def ConditionalOnMissingBean(target_or_type: type | None = None) -> Callable[[T], T]:
    """
    条件Bean装饰器（仅当指定类型的Bean不存在时，才注册此Bean/组件）。

    用于提供默认实现，允许用户通过提供同名接口实现来覆盖默认Bean。

    支持的用法：
    1. 指定接口类型：@ConditionalOnMissingBean(IAuthProvider) 装饰类/方法
       当容器中不存在 IAuthProvider 的实现时才注册。
    2. 无参数带括号：@ConditionalOnMissingBean() 装饰类
       自动使用被装饰的类作为检查类型。

    Args:
        target_or_type: 检查的类型（bean_type）。
            - 如果提供，则作为检查类型，返回装饰器。
            - 如果为 None（无参数），装饰器自动推断被装饰类作为检查类型。

    设计说明：
    - 本装饰器**始终返回装饰器**（Callable[[T], T]），不在调用时直接应用，
      保证类型可推断（T 由被装饰对象绑定），避免 (Unknown) 类型错误。
    - 因此使用时应**始终带括号**：`@ConditionalOnMissingBean(SomeType)` 或
      `@ConditionalOnMissingBean()`。不支持 `@ConditionalOnMissingBean`（无括号）。
    """

    def apply_decorator(target: T, bean_type: type) -> T:
        """应用装饰器逻辑"""
        setattr(target, "__pyspring_conditional_on_missing_bean__", bean_type)

        # 如果装饰的是类（不是方法），自动标记为组件，
        # 这样扫描器才能识别它，即使它不继承 IManaged。
        if isinstance(target, type):
            setattr(target, "__pyspring_component__", True)

        return target

    # 有参数：target_or_type 作为检查类型，返回装饰器
    if target_or_type is not None:
        bean_type = target_or_type

        def decorator(target: T) -> T:
            return apply_decorator(target, bean_type)

        return decorator

    # 无参数（带括号）：自动推断检查类型
    def decorator(target: T) -> T:
        # 被装饰的是类则用类本身，否则用 object（兼容旧行为）
        bean_type = target if isinstance(target, type) else object
        return apply_decorator(target, bean_type)

    return decorator


__all__ = [
    "ConditionalOnMissingBean",
]
