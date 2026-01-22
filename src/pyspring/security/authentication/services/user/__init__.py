"""
User services
"""
from pyspring.security.authentication.services.user.manager import DefaultUserManagerService

# Backward compatibility alias
UserManager = DefaultUserManagerService

__all__ = ['DefaultUserManagerService', 'UserManager']
