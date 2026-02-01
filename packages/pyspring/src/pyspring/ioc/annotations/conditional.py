"""
条件装饰器

定义用于条件注册的装饰器：ConditionalOnMissingBean
这些装饰器用于实现条件化的组件注册。
"""
from abc import ABCMeta
from typing import TypeVar, Type, Callable, Union

T = TypeVar('T')


def ConditionalOnMissingBean(
        target_or_type: Union[Type[T], Callable[..., T], type, None] = None
) -> Union[Callable[[Union[Type[T], Callable[..., T]]], Union[Type[T], Callable[..., T]]], Type[T], Callable[..., T]]:
    """
    条件Bean装饰器（支持装饰类和方法，支持无参数调用）
    
    仅当指定类型的Bean不存在时，才注册此Bean/组件。
    用于提供默认实现，允许用户覆盖。
    
    支持三种使用方式：
    1. 无参数带括号：@ConditionalOnMissingBean()
    2. 无参数不带括号：@ConditionalOnMissingBean
    3. 指定类型：@ConditionalOnMissingBean(IAuthProvider)
    
    Args:
        target_or_type: 
            - 如果是 None，则为无参数模式（带括号）
            - 如果是类型，则可能是：
              a) 指定类型模式 @ConditionalOnMissingBean(IAuthProvider)
              b) 直接装饰模式 @ConditionalOnMissingBean (被装饰的类作为参数)
            - 如果是可调用对象但不是类型，则为方法装饰
    
    使用场景1: 装饰 @Bean 方法（在配置类中）
        @Configuration
        class DefaultConfig:
            @Bean
            @ConditionalOnMissingBean(IAuthProvider)
            def default_auth_provider(self) -> IAuthProvider:
                return DefaultAuthProvider()
    
    使用场景2: 装饰组件类 - 指定接口类型
        @ConditionalOnMissingBean(ILoginProvider)
        class DefaultPasswordLoginProvider(ILoginProvider):
            '''用户可以通过提供自己的 ILoginProvider 实现来替换此默认类'''
            pass
    
    使用场景3: 装饰组件类 - 不带括号（自动推断）
        @ConditionalOnMissingBean
        class SecurityEntityConfiguration:
            '''自动使用 SecurityEntityConfiguration 作为检查类型'''
            pass
            
    使用场景4: 装饰组件类 - 带括号（自动推断）
        @ConditionalOnMissingBean()
        class SecurityEntityConfiguration:
            '''自动使用 SecurityEntityConfiguration 作为检查类型'''
            pass
    """

    def apply_decorator(target: Union[Type[T], Callable[..., T]], bean_type: type) -> Union[Type[T], Callable[..., T]]:
        """应用装饰器逻辑"""
        setattr(target, "__pyspring_conditional_on_missing_bean__", bean_type)

        # 🔧 如果装饰的是类（不是方法），自动标记为组件
        # 这样扫描器才能识别它，即使它不继承 IManaged
        if isinstance(target, type):
            setattr(target, "__pyspring_component__", True)

        return target

    # 情况1: 无参数带括号模式 @ConditionalOnMissingBean()
    if target_or_type is None:
        def decorator(target: Union[Type[T], Callable[..., T]]) -> Union[Type[T], Callable[..., T]]:
            # 自动使用被装饰的类作为bean_type
            # 如果是类，使用类本身；如果是方法，使用 object（兼容旧行为）
            bean_type = target if isinstance(target, type) else object
            return apply_decorator(target, bean_type)

        return decorator

    # 情况2: 直接装饰函数/方法 @ConditionalOnMissingBean
    # 注意：这里 callable(target_or_type) 会对类也返回 True，所以要先排除类
    if callable(target_or_type) and not isinstance(target_or_type, type):
        # 这是一个方法或函数，直接装饰
        return apply_decorator(target_or_type, object)

    # 情况3: target_or_type 是一个类
    if isinstance(target_or_type, type):
        # 需要判断这是：
        # a) 直接装饰：@ConditionalOnMissingBean 应用于类（类作为第一个参数传入）
        # b) 指定类型：@ConditionalOnMissingBean(SomeInterface) 应用于实现类

        # 判断依据：
        # - 如果是直接装饰，那么 target_or_type 就是要被装饰的类
        # - 如果是指定类型，那么 target_or_type 是接口/抽象类
        # 
        # 当 @ConditionalOnMissingBean 不带括号直接装饰类时：
        #   @ConditionalOnMissingBean
        #   class MyClass:
        #       pass
        # Python 会调用 ConditionalOnMissingBean(MyClass)
        # 
        # 当用作 @ConditionalOnMissingBean(Interface) 时：
        #   @ConditionalOnMissingBean(Interface)
        #   class MyClass:
        #       pass
        # Python 会先调用 ConditionalOnMissingBean(Interface) 返回装饰器
        # 然后用这个装饰器装饰 MyClass
        #
        # 关键区别：在直接装饰时，我们要立即返回装饰后的类
        #          在指定类型时，我们要返回一个装饰器函数
        #
        # 如何区分？检查是否是抽象类或接口
        # 如果是抽象类或 Protocol，很可能是接口类型
        # 但是！实现类也可能继承抽象类，所以不能仅凭 is_abstract 判断
        # 更好的判断方式：检查类是否有抽象方法
        # 如果有未实现的抽象方法，则是接口；否则是具体实现

        is_abstract_interface = (
                                        isinstance(target_or_type, ABCMeta) and
                                        len(getattr(target_or_type, '__abstractmethods__', set())) > 0
                                ) or getattr(target_or_type, '_is_protocol', False)

        if is_abstract_interface:
            # 这是接口类型（有未实现的抽象方法），返回装饰器
            bean_type = target_or_type

            def decorator(target: Union[Type[T], Callable[..., T]]) -> Union[Type[T], Callable[..., T]]:
                return apply_decorator(target, bean_type)

            return decorator

        # 否则，假设这是直接装饰（包括实现了所有抽象方法的具体类）
        # 使用类本身作为 bean_type
        return apply_decorator(target_or_type, target_or_type)

    # 兜底：返回装饰器
    def decorator(target: Union[Type[T], Callable[..., T]]) -> Union[Type[T], Callable[..., T]]:
        bean_type = target_or_type if target_or_type is not None else target
        return apply_decorator(target, bean_type)

    return decorator


__all__ = [
    'ConditionalOnMissingBean',
]
