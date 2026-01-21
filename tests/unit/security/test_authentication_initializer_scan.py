"""
Test AuthenticationInitializer scanning in IoC container.
"""
from unittest.mock import MagicMock

from pyspring.ioc.manager import AppContainerManager
from pyspring.security.authentication.core.interfaces import IAuthenticationProvider, ISecurityContextValidator
from pyspring.security.authentication.web.chain import AuthenticationChain

from pyspring.core.abstracts.interfaces.ISingleton import ISingletonService
from pyspring.core.abstracts.interfaces.initializer.startup import IStartupInitializer
from pyspring.security.authentication.core.initializer import AuthenticationInitializer
from pyspring.security.authentication.services.context_validator import SecurityContextManagerService


# Mock implementation for IAuthenticationProvider
class MockAuthenticationProvider(IAuthenticationProvider, ISingletonService):
    def __init__(self, name="mock_provider"):
        self.name = name

    async def authenticate(self, request: object) -> object:
        return MagicMock()


# Mock implementation for ISecurityContextValidator
class MockSecurityContextValidator(ISecurityContextValidator, ISingletonService):
    def __init__(self, name="mock_validator"):
        self.name = name

    async def validate(self, context_data: dict) -> bool:
        return True

    @property
    def name(self) -> str:
        return self._name

    @name.setter
    def name(self, value: str):
        self._name = value


def test_scan_initializer_inheritance():
    """Test that AuthenticationInitializer inherits from correct interfaces."""
    assert issubclass(AuthenticationInitializer, IStartupInitializer)
    assert issubclass(AuthenticationInitializer, ISingletonService)


async def test_ioc_scan_and_initialize_authentication_initializer():
    """Test if IoC container can find, register, and initialize AuthenticationInitializer."""
    ioc_manager = AppContainerManager()

    # Register mock services for dependencies
    ioc_manager.register_service(AuthenticationChain, instance=MagicMock(spec=AuthenticationChain))
    ioc_manager.register_service(SecurityContextManagerService, instance=MagicMock(spec=SecurityContextManagerService))
    ioc_manager.register_service(MockAuthenticationProvider)  # Register a mock provider
    ioc_manager.register_service(MockSecurityContextValidator)  # Register a mock validator

    # Register all services, including AuthenticationInitializer
    ioc_manager.register_all_services()

    # Get the AuthenticationInitializer instance from the container
    initializer_instance = ioc_manager.get_service(AuthenticationInitializer)

    assert isinstance(initializer_instance, AuthenticationInitializer)

    # Ensure dependencies were correctly injected (mock objects)
    assert isinstance(initializer_instance.auth_chain, MagicMock)
    assert isinstance(initializer_instance.context_manager, MagicMock)
    assert len(initializer_instance.authentication_providers) == 1
    assert isinstance(initializer_instance.authentication_providers[0], MockAuthenticationProvider)

    # Run the initializer
    await initializer_instance.initialize()

    # Verify that auth_chain.register_providers was called with the mock provider
    initializer_instance.auth_chain.register_providers.assert_called_once()
    registered_providers = initializer_instance.auth_chain.register_providers.call_args[0][0]
    assert len(registered_providers) == 1
    assert isinstance(registered_providers[0], MockAuthenticationProvider)

    # Verify that context_manager.register was called with the mock validator
    initializer_instance.context_manager.register.assert_called_once()
    registered_validator = initializer_instance.context_manager.register.call_args[0][0]
    assert isinstance(registered_validator, MockSecurityContextValidator)
