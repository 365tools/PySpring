from typing import Any, List

from fastapi import HTTPException, status

from pyspring.security.authentication.contracts.login import ILoginProvider


class DefaultLoginProviderManager(ILoginProvider):
    """
    Manager for multiple authentication providers.
    It iterates through registered providers and delegates authentication to the first one that supports the request.
    """

    def __init__(self, providers: List[ILoginProvider]):
        self.providers = providers

    def supports(self, request: Any) -> bool:
        # Manager itself supports if any of his children supports
        return any(provider.supports(request) for provider in self.providers)

    async def authenticate(self, request: Any) -> Any:
        for provider in self.providers:
            if provider.supports(request):
                return await provider.authenticate(request)

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"No LoginProvider found for request type: {type(request)}"
        )
