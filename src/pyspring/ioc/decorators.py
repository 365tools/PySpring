from typing import Optional, Type


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
    """Alias for Factory-like components (Non-singleton/Prototype by default is not standard Spring but often used for factories. 
    However, Spring Beans are singletons by default. Here we use it for whatever user specifies)"""
    return component(cls, name=name, singleton=True)


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
ComponentScan = component_scan

__all__ = [
    'component', 'service', 'repository', 'bean', 'component_scan',
    'Component', 'Service', 'Repository', 'Bean', 'ComponentScan',
]
