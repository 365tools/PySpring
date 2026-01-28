from typing import Any, Dict

from sqlalchemy import select

from pyspring.repositories.db.manager import DBManagerService
from pyspring.security.authentication.config.entity import SecurityEntityConfiguration
from pyspring.security.authentication.contracts.token import ITokenPayloadBuilder


class DefaultTokenPayloadBuilder(ITokenPayloadBuilder):
    """
    默认的 Token Payload 构建器
    """

    def __init__(self, db: DBManagerService, component: SecurityEntityConfiguration):
        self.db = db
        self.component = component

    async def build_payload(self, user: Any, context_evaluation: Any = None) -> Dict[str, Any]:
        # 1. 查询角色和权限 (这部分逻辑从 LoginService 移过来了)
        async with await self.db.session() as session:
            stmt = select(self.component.role_orm_model).join(
                self.component.user_role_orm_model,
                self.component.user_role_orm_model.role_code == self.component.role_orm_model.code
            ).where(self.component.user_role_orm_model.user_id == user.user_id)
            result = await session.execute(stmt)
            roles = result.scalars().all()
            role_codes = [role.code for role in roles]

            permissions = []
            if role_codes:
                stmt_perms = select(self.component.permission_orm_model.code).join(
                    self.component.role_permission_orm_model,
                    self.component.role_permission_orm_model.permission_code == self.component.permission_orm_model.code
                ).where(self.component.role_permission_orm_model.role_code.in_(role_codes))
                result_perms = await session.execute(stmt_perms)
                permissions = list(set(result_perms.scalars().all()))

        # 2. 构造基础 Payload（符合 JWT RFC 7519 标准）
        # sub: 用户唯一标识符（使用 user_id UUID，不可变）
        # 避免使用数据库自增 ID（可枚举、不安全）或 email（可变）
        payload = {
            "sub": user.user_id,  # Subject: 用户唯一标识符（UUID，不可变）
            "roles": role_codes,
            "permissions": permissions,
        }

        # 动态添加配置中定义的所有 identifier_fields 到 payload
        # 这些字段可以用于登录和用户识别
        for field_name in self.component.identifier_fields:
            if hasattr(user, field_name):
                field_value = getattr(user, field_name)
                if field_value is not None:  # 只添加非空值
                    payload[field_name] = field_value

        # 3. 合并来自安全上下文的动态 Claims
        if context_evaluation and context_evaluation.claims:
            claims_to_merge = context_evaluation.claims.copy()

            # 特殊处理 roles 和 permissions 的合并
            if 'roles' in claims_to_merge:
                extra_roles = claims_to_merge.pop('roles')
                if isinstance(extra_roles, list):
                    payload['roles'] = list(set((payload.get('roles') or []) + extra_roles))

            if 'permissions' in claims_to_merge:
                extra_perms = claims_to_merge.pop('permissions')
                if isinstance(extra_perms, list):
                    payload['permissions'] = list(set((payload.get('permissions') or []) + extra_perms))

            payload.update(claims_to_merge)

        return payload
