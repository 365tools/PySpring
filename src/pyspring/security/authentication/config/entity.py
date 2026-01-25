from typing import Type, List, Optional

from pyspring.config_manager import ConfigManager
from pyspring.ioc.annotations import Component, ConditionalOnMissingBean
# ORM Models
from pyspring.repositories.db.models.common.define import (
    BaseUserTable, BaseRoleTable, BasePermissionTable,
    BaseUserRoleTable, BaseRolePermissionTable
)
# Pydantic Schemas
from pyspring.security.authentication.contracts.request import (
    LoginRequest
)
from pyspring.security.authentication.contracts.response import (
    LoginResponse, TokenResponse, LogoutResponse, UserInfo, User, Role, Permission
)
from pyspring.security.orm.tables import (
    UserTable, RoleTable, PermissionTable,
    UserRoleTable, RolePermissionTable
)


@Component()
@ConditionalOnMissingBean
class SecurityEntityConfiguration:
    """
    Component for holding Security Entity types (Tables/Models) and Pydantic schemas.
    Default services use this component to know which classes to use for ORM operations and validation.
    
    设计说明：
    - 使用 @Component 让扫描器能够识别这个配置类
    - 使用 @ConditionalOnMissingBean 让用户可以完全替换这个配置类
    - 不是 @dataclass，是一个普通的配置类，方便继承和自定义
    """

    def __init__(
            self,
            # ==================== ORM Models (数据库表) ====================
            user_orm_model: Type[BaseUserTable] = UserTable,
            role_orm_model: Type[BaseRoleTable] = RoleTable,
            permission_orm_model: Type[BasePermissionTable] = PermissionTable,
            user_role_orm_model: Type[BaseUserRoleTable] = UserRoleTable,
            role_permission_orm_model: Type[BaseRolePermissionTable] = RolePermissionTable,
            # ==================== Pydantic Schemas (API 交互) ====================
            # Requests
            login_request_schema: Type[LoginRequest] = LoginRequest,
            # Responses
            login_response_schema: Type[LoginResponse] = LoginResponse,
            token_response_schema: Type[TokenResponse] = TokenResponse,
            logout_response_schema: Type[LogoutResponse] = LogoutResponse,
            # Data Structures
            user_info_schema: Type[UserInfo] = UserInfo,
            user_schema: Type[User] = User,
            role_schema: Type[Role] = Role,
            permission_schema: Type[Permission] = Permission,
            # ==================== 登录标识符字段配置 ====================
            identifier_fields: Optional[List[str]] = None
    ):
        self.user_orm_model = user_orm_model
        self.role_orm_model = role_orm_model
        self.permission_orm_model = permission_orm_model
        self.user_role_orm_model = user_role_orm_model
        self.role_permission_orm_model = role_permission_orm_model

        self.login_request_schema = login_request_schema

        self.login_response_schema = login_response_schema
        self.token_response_schema = token_response_schema
        self.logout_response_schema = logout_response_schema

        self.user_info_schema = user_info_schema
        self.user_schema = user_schema
        self.role_schema = role_schema
        self.permission_schema = permission_schema

        # 登录标识符字段配置（从配置文件加载或使用默认值）
        if identifier_fields is None:
            # 从配置文件加载
            try:
                config = ConfigManager.load_config('security')
                identifier_fields = config.get('authentication', {}).get(
                    'identifier_fields',
                    ['username', 'email', 'user_id']  # 默认值（包含框架标准字段）
                )
            except Exception:
                # 如果加载失败，使用默认值
                identifier_fields = ['username', 'email', 'user_id']
        self.identifier_fields = identifier_fields
