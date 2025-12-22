from datetime import datetime, UTC

from sqlalchemy import Column, String, Boolean, INT, TIMESTAMP
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """SQLAlchemy 基类"""

    version = Column(INT, nullable=True)
    active = Column(Boolean, nullable=False, default=True)
    deleted = Column(Boolean, nullable=False, default=False)
    creator = Column(String, nullable=False, default="system")
    created_time = Column(TIMESTAMP, nullable=False, default=lambda: datetime.now(UTC))
    modifier = Column(String, nullable=False, default="system")
    modified_time = Column(TIMESTAMP, nullable=False, default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC))
