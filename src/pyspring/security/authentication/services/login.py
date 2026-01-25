from typing import Optional, List

from fastapi import HTTPException, status
from pyspring.ioc.annotations import ConditionalOnMissingBean
from pyspring.log.instance import logger
from pyspring.security.authentication.contracts.constant import RevokeTokenReason
from pyspring.security.authentication.contracts.flow import ILoginService
from pyspring.security.authentication.contracts.login import ILoginProvider
from pyspring.security.authentication.contracts.response import IResponseBuilder
from pyspring.security.authentication.contracts.token import ITokenPayloadBuilder, ITokenService
from pyspring.security.authentication.contracts.user import IUserProvider
from pyspring.security.authentication.services.context_validator import SecurityContextManagerService


@ConditionalOnMissingBean(ILoginService)
class DefaultLoginService(ILoginService):
    """
    默认登录认证服务（编排者）
    
    负责协调各个组件完成用户登录、登出等流程。
    支持多个认证提供者，按顺序尝试直到找到支持的提供者。
    具体的业务逻辑（查库、验密、构造响应）委托给具体的 Provider 实现。
    """

    def __init__(
            self,
            user_provider: IUserProvider,
            login_providers: List[ILoginProvider],
            response_builder: IResponseBuilder,
            payload_builder: ITokenPayloadBuilder,
            context_manager: SecurityContextManagerService,
            token_manager: ITokenService
    ):
        """
        初始化登录服务
        
        Args:
            user_provider: 用户提供者
            login_providers: 登录提供者列表（支持多种登录方式）
            response_builder: 响应构建器
            payload_builder: Token Payload 构建器
            context_manager: 安全上下文管理器
            token_manager: Token管理服务（通过IOC注入）
        """
        self.user_provider = user_provider
        self.login_providers = login_providers
        self.response_builder = response_builder
        self.payload_builder = payload_builder
        self.context_manager = context_manager
        self.token_manager = token_manager

        logger.info(f"[Auth] DefaultLoginService 初始化完成，注册了 {len(login_providers)} 个登录提供者")

    async def login(self, request: object) -> object:
        """
        用户登录流程编排
        
        支持多个登录提供者，按顺序尝试直到找到支持的提供者
        """
        try:
            # 1. 查找支持的登录提供者并执行认证
            user = None
            for provider in self.login_providers:
                if provider.supports(request):
                    user = await provider.authenticate(request)
                    break

            # 如果没有找到支持的提供者
            if user is None:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"No LoginProvider found for request type: {type(request)}"
                )

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

            # 撤销用户的 Refresh Token
            await self.token_manager.revoke_user_refresh_tokens(
                None,  # session 后续直接传递，TokenManager 库自己处理，目前不需要
                user.id,
                reason=RevokeTokenReason.USER_LOGIN
            )

            # 3. 构建 Token Payload (委托给 PayloadBuilder)
            access_payload = await self.payload_builder.build_payload(user, evaluation)

            # Refresh Token Payload 通常比较简单，只包含 sub
            refresh_payload = {
                "sub": str(user.id),
            }
            if evaluation and evaluation.claims:
                refresh_payload.update(evaluation.claims)

            # 4. 生成 Token
            access_token = self.token_manager.create_access_token(data=access_payload)
            refresh_token = await self.token_manager.create_refresh_token(data=refresh_payload)

            logger.info(f"[Success]用户登录成功: {user.email}")

            # 5. 构造响应（委托给 ResponseBuilder)
            return self.response_builder.build_login_response(
                user=user,
                access_token=access_token,
                refresh_token=refresh_token,
                warning_msg=warning_msg
            )

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"[Error] 登录失败: {e}")
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
            logger.info(f"[Success]用户登出成功: {email}")

            # 3. 构造响应
            return self.response_builder.build_logout_response()

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"[Error] 登出失败: {e}")
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

            logger.info("[Success]Token 刷新成功")

            # 2. 构造响应
            return self.response_builder.build_token_response(
                access_token=new_access_token
            )
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"[Error] Token 刷新失败: {e}")
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

            # 2. 查找用户 (委托给UserProvider)
            user = await self.user_provider.get_user_by_id(user_id)

            if not user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="用户不存在",
                    headers={"WWW-Authenticate": "Bearer"},
                )

            # 3. 构造 UserInfo
            # 这里暂时直接返回 user 对象
            # 理想情况下：return self.response_builder.build_user_info(user)
            return user

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"[Error] 获取当前用户失败: {e}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="认证失败",
                headers={"WWW-Authenticate": "Bearer"},
            )
