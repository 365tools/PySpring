"""
认证配置管理器
用于加载和管理 security.yaml 配置文件
"""

import os
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml

from pyspring.core.abstracts.interfaces.ISingleton import ISingletonService
from pyspring.log.instance import logger
from pyspring.utils.config_finder import find_config_file


class SecurityConfigManager(ISingletonService):
    """认证与授权配置管理器（由 IoC 容器管理单例）"""

    _config: Optional[Dict[str, Any]] = None

    def __init__(self):
        """初始化配置管理器"""
        self._load_config()

    @staticmethod
    def _find_project_root() -> Path:
        """查找项目根目录"""
        current = Path(__file__).resolve()

        # 向上查找，直到找到包含 config 目录的父目录
        while current != current.parent:
            config_dir = current / "config"
            if config_dir.exists() and config_dir.is_dir():
                return current
            current = current.parent

        # 如果没找到，返回当前文件所在目录的三级父目录
        return Path(__file__).resolve().parent.parent.parent.parent

    def _load_config(self):
        """加载配置文件（优先级：当前工作目录 > 项目根目录）"""
        try:
            config_file = find_config_file('security.yaml')

            if not config_file:
                logger.debug("[SecurityConfigManager] 配置文件不存在")
                logger.debug("[SecurityConfigManager] 使用默认配置")
                self._config = self._get_default_config()
                return

            with open(config_file, 'r', encoding='utf-8') as f:
                self._config = yaml.safe_load(f)

            logger.debug(f"[SecurityConfigManager] 已加载配置文件: {config_file}")

            # 应用环境变量覆盖
            self._apply_env_overrides()

        except Exception as e:
            logger.debug(f"[SecurityConfigManager] 加载配置文件失败: {e}")
            logger.debug("[SecurityConfigManager] 使用默认配置")
            self._config = self._get_default_config()

    def _apply_env_overrides(self):
        """应用环境变量覆盖"""
        if self._config is None:
            return

        # JWT 密钥
        jwt_secret = os.getenv("JWT_SECRET_KEY")
        if jwt_secret:
            if "authentication" not in self._config:
                self._config["authentication"] = {}
            if "jwt" not in self._config["authentication"]:
                self._config["authentication"]["jwt"] = {}
            self._config["authentication"]["jwt"]["secret_key"] = jwt_secret
            logger.debug("[SecurityConfigManager] JWT_SECRET_KEY 已从环境变量加载")

        # JWT 算法
        jwt_algorithm = os.getenv("JWT_ALGORITHM")
        if jwt_algorithm:
            self._config["authentication"]["jwt"]["algorithm"] = jwt_algorithm

        # Token 过期时间
        access_token_expire = os.getenv("ACCESS_TOKEN_EXPIRE")
        if access_token_expire:
            self._config["authentication"]["jwt"]["access_token_expire"] = int(access_token_expire)

        refresh_token_expire = os.getenv("REFRESH_TOKEN_EXPIRE")
        if refresh_token_expire:
            self._config["authentication"]["jwt"]["refresh_token_expire"] = int(refresh_token_expire)

        # JWT 加密配置
        jwt_encryption_enabled = os.getenv("JWT_ENCRYPTION_ENABLED")
        if jwt_encryption_enabled:
            if "encryption" not in self._config["authentication"]["jwt"]:
                self._config["authentication"]["jwt"]["encryption"] = {}
            self._config["authentication"]["jwt"]["encryption"]["enabled"] = jwt_encryption_enabled.lower() == "true"

        jwt_encryption_key = os.getenv("JWT_ENCRYPTION_KEY")
        if jwt_encryption_key:
            if "encryption" not in self._config["authentication"]["jwt"]:
                self._config["authentication"]["jwt"]["encryption"] = {}
            self._config["authentication"]["jwt"]["encryption"]["encryption_key"] = jwt_encryption_key
            logger.debug("[SecurityConfigManager] JWT_ENCRYPTION_KEY 已从环境变量加载")

    def _get_default_config(self) -> Dict[str, Any]:
        """获取默认配置"""
        return {
            "authentication": {
                "enabled": True,
                "jwt": {
                    "secret_key": os.getenv("JWT_SECRET_KEY", "your-secret-key-change-in-production"),
                    "algorithm": "HS256",
                    "access_token_expire": 3600,
                    "refresh_token_expire": 2592000
                },
                "providers": [
                    {
                        "name": "jwt",
                        "type": "JWTAuthProvider",
                        "enabled": True,
                        "priority": 1,
                        "config": {
                            "token_sources": ["header", "cookie", "query"],
                            "token_prefix": "Bearer"
                        }
                    }
                ],
                "whitelist": {
                    "exact_paths": [
                        "/", "/health", "/favicon.ico",
                        "/docs", "/redoc", "/openapi.json",
                        "/api/auth/login", "/api/auth/register", "/api/auth/token/refresh"
                    ],
                    "prefix_paths": ["/static/", "/api/docs/", "/api/public/"],
                    "regex_patterns": ["^/api/v[0-9]+/public/.*"]
                }
            },
            "authorization": {
                "enabled": True,
                "role_mappings": {},
                "role_hierarchy": {}
            },
            "security": {
                "rate_limit": {
                    "enabled": False,
                    "default_limit": 60,
                    "path_limits": {}
                },
                "cors": {
                    "enabled": True,
                    "allow_origins": ["http://localhost:3000"],
                    "allow_credentials": True,
                    "allow_methods": ["GET", "POST", "PUT", "DELETE", "PATCH"],
                    "allow_headers": ["*"]
                }
            }
        }

    @property
    def config(self) -> Dict[str, Any]:
        """
        获取配置
        
        Returns:
            配置字典
        """
        return self._config

    def get(self, key: str, default: Any = None) -> Any:
        """
        使用点号分隔的键获取配置值
        例如: config.get("authentication.jwt.secret_key")
        """
        if self._config is None:
            return default

        keys = key.split('.')
        value = self._config

        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default

        return value

    def get_authentication_config(self) -> Dict[str, Any]:
        """获取认证配置"""
        return self._config.get("authentication", {}) if self._config else {}

    def get_authorization_config(self) -> Dict[str, Any]:
        """获取授权配置"""
        return self._config.get("authorization", {}) if self._config else {}

    def get_security_config(self) -> Dict[str, Any]:
        """获取安全配置"""
        return self._config.get("security", {}) if self._config else {}

    def get_jwt_config(self) -> Dict[str, Any]:
        """获取 JWT 配置"""
        auth_config = self.get_authentication_config()
        return auth_config.get("jwt", {})

    def get_providers_config(self) -> List[Dict[str, Any]]:
        """获取认证提供者配置"""
        auth_config = self.get_authentication_config()
        return auth_config.get("providers", [])

    def get_authentication_providers(self) -> List[Dict[str, Any]]:
        """获取认证提供者配置 (Alias for get_providers_config)"""
        return self.get_providers_config()

    def get_whitelist_config(self) -> Dict[str, Any]:
        """获取白名单配置"""
        auth_config = self.get_authentication_config()
        return auth_config.get("whitelist", {})

    def get_role_mappings(self) -> Dict[str, List[str]]:
        """获取角色映射"""
        auth_config = self.get_authorization_config()
        return auth_config.get("role_mappings", {})

    def get_role_hierarchy(self) -> Dict[str, Dict[str, List[str]]]:
        """获取角色继承关系"""
        auth_config = self.get_authorization_config()
        return auth_config.get("role_hierarchy", {})

    def is_authentication_enabled(self) -> bool:
        """认证是否启用"""
        return self.get("authentication.enabled", True)

    def is_authorization_enabled(self) -> bool:
        """授权是否启用"""
        return self.get("authorization.enabled", True)

    def is_rate_limit_enabled(self) -> bool:
        """限流是否启用"""
        return self.get("security.rate_limit.enabled", False)

    def is_cors_enabled(self) -> bool:
        """CORS 是否启用"""
        return self.get("security.cors.enabled", True)

    def reload(self):
        """重新加载配置"""
        self._config = None
        self._load_config()


# 导出单例实例
security_config = SecurityConfigManager()
