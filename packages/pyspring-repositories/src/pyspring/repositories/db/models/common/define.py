from datetime import UTC, datetime

from sqlalchemy import INT, TIMESTAMP, Boolean, Column, DateTime, Integer, String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """SQLAlchemy 基类"""

    version = Column(INT, nullable=True)
    active = Column(Boolean, nullable=False, default=True)
    deleted = Column(Boolean, nullable=False, default=False)
    creator = Column(String, nullable=False, default="system")
    created_time = Column(TIMESTAMP, nullable=False, default=lambda: datetime.now(UTC))
    modifier = Column(String, nullable=False, default="system")
    modified_time = Column(TIMESTAMP, nullable=False, default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC))


class BaseUserTable(Base):
    """
    用户表基类（抽象类）
    """
    __abstract__ = True

    id: Mapped[int] = mapped_column(INT, primary_key=True, autoincrement=True)
    user_id: Mapped[str] = mapped_column(String, unique=True, index=True, nullable=True)
    email: Mapped[str] = mapped_column(String, unique=True, index=True, nullable=True)
    password: Mapped[str] = mapped_column(String, nullable=False)
    first_name: Mapped[str] = mapped_column(String, nullable=True)
    last_name: Mapped[str] = mapped_column(String, nullable=True)
    uuid: Mapped[str] = mapped_column(String(36), unique=True, index=True, nullable=True)


class BaseRoleTable(Base):
    """
    角色表基类（抽象类）
    """
    __abstract__ = True

    id: Mapped[int] = mapped_column(INT, primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String, unique=True, index=True, nullable=False)
    name: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[str] = mapped_column(String, nullable=False)
    status: Mapped[bool] = mapped_column(Boolean, nullable=False)


class BasePermissionTable(Base):
    """
    权限表基类（抽象类）
    """
    __abstract__ = True

    id: Mapped[int] = mapped_column(INT, primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String, unique=True, index=True, nullable=False)
    name: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[str] = mapped_column(String, nullable=False)
    status: Mapped[bool] = mapped_column(Boolean, nullable=False)


class BaseUserRoleTable(Base):
    """
    用户角色关联表基类（抽象类）
    """
    __abstract__ = True

    id: Mapped[int] = mapped_column(INT, primary_key=True, autoincrement=True)
    user_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    role_code: Mapped[str] = mapped_column(String(50), nullable=False, index=True)


class BaseRolePermissionTable(Base):
    """
    角色权限关联表基类（抽象类）
    """
    __abstract__ = True

    id: Mapped[int] = mapped_column(INT, primary_key=True, autoincrement=True)
    role_code: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    permission_code: Mapped[str] = mapped_column(String(100), nullable=False, index=True)


# ============================================================
# Token 相关表
# ============================================================

class BaseTokenBlacklistTable(Base):
    """
    Token 黑名单表（已撤销的 Token 抽象类）

    用于存储被撤销的 Access Token，防止其继续使用
    """
    __abstract__ = True

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True, comment="主键ID")
    token_id: Mapped[str] = mapped_column(String(36), nullable=False, unique=True, index=True, comment="Token ID (JTI)")
    token_type: Mapped[str] = mapped_column(String(20), nullable=False, comment="Token类型")
    user_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True, comment="用户UUID")
    expires_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, comment="Token过期时间")
    reason: Mapped[str | None] = mapped_column(String(200), nullable=True, comment="撤销原因")


class BaseRefreshTokenTable(Base):
    """
    Refresh Token 抽象类

    用于存储长期有效的 Refresh Token，用于刷新 Access Token
    """
    __abstract__ = True

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True, comment="主键ID")
    token: Mapped[str] = mapped_column(String(500), unique=True, nullable=False, index=True, comment="Refresh Token字符串")
    user_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True, comment="用户UUID")
    user_email: Mapped[str] = mapped_column(String(100), nullable=False, comment="用户邮箱")
    roles: Mapped[str | None] = mapped_column(Text, nullable=True, comment="用户角色(JSON数组)")
    issued_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=lambda: datetime.now(UTC), comment="签发时间")
    expires_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, comment="过期时间")
    is_revoked: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, index=True, comment="是否已撤销")
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True, comment="撤销时间")
    revoke_reason: Mapped[str | None] = mapped_column(String(200), nullable=True, comment="撤销原因(如: 用户重新登录、主动登出、安全原因等)")
