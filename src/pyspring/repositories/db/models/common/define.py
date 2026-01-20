from datetime import datetime, UTC

from sqlalchemy import Column, String, Boolean, INT, TIMESTAMP
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
    user_id: Mapped[int] = mapped_column(INT, nullable=False)
    role_id: Mapped[int] = mapped_column(INT, nullable=False)


class BaseRolePermissionTable(Base):
    """
    角色权限关联表基类（抽象类）
    """
    __abstract__ = True

    id: Mapped[int] = mapped_column(INT, primary_key=True, autoincrement=True)
    role_code: Mapped[str] = mapped_column(String, nullable=False)
    permission_code: Mapped[str] = mapped_column(String, nullable=False)
