from datetime import datetime, UTC

from sqlalchemy import Column, Integer, String, DateTime, Text

from pyspring.repositories.db.models.common.define import Base


class TokenBlacklistTable(Base):
    """Token 黑名单表(已撤销的token)"""
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
    Refresh Token表
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
        return f"<RefreshToken(id={self.id}, user_id={self.user_id}, active={self.active})>"
