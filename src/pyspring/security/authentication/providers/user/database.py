from typing import Any, Optional

from pyspring.ioc.annotations import ConditionalOnMissingBean
from pyspring.repositories.db.manager import DBManagerService
from pyspring.security.authentication.config.entity import SecurityEntityConfiguration
from pyspring.security.authentication.contracts.user import IUserProvider
from sqlalchemy import select


@ConditionalOnMissingBean(IUserProvider)
class DefaultUserProvider(IUserProvider):
    """
    Default User Provider: Query database using SQLAlchemy
    """

    def __init__(self, db: DBManagerService, component: SecurityEntityConfiguration):
        self.db = db
        self.component = component

    async def get_user_by_id(self, user_id: Any) -> Optional[Any]:
        async with await self.db.session() as session:
            stmt = select(self.component.user_orm_model).where(self.component.user_orm_model.id == user_id)
            result = await session.execute(stmt)
            return result.scalar_one_or_none()

    async def get_user_by_identity(self, identity: str) -> Optional[Any]:
        async with await self.db.session() as session:
            # 尝试匹配 user_id 或 email
            # 这里为了简单，假设 identity 可能是 user_id 也可能是 email
            # 实际逻辑可以更复杂，或者由具体的 SQL 决定
            stmt = select(self.component.user_orm_model).where(
                (self.component.user_orm_model.user_id == identity) |
                (self.component.user_orm_model.email == identity)
            )
            result = await session.execute(stmt)
            return result.scalar_one_or_none()
