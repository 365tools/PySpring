"""
认证提供者基类
所有认证实现都需要继承此基类
"""
import re
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional, Dict, Any, List

from fastapi import Request


@dataclass
class AuthenticationResult:
    """认证结果"""
    success: bool
    user_id: Optional[str] = None
    username: Optional[str] = None
    roles: Optional[List[str]] = None
    extra_data: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    provider_name: Optional[str] = None


class BaseAuthenticationProvider(ABC):
    """认证提供者基类"""

    def __init__(self, name: str, config: Dict[str, Any]):
        """
        初始化认证提供者
        
        Args:
            name: 提供者名称
            config: 提供者配置
        """
        self.name = name
        self.config = config
        self.enabled = config.get("enabled", True)
        self.priority = config.get("priority", 999)
        self._provider_config = config.get("config", {})

    @abstractmethod
    async def authenticate(self, request: Request) -> AuthenticationResult:
        """
        执行认证逻辑
        
        Args:
            request: FastAPI Request 对象
            
        Returns:
            AuthenticationResult: 认证结果
        """
        pass

    @abstractmethod
    async def extract_credentials(self, request: Request) -> Optional[Any]:
        """
        从请求中提取凭证
        
        Args:
            request: FastAPI Request 对象
            
        Returns:
            Optional[Any]: 凭证数据（如 Token、API Key 等）
        """
        pass

    @abstractmethod
    async def validate_credentials(self, credentials: Any) -> AuthenticationResult:
        """
        验证凭证
        
        Args:
            credentials: 凭证数据
            
        Returns:
            AuthenticationResult: 验证结果
        """
        pass

    def is_enabled(self) -> bool:
        """检查提供者是否启用"""
        return self.enabled

    def get_priority(self) -> int:
        """获取优先级（数字越小优先级越高）"""
        return self.priority

    def get_name(self) -> str:
        """获取提供者名称"""
        return self.name

    def get_config(self, key: str, default: Any = None) -> Any:
        """获取配置值"""
        keys = key.split('.')
        value = self._provider_config

        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default

        return value


class PathMatcher:
    """路径匹配工具"""

    @staticmethod
    def is_exact_match(path: str, exact_paths: List[str]) -> bool:
        """
        精确匹配
        
        Args:
            path: 请求路径
            exact_paths: 精确路径列表
            
        Returns:
            bool: 是否匹配
        """
        return path in exact_paths

    @staticmethod
    def is_prefix_match(path: str, prefix_paths: List[str]) -> bool:
        """
        前缀匹配
        
        Args:
            path: 请求路径
            prefix_paths: 前缀路径列表
            
        Returns:
            bool: 是否匹配
        """
        return any(path.startswith(prefix) for prefix in prefix_paths)

    @staticmethod
    def is_regex_match(path: str, regex_patterns: List[str]) -> bool:
        """
        正则表达式匹配
        
        Args:
            path: 请求路径
            regex_patterns: 正则表达式列表
            
        Returns:
            bool: 是否匹配
        """
        for pattern in regex_patterns:
            try:
                if re.match(pattern, path):
                    return True
            except re.error:
                # 忽略无效的正则表达式
                continue
        return False

    @staticmethod
    def is_wildcard_match(path: str, wildcard_paths: List[str]) -> bool:
        """
        通配符匹配（* 匹配任意字符）
        
        Args:
            path: 请求路径
            wildcard_paths: 通配符路径列表
            
        Returns:
            bool: 是否匹配
        """
        for pattern in wildcard_paths:
            # 将通配符转换为正则表达式
            regex_pattern = "^" + pattern.replace("*", ".*") + "$"
            try:
                if re.match(regex_pattern, path):
                    return True
            except re.error:
                continue
        return False

    @classmethod
    def is_match(cls, path: str, whitelist: Dict[str, List[str]]) -> bool:
        """
        检查路径是否匹配白名单
        
        Args:
            path: 请求路径
            whitelist: 白名单配置
            
        Returns:
            bool: 是否匹配
        """
        # 精确匹配
        exact_paths = whitelist.get("exact_paths", [])
        if cls.is_exact_match(path, exact_paths):
            return True

        # 前缀匹配
        prefix_paths = whitelist.get("prefix_paths", [])
        if cls.is_prefix_match(path, prefix_paths):
            return True

        # 正则表达式匹配
        regex_patterns = whitelist.get("regex_patterns", [])
        if cls.is_regex_match(path, regex_patterns):
            return True

        # 通配符匹配（如果配置了）
        wildcard_paths = whitelist.get("wildcard_paths", [])
        if cls.is_wildcard_match(path, wildcard_paths):
            return True

        return False


class BaseAuthProvider(BaseAuthenticationProvider):
    """
    基础认证提供者（提供默认实现）
    
    子类可以选择性覆盖需要的方法
    """

    async def authenticate(self, request: Request) -> AuthenticationResult:
        """
        默认的认证流程：
        1. 提取凭证
        2. 验证凭证
        """
        try:
            # 提取凭证
            credentials = await self.extract_credentials(request)
            if credentials is None:
                return AuthenticationResult(
                    success=False,
                    error_message=f"{self.name}: 未找到认证凭证",
                    provider_name=self.name
                )

            # 验证凭证
            result = await self.validate_credentials(credentials)
            result.provider_name = self.name
            return result

        except Exception as e:
            return AuthenticationResult(
                success=False,
                error_message=f"{self.name}: 认证失败 - {str(e)}",
                provider_name=self.name
            )

    async def extract_credentials(self, request: Request) -> Optional[Any]:
        """默认凭证提取（子类应覆盖此方法）"""
        return None

    async def validate_credentials(self, credentials: Any) -> AuthenticationResult:
        """默认凭证验证（子类应覆盖此方法）"""
        return AuthenticationResult(
            success=False,
            error_message=f"{self.name}: 未实现凭证验证",
            provider_name=self.name
        )
