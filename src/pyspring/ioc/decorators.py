from typing import Optional, Type

def Component(cls: Optional[Type] = None, *, name: Optional[str] = None, singleton: bool = True):
    """
    Decorator to mark a class as a component managed by the IoC container.
    """
    def wrapper(cls):
        setattr(cls, "__pyspring_component__", True)
        setattr(cls, "__pyspring_name__", name)
        setattr(cls, "__pyspring_singleton__", singleton)
        return cls

    if cls is None:
        return wrapper
    return wrapper(cls)

def Service(cls: Optional[Type] = None, *, name: Optional[str] = None):
    """Alias for Component, usually for business logic (Singleton by default)"""
    return Component(cls, name=name, singleton=True)

def Repository(cls: Optional[Type] = None, *, name: Optional[str] = None):
    """Alias for Component, usually for data access (Singleton by default)"""
    return Component(cls, name=name, singleton=True)

def Bean(cls: Optional[Type] = None, *, name: Optional[str] = None):
    """Alias for Factory-like components (Non-singleton/Prototype by default is not standard Spring but often used for factories. 
    However, Spring Beans are singletons by default. Here we use it for whatever user specifies)"""
    return Component(cls, name=name, singleton=True)


def ComponentScan(packages: list[str]):
    """
    Decorator to configure component scanning packages.
    Usually used on the main application class or a configuration class.
    
    Example:
        @ComponentScan(['app.services', 'app.controllers'])
        class AppConfig:
            pass
    """
    def wrapper(cls):
        setattr(cls, "__pyspring_component_scan__", packages)
        return cls
    return wrapper
