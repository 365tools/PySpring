from typing import Protocol


class IComponent(Protocol):
    """
    Component Interface.
    All classes that need to be managed by the IoC container should implement this interface
    or be decorated with @Component.
    """
    pass
