import uuid

from sqlalchemy import Column, String, Boolean, INT, TEXT, DateTime
from sqlalchemy.sql.schema import ForeignKey

from pyspring.repositories.db.models.common.define import Base


class UserTable(Base):
    """
    用户表模型（数据库）
    """
    __tablename__ = "user"

    id = Column(INT, primary_key=True, autoincrement=True)
    uuid = Column(String(36), default=lambda: str(uuid.uuid4()), unique=True, index=True, nullable=True)
    user_id = Column(String, unique=True, index=True, nullable=True)
    first_name = Column(String, nullable=True)
    last_name = Column(String, nullable=True)
    password = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=True)


class RoleTable(Base):
    """
    角色表模型（数据库）
    """
    __tablename__ = "role"

    id = Column(INT, primary_key=True, autoincrement=True)
    code = Column(String, unique=True, index=True, nullable=False)
    name = Column(String, nullable=False)
    description = Column(String, nullable=False)
    status = Column(Boolean, nullable=False)


class PermissionTable(Base):
    """
    权限表模型（数据库）
    """
    __tablename__ = "permission"

    id = Column(INT, primary_key=True, autoincrement=True)
    code = Column(String, unique=True, index=True, nullable=False)
    name = Column(String, nullable=False)
    description = Column(String, nullable=False)
    status = Column(Boolean, nullable=False)


class UserRoleTable(Base):
    """
    用户角色表模型（数据库）
    """
    __tablename__ = "user_role"

    id = Column(INT, primary_key=True, autoincrement=True)
    user_id = Column(INT, ForeignKey('user.id'), nullable=False)
    role_id = Column(INT, ForeignKey('role.id'), nullable=False)


class UserDeviceTable(Base):
    """
    用户设备表模型（数据库）
    """
    __tablename__ = "user_device"

    id = Column(INT, primary_key=True, autoincrement=True)
    user_id = Column(INT, ForeignKey('user.id'), nullable=False)
    name = Column(String, nullable=False)
    fingerprint = Column(TEXT, nullable=False, unique=True, index=True)
    status = Column(Boolean, nullable=False, default=True)
    approved = Column(Boolean, nullable=False, default=False, comment="是否已审批通过")
    expires_at = Column(DateTime, nullable=True, comment="过期时间")
    requested_duration_days = Column(INT, nullable=False, default=7, comment="申请的访问时长（天）")
    approved_at = Column(DateTime, nullable=True, comment="审批时间")


class RolePermissionTable(Base):
    """
    角色权限表模型（数据库）
    """
    __tablename__ = "role_permission"

    id = Column(INT, primary_key=True, autoincrement=True)
    role_code = Column(INT, ForeignKey('role.code'), nullable=False)
    permission_code = Column(INT, ForeignKey('permission.code'), nullable=False)
