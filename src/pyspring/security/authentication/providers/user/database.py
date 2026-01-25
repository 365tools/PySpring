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
        """\u6839\u636e user_id (UUID) \u83b7\u53d6\u7528\u6237"""
        async with await self.db.session() as session:
            stmt = select(self.component.user_orm_model).where(self.component.user_orm_model.user_id == str(user_id))
            result = await session.execute(stmt)
            return result.scalar_one_or_none()

    async def get_user_by_identity(self, identity: str) -> Optional[Any]:
        """
        根据身份标识查找用户
        
        支持根据配置的字段列表进行匹配（从 SecurityEntityConfiguration.identifier_fields）
        
        配置示例（config/security.yaml）：
        authentication:
          identifier_fields:
            - "user_id"
            - "username"
            - "email"
            - "phone"
        
        框架会：
        1. 从配置读取字段列表
        2. 动态检查用户模型是否有这些字段
        3. 构建 OR 查询条件
        4. 返回匹配的用户
        """
        async with await self.db.session() as session:
            # 从配置获取需要匹配的字段列表
            identifier_fields = self.component.identifier_fields

            # 构建查询条件
            conditions = []
            for field_name in identifier_fields:
                # 动态检查用户模型是否有该字段
                if hasattr(self.component.user_orm_model, field_name):
                    field = getattr(self.component.user_orm_model, field_name)
                    conditions.append(field == identity)

            # 如果没有可用的字段，抛出异常
            if not conditions:
                raise ValueError(
                    f"No valid identifier fields found in user model. "
                    f"Configured fields: {identifier_fields}"
                )

            # 使用 OR 条件查询
            from sqlalchemy import or_
            stmt = select(self.component.user_orm_model).where(or_(*conditions))
            result = await session.execute(stmt)
            return result.scalar_one_or_none()
