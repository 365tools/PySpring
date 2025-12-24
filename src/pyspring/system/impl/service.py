"""
SystemService - 基于新配置系统的实现

直接使用新的配置系统(ConfigManager).

使用方式:
    from pyspring.system.impl.service import SystemService
    
    service = SystemService()
    # 直接访问配置
    port = service.settings.app.server.port
    
    # 或使用兼容方法
    server_config = service.get("server")
"""
import inspect
from pyspring.log.loguru.ins import logger
from pyspring.system.config.models import settings, AppSettings
from pyspring.system.interfaces.service import ISystemService
from typing import Any, Optional, Dict, Callable, List


class SystemService(ISystemService):
    """
    System管理服务
    基于新配置系统(ConfigManager), 提供统一的配置访问接口
    """

    # ✅ 类级别跟踪事件监听器创建的任务
    _event_tasks = set()

    def __init__(self):
        super().__init__()
        # 使用新的配置系统(单例)
        self._settings: AppSettings = settings
        # 缓存配置对象, 避免重复创建
        self._config_cache: Dict[str, Any] = {}
        # 订阅者(监听系统配置变化)
        self._listeners: List[Callable[[str, Dict[str, Any]], Any]] = []
        # 配置加载器（用于读取额外的 YAML 文件）
        self._config_loader = None
        self._yaml_configs: Dict[str, Any] = {}
        # logger.debug("🔧 SystemService initialized with new config system")

    def _load_yaml_config(self, filename: str) -> Dict[str, Any]:
        """
        加载指定的 YAML 配置文件
        
        Args:
            filename: 配置文件名（如 "application.yaml"）
            
        Returns:
            Dict[str, Any]: 配置字典
        """
        if filename not in self._yaml_configs:
            if self._config_loader is None:
                from pyspring.system.config.loader import ConfigLoader
                self._config_loader = ConfigLoader()

            config_path = self._config_loader.project_root / "config" / filename
            self._yaml_configs[filename] = self._config_loader.load_yaml(config_path)

        return self._yaml_configs[filename]

    def get_config(self, key: str, default: Any = None, config_file: str = "application.yaml") -> Any:
        """
        从配置文件中获取配置值（支持点号路径）
        
        Args:
            key: 配置键（点号分隔），如 "server.host", "server.port"
            default: 默认值
            config_file: 配置文件名，默认 "application.yaml"
            
        Returns:
            Any: 配置值
            
        Examples:
            >>> service = SystemService()
            >>> host = service.get_config("server.host", "0.0.0.0")
            >>> port = service.get_config("server.port", 8000)
        """
        try:
            # 加载配置文件
            config = self._load_yaml_config(config_file)

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
            logger.debug(f"获取配置失败 {key}: {e}")
            return default

    @property
    def settings(self) -> AppSettings:
        """直接访问新配置系统"""
        return self._settings

    def add_listener(self, listener: Callable[[str, Dict[str, Any]], Any]) -> None:
        """
        添加配置变化监听器
        """
        if listener not in self._listeners:
            self._listeners.append(listener)

    def remove_listener(self, listener: Callable[[str, Dict[str, Any]], Any]) -> None:
        """移除配置变化监听器"""
        try:
            self._listeners.remove(listener)
        except ValueError:
            pass

    def _notify(self, event: str, payload: Dict[str, Any]) -> None:
        """
        通知所有监听者. 异步监听者使用create_task
        调度, 不阻塞当前流程.
        """
        for listener in list(self._listeners):
            try:
                if inspect.iscoroutinefunction(listener):
                    try:
                        import asyncio
                        loop = asyncio.get_event_loop()
                        if loop.is_running():
                            # ✅ 跟踪事件任务
                            task = loop.create_task(listener(event, payload))
                            SystemService._event_tasks.add(task)
                            task.add_done_callback(SystemService._event_tasks.discard)
                        else:
                            asyncio.run(listener(event, payload))
                    except Exception as e:
                        logger.error(f"🚨 Async listener error: {e}")
                else:
                    listener(event, payload)
            except Exception as e:
                logger.error(f"🚨 Listener error: {e}")

    def get(self, key: str = "all") -> Optional[Any]:
        """
        获取系统配置（推荐直接使用 service.settings 访问）
        
        Args:
            key: 配置类别
            - 'server': 返回 ServerConfig
            - 'database': 返回 DatabaseConfig
            - 'redis': 返回 RedisConfig
            - 'logging': 返回 LoggingConfig
            - 'authentication': 返回 AuthenticationConfig
            - 'all': 返回完整 AppSettings

        Returns:
            配置对象
        """
        # 如果已经缓存, 直接返回
        if key in self._config_cache:
            return self._config_cache[key]

        try:
            if key == "server":
                config = self._settings.app.server
            elif key == "database":
                config = self._settings.database
            elif key == "redis":
                config = self._settings.redis
            elif key == "logging":
                config = self._settings.logging
            elif key == "authentication":
                config = self._settings.authentication
            else:  # "all"
                config = self._settings

            # 缓存配置
            self._config_cache[key] = config
            return config

        except Exception as e:
            logger.error(f"🚨 Failed to get config for key '{key}': {e}")
            return None

    def set(self, key: str, value: Any) -> bool:
        """
        设置配置值(运行时动态配置)
        
        注意: 新配置系统主要通过配置文件和环境变量管理,
        动态设置可能不会持久化
        
        Args:
            key: 配置键(使用点号分隔的路径, 如'app.server.port')
            value: 配置值

        Returns:
            bool: 是否设置成功
        """
        try:
            # 清除缓存
            self._config_cache.clear()

            # 解析键路径
            parts = key.split('.')
            target = self._settings

            # 导航到目标对象
            for part in parts[:-1]:
                target = getattr(target, part)

            # 设置值
            setattr(target, parts[-1], value)

            # 通知监听者
            self._notify("config_changed", {"key": key, "value": value})

            logger.info(f"✅ Config updated: {key} = {value}")
            return True

        except Exception as e:
            logger.error(f"🚨 Failed to set config {key}: {e}")
            return False

    def reload(self) -> bool:
        """
        重新加载配置
        
        注意: 新配置系统在启动时加载, 运行时重载需要重启应用
        此方法主要用于清除缓存
        
        Returns:
            bool: 是否重载成功
        """
        try:
            # 清除配置缓存
            self._config_cache.clear()
            logger.info("✅ Config cache cleared")

            # 通知监听者
            self._notify("config_reloaded", {})
            
            return True
        except Exception as e:
            logger.error(f"🚨 Failed to reload config: {e}")
            return False

    def validate(self) -> bool:
        """
        验证配置完整性
        
        Returns:
            bool: 配置是否有效
        """
        try:
            # Pydantic 会在加载时自动验证
            # 这里主要检查关键配置是否存在
            assert self._settings.app.server.host
            assert self._settings.app.server.port > 0
            assert self._settings.authentication.jwt.secret_key

            logger.info("✅ Config validation passed")
            return True

        except Exception as e:
            logger.error(f"🚨 Config validation failed: {e}")
            return False

    def __repr__(self) -> str:
        return f"<SystemService (using ConfigManager)>"

    @classmethod
    async def cancel_event_tasks(cls):
        """
        ✅ 取消所有事件任务，用于程序退出时清理
        """
        import asyncio
        if cls._event_tasks:
            logger.debug(f"🔄 正在取消 {len(cls._event_tasks)} 个事件任务...")
            for task in cls._event_tasks:
                if not task.done():
                    task.cancel()
            # 等待所有任务取消完成（最多等待2秒）
            try:
                await asyncio.wait_for(
                    asyncio.gather(*cls._event_tasks, return_exceptions=True),
                    timeout=2.0
                )
            except asyncio.TimeoutError:
                logger.warning("⚠️  部分事件任务取消超时")
            cls._event_tasks.clear()
            logger.debug("✅ 事件任务已清理")



# 单例实例(推荐使用IoC 容器注入)
system_service = SystemService()
