from abc import ABC, abstractmethod
from typing import Any

from pyspring.core.abstracts.interfaces.ISingleton import ISingletonService


class ILoginProvider(ISingletonService, ABC):
    """
    Interface for authentication providers that handle login requests.
    
    This interface defines the contract for providers that can authenticate a user
    based on a specific request object (e.g., username/password, API key, etc.).
    """

    @abstractmethod
    def supports(self, request: Any) -> bool:
        """
        Check if this provider supports the given authentication request.
        
        Args:
            request: The authentication request object.
        
        Returns:
            True if the provider supports the request, False otherwise.
        """
        pass

    @abstractmethod
    async def authenticate(self, request: Any) -> Any:
        """
        Authenticate the user based on the request.
        
        Args:
            request: The authentication request object.
                     For example, PasswordLoginProvider expects a LoginRequest (pydantic model).
        
        Returns:
            AuthenticationResult: The result of the authentication process.
        
        Args:
            request: The login request object. The type depends on the specific implementation.
                     For example, DefaultPasswordAuthenticationProvider expects a LoginRequest (pydantic model).
                     You can pass dict, custom objects, etc., as long as your Provider handles it.
            
        Returns:
            Any: The authenticated User object (usually a DB model or Pydantic model).

        Raises:
            HTTPException: Raised when authentication fails.
        """
        pass
