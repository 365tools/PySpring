"""
PySpring 配置管理器
支持三层配置架构：框架级配置、框架默认值、用户配置
"""
import os
from pathlib import Path
from typing import Dict, Any, Optional

import yaml
from loguru import logger


class ConfigManager:
    """
    配置管理器，负责加载和合并配置
    
    配置加载顺序（后面的覆盖前面的）：
    1. 框架默认配置 (src/pyspring/config/defaults/)
    2. 用户项目配置 (user_project/config/)
    3. 环境变量 (JWT_SECRET_KEY 等)
    4. 代码中显式指定的参数
    """

    # 框架配置目录
    _FRAMEWORK_CONFIG_DIR = Path(__file__).parent / "config"
    _FRAMEWORK_DEFAULTS_DIR = _FRAMEWORK_CONFIG_DIR / "defaults"

    # 缓存已加载的配置
    _config_cache: Dict[str, Dict[str, Any]] = {}

    @classmethod
    def load_config(
            cls,
            config_name: str,
            user_config_dir: Optional[str] = None,
            use_cache: bool = True
    ) -> Dict[str, Any]:
        """
        加载配置文件
        
        Args:
            config_name: 配置文件名（不含扩展名），如 'security', 'database', 'logging'
            user_config_dir: 用户项目配置目录，默认为 'config/'
            use_cache: 是否使用缓存
            
        Returns:
            合并后的配置字典
            
        Example:
            >>> config = ConfigManager.load_config('security')
            >>> jwt_expire = config['authentication']['jwt']['access_token_expire']
        """
        # 检查缓存
        cache_key = f"{config_name}:{user_config_dir}"
        if use_cache and cache_key in cls._config_cache:
            logger.debug(f"📦 从缓存加载配置: {config_name}")
            return cls._config_cache[cache_key].copy()

        # 1. 加载框架默认配置
        framework_defaults = cls._load_framework_defaults(config_name)

        # 2. 加载用户项目配置
        user_config = cls._load_user_config(config_name, user_config_dir)

        # 3. 深度合并配置（用户配置覆盖框架默认）
        merged_config = cls._deep_merge(framework_defaults, user_config)

        # 4. 应用环境变量覆盖
        final_config = cls._apply_env_overrides(merged_config, config_name)

        # 缓存配置
        if use_cache:
            cls._config_cache[cache_key] = final_config.copy()

        return final_config

    @classmethod
    def _load_framework_defaults(cls, config_name: str) -> Dict[str, Any]:
        """加载框架默认配置"""
        defaults_file = cls._FRAMEWORK_DEFAULTS_DIR / f"{config_name}.yaml"

        if not defaults_file.exists():
            logger.warning(f"⚠️  框架默认配置不存在: {defaults_file}")
            return {}

        try:
            with open(defaults_file, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f) or {}
            logger.debug(f"✅ 已加载框架默认配置: {config_name} <- {defaults_file}")
            return config
        except Exception as e:
            logger.error(f"❌ 加载框架默认配置失败: {defaults_file}, 错误: {e}")
            return {}

    @classmethod
    def _load_user_config(
            cls,
            config_name: str,
            user_config_dir: Optional[str] = None
    ) -> Dict[str, Any]:
        """加载用户项目配置"""
        if user_config_dir is None:
            user_config_dir = "config"

        # 支持相对路径和绝对路径
        user_config_path = Path(user_config_dir)
        if not user_config_path.is_absolute():
            # 相对于当前工作目录
            user_config_path = Path.cwd() / user_config_path

        user_config_file = user_config_path / f"{config_name}.yaml"

        if not user_config_file.exists():
            logger.debug(f"📝 用户配置不存在（使用框架默认值）: {user_config_file}")
            return {}

        try:
            with open(user_config_file, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f) or {}
            logger.debug(f"✅ 已加载用户配置: {config_name} <- {user_config_file}")
            return config
        except Exception as e:
            logger.warning(f"⚠️  加载用户配置失败，使用框架默认值: {user_config_file}, 错误: {e}")
            return {}

    @classmethod
    def _deep_merge(cls, base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
        """
        深度合并两个字典
        override 中的值会覆盖 base 中的值
        
        **重要**: None 值会被忽略，不会覆盖框架默认值
        这允许用户配置中使用 null 而不破坏框架默认配置
        """
        result = base.copy()

        for key, value in override.items():
            # 🔧 忽略 None 值，保留框架默认值
            # 这符合三层配置架构：用户配置的 null 不应覆盖框架默认值
            if value is None:
                continue
                
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                # 递归合并字典
                result[key] = cls._deep_merge(result[key], value)
            else:
                # 直接覆盖
                result[key] = value

        return result

    @classmethod
    def _apply_env_overrides(cls, config: Dict[str, Any], config_name: str) -> Dict[str, Any]:
        """
        应用环境变量覆盖
        
        环境变量命名规则：
        - security.yaml: JWT_SECRET_KEY, JWT_ENCRYPTION_KEY
        - repositories.yaml: POSTGRES_PASSWORD, MYSQL_PASSWORD, REDIS_PASSWORD
        """
        result = config.copy()

        if config_name == "security":
            # JWT 密钥
            if jwt_secret := os.getenv("JWT_SECRET_KEY"):
                cls._set_nested(result, ["authentication", "jwt", "secret_key"], jwt_secret)
                logger.debug("✅ 从环境变量加载 JWT_SECRET_KEY")

            # JWT 加密密钥
            if jwt_enc_key := os.getenv("JWT_ENCRYPTION_KEY"):
                cls._set_nested(result, ["authentication", "jwt", "encryption", "encryption_key"], jwt_enc_key)
                logger.debug("✅ 从环境变量加载 JWT_ENCRYPTION_KEY")

        elif config_name == "repositories":
            # PostgreSQL 密码
            if pg_password := os.getenv("POSTGRES_PASSWORD"):
                cls._set_nested(result, ["database", "postgresql", "password"], pg_password)
                logger.debug("✅ 从环境变量加载 POSTGRES_PASSWORD")

            # MySQL 密码
            if mysql_password := os.getenv("MYSQL_PASSWORD"):
                cls._set_nested(result, ["database", "mysql", "password"], mysql_password)
                logger.debug("✅ 从环境变量加载 MYSQL_PASSWORD")

            # Redis 密码
            if redis_password := os.getenv("REDIS_PASSWORD"):
                cls._set_nested(result, ["cache", "redis", "password"], redis_password)
                logger.debug("✅ 从环境变量加载 REDIS_PASSWORD")

        return result

    @classmethod
    def _set_nested(cls, config: Dict[str, Any], keys: list, value: Any) -> None:
        """设置嵌套字典的值"""
        current = config
        for key in keys[:-1]:
            if key not in current:
                current[key] = {}
            current = current[key]
        current[keys[-1]] = value

    @classmethod
    def clear_cache(cls) -> None:
        """清除配置缓存"""
        cls._config_cache.clear()
        logger.debug("🧹 已清除配置缓存")

    @classmethod
    def reload_config(cls, config_name: str, user_config_dir: Optional[str] = None) -> Dict[str, Any]:
        """重新加载配置（不使用缓存）"""
        return cls.load_config(config_name, user_config_dir, use_cache=False)


# 便捷函数
def load_security_config(user_config_dir: Optional[str] = None) -> Dict[str, Any]:
    """加载安全配置"""
    return ConfigManager.load_config("security", user_config_dir)


def load_repositories_config(user_config_dir: Optional[str] = None) -> Dict[str, Any]:
    """加载数据仓储配置（数据库+缓存）"""
    return ConfigManager.load_config("repositories", user_config_dir)


def load_logging_config(user_config_dir: Optional[str] = None) -> Dict[str, Any]:
    """加载日志配置"""
    return ConfigManager.load_config("logging", user_config_dir)
