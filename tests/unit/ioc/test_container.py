"""
PySpring Unit Tests - IoC Container
"""
import pytest
from pyspring.ioc.manager import AppContainerManager

from pyspring.core.abstracts.interfaces.ISingleton import ISingletonService


# Reset singleton for testing
@pytest.fixture
def container():
    AppContainerManager._instance = None
    manager = AppContainerManager()
    return manager


def test_singleton_instance(container):
    """Test that the container is a singleton"""
    manager1 = AppContainerManager()
    manager2 = AppContainerManager()
    assert manager1 is manager2


def test_register_and_get_bean(container):
    """Test registering and retrieving a simple bean"""

    class TestService(ISingletonService):  # Make it a singleton service for registration
        pass

    container.register_service(TestService)

    instance = container.get_service(TestService)
    assert isinstance(instance, TestService)

    instance2 = container.get_service(TestService)
    assert instance is instance2  # Should be the same instance for SingletonService


def test_dependency_injection_simple(container):
    """Test simple dependency injection via constructor"""

    class Dependency(ISingletonService):
        def __init__(self):
            self.value = "dependency_value"

    class ServiceWithDependency(ISingletonService):
        def __init__(self, dependency: Dependency):
            self.dependency = dependency

    container.register_service(Dependency)
    container.register_service(ServiceWithDependency)

    service_instance = container.get_service(ServiceWithDependency)
    assert isinstance(service_instance, ServiceWithDependency)
    assert isinstance(service_instance.dependency, Dependency)
    assert service_instance.dependency.value == "dependency_value"

    # Ensure it's a singleton
    service_instance2 = container.get_service(ServiceWithDependency)
    assert service_instance is service_instance2
    assert service_instance.dependency is service_instance2.dependency
