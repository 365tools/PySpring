"""
PySpring Security 模块 ORM 表定义

统一管理所有安全相关的数据库表：
- 用户表（User）
- 角色表（Role）
- 权限表（Permission）
- 用户角色关联表（UserRole）
- 角色权限关联表（RolePermission）
- Token 黑名单表（TokenBlacklist）
- Refresh Token 表（RefreshToken）
"""

from pyspring.repositories.db.models.common.define import (
    BasePermissionTable,
    BaseRefreshTokenTable,
    BaseRolePermissionTable,
    BaseRoleTable,
    BaseTokenBlacklistTable,
    BaseUserRoleTable,
    BaseUserTable,
)

# ============================================================
# 用户、角色、权限表
# ============================================================


class UserTable(BaseUserTable):
    """
    用户表模型（数据库）

    继承自 BaseUserTable，提供基础的用户字段
    """

    __tablename__ = "pyspring_user"


class RoleTable(BaseRoleTable):
    """
    角色表模型（数据库）

    继承自 BaseRoleTable，提供基础的角色字段
    """

    __tablename__ = "pyspring_role"


class PermissionTable(BasePermissionTable):
    """
    权限表模型（数据库）

    继承自 BasePermissionTable，提供基础的权限字段
    """

    __tablename__ = "pyspring_permission"


class UserRoleTable(BaseUserRoleTable):
    """
    用户角色关联表模型（数据库）

    继承自 BaseUserRoleTable，建立用户和角色的多对多关系
    使用业务标识符关联，无外键约束
    """

    __tablename__ = "pyspring_user_role"


class RolePermissionTable(BaseRolePermissionTable):
    """
    角色权限关联表模型（数据库）

    继承自 BaseRolePermissionTable，建立角色和权限的多对多关系
    使用业务代码关联，无外键约束
    """

    __tablename__ = "pyspring_role_permission"


# ============================================================
# Token 相关表
# ============================================================


class TokenBlacklistTable(BaseTokenBlacklistTable):
    """
    Token 黑名单表（已撤销的 Token）

    用于存储被撤销的 Access Token，防止其继续使用
    """

    __tablename__ = "pyspring_token_blacklist"

    def __repr__(self):
        return f"<TokenBlacklist(id={self.id}, user_id={self.user_id}, expires_at={self.expires_at})>"


class RefreshTokenTable(BaseRefreshTokenTable):
    """
    Refresh Token 表

    用于存储长期有效的 Refresh Token，用于刷新 Access Token
    """

    __tablename__ = "pyspring_refresh_token"

    def __repr__(self):
        return f"<RefreshToken(id={self.id}, user_id={self.user_id}, expires_at={self.expires_at}, is_revoked={self.is_revoked})>"


# ============================================================
# 导出所有表
# ============================================================

__all__ = [
    # 用户、角色、权限
    "UserTable",
    "RoleTable",
    "PermissionTable",
    "UserRoleTable",
    "RolePermissionTable",
    # Token
    "TokenBlacklistTable",
    "RefreshTokenTable",
]
