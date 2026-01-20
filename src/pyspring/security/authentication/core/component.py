from dataclasses import dataclass
from typing import Type

# ORM Models
from pyspring.repositories.db.models.common.define import (
    BaseUserTable, BaseRoleTable, BasePermissionTable,
    BaseUserRoleTable, BaseRolePermissionTable
)
# Pydantic Schemas
from pyspring.security.authorization.contracts.schema.requests import (
    LoginRequest, UserInfo, User, Role, Permission
)
from pyspring.security.authorization.contracts.schema.response import (
    LoginResponse, TokenResponse, LogoutResponse
)
from pyspring.security.authorization.implementations.orm.tables import (
    UserTable, RoleTable, PermissionTable,
    UserRoleTable, RolePermissionTable
)


@dataclass
class SecurityEntityConfiguration:
    """
    Component for holding Security Entity types (Tables/Models) and Pydantic schemas.
    Default services use this component to know which classes to use for ORM operations and validation.
    """

    # ==================== ORM Models (数据库表) ====================
    user_orm_model: Type[BaseUserTable] = UserTable
    role_orm_model: Type[BaseRoleTable] = RoleTable
    permission_orm_model: Type[BasePermissionTable] = PermissionTable
    user_role_orm_model: Type[BaseUserRoleTable] = UserRoleTable
    role_permission_orm_model: Type[BaseRolePermissionTable] = RolePermissionTable

    # ==================== Pydantic Schemas (API 交互) ====================
    # Requests
    login_request_schema: Type[LoginRequest] = LoginRequest

    # Responses
    login_response_schema: Type[LoginResponse] = LoginResponse
    token_response_schema: Type[TokenResponse] = TokenResponse
    logout_response_schema: Type[LogoutResponse] = LogoutResponse

    # Data Structures
    user_info_schema: Type[UserInfo] = UserInfo
    user_schema: Type[User] = User
    role_schema: Type[Role] = Role
    permission_schema: Type[Permission] = Permission
