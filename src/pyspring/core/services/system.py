"""
SystemService - 系统配置服务

提供统一的配置访问接口。

使用方式（推荐IoC注入）:
    @Component()
    class MyService:
        def __init__(self, config_service: SystemService):
            port = config_service.settings.app.server.port
            db_type = config_service.settings.database.type
"""
from typing import Any, Optional

from pyspring.ioc.annotations.component import Component
from pyspring.ioc.annotations.scope import Singleton
from pyspring.ioc.interfaces.core import IManaged
from pyspring.log.instance import logger
from ..configuration.loader import ConfigLoader
from ..configuration.models import AppSettings


@Component()
@Singleton
class SystemService(IManaged):
    """
    系统配置服务
    
    提供统一的配置访问接口：
    - 通过 settings 属性访问完整配置
    - 通过 get_yaml_config() 读取额外的 YAML 文件
    """

    def __init__(self, settings: AppSettings):
        """
        初始化系统配置服务
        
        Args:
            settings: 应用配置实例（通过IoC注入）
        """
        super().__init__()
        self._settings = settings
        self._config_loader: Optional[ConfigLoader] = None

    @property
    def settings(self) -> AppSettings:
        """
        获取应用配置
        
        Returns:
            AppSettings: 完整的应用配置对象
        """
        return self._settings

    def get_yaml_config(self, filename: str, key: str = None, default: Any = None) -> Any:
        """
        从YAML配置文件中读取配置
        
        Args:
            filename: 配置文件名（如 "application.yaml"）
            key: 配置键（点号分隔），如 "server.host"。如果为None，返回整个文件
            default: 默认值
            
        Returns:
            Any: 配置值
            
        Examples:
            >>> service.get_yaml_config("application.yaml", "server.host", "0.0.0.0")
            >>> service.get_yaml_config("custom.yaml")  # 返回整个文件
        """
        try:
            # 懒加载 ConfigLoader
            if self._config_loader is None:
                self._config_loader = ConfigLoader()

            # 加载 YAML 文件
            config_path = self._config_loader.project_root / "config" / filename
            config = self._config_loader.load_yaml(config_path)

            # 如果没有指定 key，返回整个配置
            if key is None:
                return config if config else default

            # 按点号分割键路径
            keys = key.split(".")
            value = config

            # 逐级获取值
            for k in keys:
                if isinstance(value, dict) and k in value:
                    value = value[k]
                else:
                    return default

            return value if value is not None else default

        except Exception as e:
            logger.debug(f"读取YAML配置失败 {filename}:{key} - {e}")
            return default

    def validate(self) -> bool:
        """
        验证配置完整性
        
        Returns:
            bool: 配置是否有效
        """
        try:
            # Pydantic 会在加载时自动验证
            # 这里检查关键配置
            assert self._settings.app.server.host
            assert self._settings.app.server.port > 0
            assert self._settings.authentication.jwt.secret_key

            logger.info("✅ 配置验证通过")
            return True

        except Exception as e:
            logger.error(f"❌ 配置验证失败: {e}")
            return False

    def __repr__(self) -> str:
        return f"<SystemService>"


__all__ = ["SystemService"]
