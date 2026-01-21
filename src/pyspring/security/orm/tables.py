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

import uuid
from datetime import datetime, UTC

from sqlalchemy import Column, String, INT, Integer, DateTime, Text
from sqlalchemy.sql.schema import ForeignKey

from pyspring.repositories.db.models.common.define import (
    Base,
    BaseUserTable,
    BaseRoleTable,
    BasePermissionTable,
    BaseUserRoleTable,
    BaseRolePermissionTable
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

    uuid = Column(String(36), default=lambda: str(uuid.uuid4()), unique=True, index=True, nullable=True)


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
    """
    __tablename__ = "pyspring_user_role"

    user_id = Column(INT, ForeignKey('pyspring_user.id'), nullable=False)
    role_id = Column(INT, ForeignKey('pyspring_role.id'), nullable=False)


class RolePermissionTable(BaseRolePermissionTable):
    """
    角色权限关联表模型（数据库）
    
    继承自 BaseRolePermissionTable，建立角色和权限的多对多关系
    """
    __tablename__ = "pyspring_role_permission"

    role_code = Column(String, ForeignKey('pyspring_role.code'), nullable=False)
    permission_code = Column(String, ForeignKey('pyspring_permission.code'), nullable=False)


# ============================================================
# Token 相关表
# ============================================================

class TokenBlacklistTable(Base):
    """
    Token 黑名单表（已撤销的 Token）
    
    用于存储被撤销的 Access Token，防止其继续使用
    """
    __tablename__ = "token_blacklist"

    id = Column(Integer, primary_key=True, autoincrement=True, comment="主键ID")
    token = Column(String(500), unique=True, nullable=False, index=True, comment="Token字符串")
    user_id = Column(Integer, nullable=False, index=True, comment="用户ID")
    expires_at = Column(DateTime, nullable=False, comment="Token过期时间")
    reason = Column(String(200), nullable=True, comment="撤销原因")

    def __repr__(self):
        return f"<TokenBlacklist(id={self.id}, user_id={self.user_id}, expires_at={self.expires_at})>"


class RefreshTokenTable(Base):
    """
    Refresh Token 表
    
    用于存储长期有效的 Refresh Token，用于刷新 Access Token
    """
    __tablename__ = "refresh_token"

    id = Column(Integer, primary_key=True, autoincrement=True, comment="主键ID")
    token = Column(String(500), unique=True, nullable=False, index=True, comment="Refresh Token字符串")
    user_id = Column(Integer, nullable=False, index=True, comment="用户ID")
    user_email = Column(String(100), nullable=False, comment="用户邮箱")
    roles = Column(Text, nullable=True, comment="用户角色(JSON数组)")
    issued_at = Column(DateTime, nullable=False, default=lambda: datetime.now(UTC), comment="签发时间")
    expires_at = Column(DateTime, nullable=False, comment="过期时间")
    revoke_reason = Column(String(200), nullable=True, comment="撤销原因(如: 用户重新登录、主动登出、安全原因等)")

    def __repr__(self):
        return f"<RefreshToken(id={self.id}, user_id={self.user_id}, expires_at={self.expires_at})>"


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
