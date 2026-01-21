from typing import Any, Dict

from sqlalchemy import select

from pyspring.repositories.db.manager import DBManagerService
from pyspring.security.authentication.contracts.interface.token import ITokenPayloadBuilder
from pyspring.security.authentication.core.component import SecurityEntityConfiguration


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
                self.component.user_role_orm_model.role_id == self.component.role_orm_model.id
            ).where(self.component.user_role_orm_model.user_id == user.id)
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

        # 2. 构造基础 Payload
        payload = {
            "sub": str(user.id),
            "email": getattr(user, 'email', None),
            "user_id": getattr(user, 'user_id', None),
            "roles": role_codes,
            "permissions": permissions,
        }

        # 3. 合并来自安全上下文的动态 Claims
        if context_evaluation and hasattr(context_evaluation, 'claims'):
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
