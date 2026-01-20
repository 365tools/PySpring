from typing import Optional, Type, Any


def component(cls: Optional[Type] = None, *, name: Optional[str] = None, singleton: bool = True):
    """
    Decorator to mark a class as a component managed by the IoC container.
    """

    def wrapper(target_cls):
        setattr(target_cls, "__pyspring_component__", True)
        setattr(target_cls, "__pyspring_name__", name)
        setattr(target_cls, "__pyspring_singleton__", singleton)
        return target_cls

    if cls is None:
        return wrapper
    return wrapper(cls)


def service(cls: Optional[Type] = None, *, name: Optional[str] = None):
    """Alias for Component, usually for business logic (Singleton by default)"""
    return component(cls, name=name, singleton=True)


def repository(cls: Optional[Type] = None, *, name: Optional[str] = None):
    """Alias for Component, usually for data access (Singleton by default)"""
    return component(cls, name=name, singleton=True)


def bean(cls: Optional[Type] = None, *, name: Optional[str] = None):
    """
    Mark a class or method as a Bean.
    
    Usage:
    @Bean
    class MyService: ...
    
    @Bean
    def my_bean(self): ...
    """

    def wrapper(target):
        if hasattr(target, "__call__") and not isinstance(target, type):
            # It's a method/function
            setattr(target, "__pyspring_bean__", True)
            setattr(target, "__pyspring_bean_name__", name)
        else:
            # It's a class
            setattr(target, "__pyspring_component__", True)
            setattr(target, "__pyspring_name__", name)
            setattr(target, "__pyspring_singleton__", True)
        return target

    if cls is None:
        return wrapper
    return wrapper(cls)


def configuration(cls: Optional[Type] = None):
    """
    Mark a class as a Configuration source.
    """

    def wrapper(target_cls):
        setattr(target_cls, "__pyspring_component__", True)
        setattr(target_cls, "__pyspring_configuration__", True)
        setattr(target_cls, "__pyspring_singleton__", True)
        return target_cls

    if cls is None:
        return wrapper
    return wrapper(cls)


def conditional_on_missing_bean(annotation: Any):
    """
    Register the bean only if the specified class/interface is not already registered.
    """

    def wrapper(f):
        setattr(f, "__pyspring_conditional_on_missing_bean__", annotation)
        return f

    return wrapper


def component_scan(packages: list[str]):
    """
    Decorator to configure component scanning packages.
    Usually used on the main application class or a configuration class.

    Example:
        @component_scan(['app.services', 'app.controllers'])
        class AppConfig:
            pass
    """

    def wrapper(cls):
        setattr(cls, "__pyspring_component_scan__", packages)
        return cls

    return wrapper


# Aliases for backward compatibility or Java-style preference
Component = component
Service = service
Repository = repository
Bean = bean
Configuration = configuration
ConditionalOnMissingBean = conditional_on_missing_bean
ComponentScan = component_scan

__all__ = [
    'component', 'service', 'repository', 'bean', 'configuration', 'conditional_on_missing_bean', 'component_scan',
    'Component', 'Service', 'Repository', 'Bean', 'Configuration', 'ConditionalOnMissingBean', 'ComponentScan',
]
