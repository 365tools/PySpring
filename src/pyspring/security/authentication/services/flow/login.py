from typing import Optional

from fastapi import HTTPException, status

from pyspring.log.instance import logger
from pyspring.security.authentication.contracts.interface.flow import ILoginService
from pyspring.security.authentication.contracts.interface.login import ILoginProvider
from pyspring.security.authentication.contracts.interface.response import IResponseBuilder
from pyspring.security.authentication.contracts.interface.token import ITokenPayloadBuilder, ITokenService
from pyspring.security.authentication.contracts.interface.user import IUserProvider
from pyspring.security.authentication.services.context_validator import SecurityContextManagerService
from pyspring.security.authorization.contracts.schema.constant import RevokeTokenReason


class DefaultLoginService(ILoginService):
    """
    默认登录认证服务 (编排者)
    
    负责协调各个组件完成用户登录、登出等流程。
    具体的业务逻辑（查库、验密、构造响应）委托给具体的 Provider 实现。
    """

    def __init__(
            self,
            user_provider: IUserProvider,
            auth_provider: ILoginProvider,
            token_manager: ITokenService,
            response_builder: IResponseBuilder,
            payload_builder: ITokenPayloadBuilder,
            context_manager: SecurityContextManagerService
    ):
        """
        初始化登录服务
        
        Args:
            user_provider: 用户提供者 (策略)
            auth_provider: 认证提供者 (策略)
            token_manager: Token管理服务 (策略)
            response_builder: 响应构建器 (策略)
            payload_builder: Token Payload 构建器 (策略)
            context_manager: 安全上下文管理器
        """
        self.user_provider = user_provider
        self.auth_provider = auth_provider
        self.token_manager = token_manager
        self.response_builder = response_builder
        self.payload_builder = payload_builder
        self.context_manager = context_manager

        logger.info("🔧 DefaultLoginService 初始化完成 (Strategy Pattern)")

    async def login(self, request: object) -> object:
        """
        用户登录流程编排
        """
        try:
            # 1. 认证 (委托给 AuthProvider)
            # AuthProvider 内部负责校验凭据，返回合法的用户对象
            user = await self.auth_provider.authenticate(request)

            # ==================== 安全上下文验证 (Context Validation) ====================
            # 使用 SecurityContextManager 调用所有验证器 (Context Policies)
            context_data = {
                "user": user,
                "request_payload": request,
            }

            evaluation = await self.context_manager.evaluate(context_data)

            if not evaluation.is_valid:
                error_msg = "; ".join(evaluation.errors)
                logger.warning(f"Login blocked by security policy: {error_msg}")
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Security Policy Violation: {error_msg}"
                )

            # 获取警告信息
            warning_msg = "; ".join(evaluation.warnings) if evaluation.warnings else ""

            # 2. 撤销旧 Token
            # 注意：这里直接使用了 user.id，假设 user 对象有 id 属性
            await self.token_manager.revoke_user_refresh_tokens(
                None,  # session 不再直接传递，TokenManager 应该自己处理或不需要
                user.id,
                reason=RevokeTokenReason.USER_LOGIN
            )

            # 3. 构建 Token Payload (委托给 PayloadBuilder)
            access_payload = await self.payload_builder.build_payload(user, evaluation)

            # Refresh Token Payload 通常比较简单，只包含 sub
            refresh_payload = {
                "sub": str(user.id),
                # 也可以包含一些动态 claims，视需求而定
            }
            if evaluation and hasattr(evaluation, 'claims'):
                refresh_payload.update(evaluation.claims)

            # 4. 生成 Token
            access_token = self.token_manager.create_access_token(data=access_payload)
            refresh_token = await self.token_manager.create_refresh_token(data=refresh_payload)

            logger.info(f"✅ 用户登录成功: {getattr(user, 'email', 'unknown')}")

            # 5. 构造响应 (委托给 ResponseBuilder)
            return self.response_builder.build_login_response(
                user=user,
                access_token=access_token,
                refresh_token=refresh_token,
                warning_msg=warning_msg
            )

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"🚨 登录失败: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"登录失败: {str(e)}"
            )

    async def logout(self, token: str) -> object:
        """
        用户登出流程编排
        """
        try:
            # 1. 验证 Token
            payload = await self.token_manager.verify_token(token)
            if not payload:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Token 无效或已过期"
                )

            # 2. 撤销 Token
            await self.token_manager.revoke_token(token)

            email = payload.get("email", "unknown")
            logger.info(f"✅ 用户登出成功: {email}")

            # 3. 构造响应
            return self.response_builder.build_logout_response()

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"🚨 登出失败: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"登出失败: {str(e)}"
            )

    async def refresh_token(self, refresh_token: str) -> object:
        """
        刷新 Token 流程编排
        """
        try:
            # 1. 刷新 Token
            new_access_token = await self.token_manager.refresh_access_token(refresh_token)

            if not new_access_token:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Refresh token 无效或已过期"
                )

            logger.info("✅ Token 刷新成功")

            # 2. 构造响应
            return self.response_builder.build_token_response(
                access_token=new_access_token
            )
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"🚨 Token 刷新失败: {e}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="刷新失败"
            )

    async def get_current_user(self, token: str) -> Optional[object]:
        """
        获取当前用户流程编排
        """
        try:
            # 1. 验证 Token
            payload = await self.token_manager.verify_token(token)
            if not payload:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Token 无效或已过期",
                    headers={"WWW-Authenticate": "Bearer"},
                )

            user_id = int(str(payload.get("sub") or 0))

            # 2. 查找用户 (委托给 UserProvider)
            user = await self.user_provider.get_user_by_id(user_id)

            if not user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="用户不存在",
                    headers={"WWW-Authenticate": "Bearer"},
                )

            # 3. 构造 UserInfo
            # 这里我们暂时直接返回 user 对象，或者您可以扩展 IResponseBuilder 来处理这个
            # 理想情况下：return self.response_builder.build_user_info(user)
            return user

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"🚨 获取当前用户失败: {e}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="认证失败",
                headers={"WWW-Authenticate": "Bearer"},
            )
