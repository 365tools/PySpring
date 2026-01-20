import uuid

from sqlalchemy import Column, String, INT
from sqlalchemy.sql.schema import ForeignKey

from pyspring.repositories.db.models.common.define import BaseUserTable, BaseRoleTable, BasePermissionTable, BaseUserRoleTable, BaseRolePermissionTable


class UserTable(BaseUserTable):
    """
    默认用户表模型（数据库）
    """
    __tablename__ = "pyspring_user"

    uuid = Column(String(36), default=lambda: str(uuid.uuid4()), unique=True, index=True, nullable=True)


class RoleTable(BaseRoleTable):
    """
    默认角色表模型（数据库）
    """
    __tablename__ = "pyspring_role"


class PermissionTable(BasePermissionTable):
    """
    默认权限表模型（数据库）
    """
    __tablename__ = "pyspring_permission"


class UserRoleTable(BaseUserRoleTable):
    """
    默认用户角色表模型（数据库）
    """
    __tablename__ = "pyspring_user_role"

    user_id = Column(INT, ForeignKey('pyspring_user.id'), nullable=False)
    role_id = Column(INT, ForeignKey('pyspring_role.id'), nullable=False)


class RolePermissionTable(BaseRolePermissionTable):
    """
    默认角色权限表模型（数据库）
    """
    __tablename__ = "pyspring_role_permission"

    role_code = Column(String, ForeignKey('pyspring_role.code'), nullable=False)
    permission_code = Column(String, ForeignKey('pyspring_permission.code'), nullable=False)
