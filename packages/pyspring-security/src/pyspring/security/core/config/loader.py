"""
认证配置管理器
用于加载和管理 security.yaml 配置文件
"""

from typing import Any

from pyspring.core.config_manager import ConfigManager
from pyspring.core.ioc.annotations.scope import Singleton
from pyspring.core.ioc.interfaces.core import IManaged
from pyspring.core.log.instance import logger


@Singleton
class SecurityConfigManager(IManaged):
    """
    认证与授权配置管理器（由IOC容器管理单例）
    
    使用框架 ConfigManager 实现三层配置架构：
    1. 框架默认配置 (src/pyspring/config/defaults/security.yaml)
    2. 用户项目配置 (project/config/security.yaml)  
    3. 环境变量覆盖 (JWT_SECRET_KEY 等)
    """

    _config: (dict[str, Any]) | None = None

    def __init__(self):
        """初始化配置管理器"""
        self._load_config()

    def _load_config(self):
        """
        加载配置文件（使用框架 ConfigManager 实现三层架构）
        
        配置优先级（后面的覆盖前面的）：
        1. 框架默认配置
        2. 用户项目配置
        3. 环境变量
        """
        try:
            # 使用框架 ConfigManager 加载配置（自动处理三层合并）
            self._config = ConfigManager.load_config('security')
            logger.debug("[SecurityConfigManager] 已加载安全配置（三层架构：框架默认 + 用户配置 + 环境变量）")
        except Exception as e:
            logger.warning(f"[SecurityConfigManager] 加载配置异常，使用极简后备配置: {e}")
            self._config = self._get_fallback_config()

    def _get_fallback_config(self) -> dict[str, Any]:
        """
        获取极简后备配置（仅在 ConfigManager 加载失败时使用）
        
        这是最后的防御措施，正常情况下应该使用 ConfigManager 加载的三层配置
        完整配置请参考 src/pyspring/config/defaults/security.yaml
        """
        return {
            "authentication": {
                "enabled": True,
                "jwt": {
                    "secret_key": "pyspring-dev-secret-key-CHANGE-IN-PRODUCTION-32bytes-minimum",
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
                        "/", "/health", "/docs", "/redoc", "/openapi.json",
                        "/api/auth/login", "/api/auth/register", "/api/auth/token/refresh"
                    ]
                }
            },
            "authorization": {
                "enabled": True
            }
        }

    @property
    def config(self) -> dict[str, Any] | None:
        """
        获取配置
        
        Returns:
            配置字典（未初始化时为 None）
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

    def get_authentication_config(self) -> dict[str, Any]:
        """获取认证配置"""
        return self._config.get("authentication", {}) if self._config else {}

    def get_authorization_config(self) -> dict[str, Any]:
        """获取授权配置"""
        return self._config.get("authorization", {}) if self._config else {}

    def get_security_config(self) -> dict[str, Any]:
        """获取安全配置"""
        return self._config.get("security", {}) if self._config else {}

    def get_jwt_config(self) -> dict[str, Any]:
        """获取 JWT 配置"""
        auth_config = self.get_authentication_config()
        return auth_config.get("jwt", {})

    def get_providers_config(self) -> list[dict[str, Any]]:
        """获取认证提供者配置"""
        auth_config = self.get_authentication_config()
        return auth_config.get("providers", [])

    def get_authentication_providers(self) -> list[dict[str, Any]]:
        """获取认证提供者配置 (Alias for get_providers_config)"""
        return self.get_providers_config()

    def get_whitelist_config(self) -> list[str]:
        """获取白名单路径列表"""
        auth_config = self.get_authentication_config()
        whitelist = auth_config.get("whitelist", [])
        return list(whitelist) if isinstance(whitelist, list) else []

    def get_role_mappings(self) -> dict[str, list[str]]:
        """获取角色映射"""
        auth_config = self.get_authorization_config()
        return auth_config.get("role_mappings", {})

    def get_role_hierarchy(self) -> dict[str, dict[str, list[str]]]:
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
