from abc import ABC, abstractmethod
from typing import Any, Optional, Dict

from pyspring.core.abstracts.interfaces.ISingleton import ISingletonService


class IUserProvider(ISingletonService, ABC):
    """
    用户提供者接口
    负责从数据源（数据库、LDAP、API等）查找用户
    """

    @abstractmethod
    async def get_user_by_id(self, user_id: Any) -> Optional[Any]:
        """根据 ID 获取用户"""
        pass

    @abstractmethod
    async def get_user_by_identity(self, identity: str) -> Optional[Any]:
        """根据标识（用户名/邮箱/手机号）获取用户"""
        pass


class IAuthenticationProvider(ISingletonService, ABC):
    """
    认证提供者接口
    负责验证用户凭据（密码、验证码等）
    """

    @abstractmethod
    def supports(self, request: Any) -> bool:
        """
        Check if this provider supports the given request type.
        """
        pass

    @abstractmethod
    async def authenticate(self, request: Any) -> Any:
        """
        Execute authentication logic.
        
        Args:
            request: The login request object. The type depends on the specific implementation.
                     For example, DefaultPasswordAuthenticationProvider expects a LoginRequest (pydantic model).
                     You can pass dict, custom objects, etc., as long as your Provider handles it.
            
        Returns:
            Any: The authenticated User object (usually a DB model or Pydantic model).

        Raises:
            HTTPException: Raised when authentication fails.
        """
        pass


class IResponseBuilder(ISingletonService, ABC):
    """
    响应构建器接口
    负责构造 API 响应
    """

    @abstractmethod
    def build_login_response(self, user: Any, access_token: str, refresh_token: str, **kwargs) -> Any:
        """构造登录成功响应"""
        pass

    @abstractmethod
    def build_logout_response(self, **kwargs) -> Any:
        """构造登出响应"""
        pass

    @abstractmethod
    def build_token_response(self, access_token: str, **kwargs) -> Any:
        """构造刷新 Token 响应"""
        pass


class ITokenPayloadBuilder(ISingletonService, ABC):
    """
    Token Payload 构建器接口
    负责定义 JWT Token 中包含哪些信息
    """

    @abstractmethod
    async def build_payload(self, user: Any, context_evaluation: Any = None) -> Dict[str, Any]:
        """
        构造 Token 的 Payload
        
        Args:
            user: 用户对象
            context_evaluation: 安全上下文评估结果 (可选)
            
        Returns:
            Dict: Token Payload
        """
        pass


class ITokenService(ISingletonService, ABC):
    """
    Token 服务接口
    负责 Token 的生命周期管理
    """

    @abstractmethod
    def create_access_token(self, data: Dict[str, Any], expires_delta: Optional[Any] = None) -> str:
        """创建 Access Token"""
        pass

    @abstractmethod
    def create_refresh_token(self, data: Dict[str, Any], expires_delta: Optional[Any] = None) -> str:
        """创建 Refresh Token"""
        pass

    @abstractmethod
    async def verify_token(self, token: str) -> Optional[Dict[str, Any]]:
        """验证 Token"""
        pass

    @abstractmethod
    async def revoke_token(self, token: str, reason: str = "") -> bool:
        """撤销 Token"""
        pass

    @abstractmethod
    async def revoke_user_refresh_tokens(self, session: Any, user_id: Any, reason: str = "") -> None:
        """撤销用户的所有刷新令牌"""
        pass

    @abstractmethod
    def refresh_access_token(self, refresh_token: str) -> str:
        """刷新 Access Token (使用 Refresh Token)"""
        pass


class ILoginService(ISingletonService, ABC):
    """
    登录服务接口
    负责登录流程编排
    """

    @abstractmethod
    async def login(self, request: Any) -> Any:
        """处理登录"""
        pass

    @abstractmethod
    async def logout(self, token: str) -> Any:
        """处理登出"""
        pass

    @abstractmethod
    async def refresh_token(self, refresh_token: str) -> Any:
        """刷新 Token"""
        pass


class IRegisterService(ISingletonService, ABC):
    """
    注册服务接口
    负责用户注册流程
    """

    @abstractmethod
    async def register(self, request: Any) -> Any:
        """注册新用户"""
        pass


class IUserManagerService(ISingletonService, ABC):
    """
    用户管理服务接口
    负责用户信息的查询、更新等
    """

    @abstractmethod
    async def get_user_by_id(self, user_id: Any) -> Optional[Any]:
        """根据ID获取用户"""
        pass

    @abstractmethod
    async def get_user_by_email(self, email: str) -> Optional[Any]:
        """根据邮箱获取用户"""
        pass

    @abstractmethod
    async def get_current_user(self, token: Optional[str] = None) -> Optional[Any]:
        """获取当前用户"""
        pass

    @abstractmethod
    async def list_users(self, skip: int = 0, limit: int = 100) -> Any:
        """获取用户列表"""
        pass

    @abstractmethod
    async def update_user_info(self, user_id: Any, user_info: Any) -> Any:
        """完整更新用户信息"""
        pass

    @abstractmethod
    async def update_user_field(self, user_id: Any, field_name: str, field_value: Any) -> Any:
        """更新单个字段"""
        pass
