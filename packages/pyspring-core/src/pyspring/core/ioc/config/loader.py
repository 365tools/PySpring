"""
IOC配置加载器

支持从YAML配置文件加载服务定义
"""
import os
from typing import Any

import yaml

from pyspring.core.ioc.annotations.scope import Scope
from pyspring.core.log.instance import logger


class IOCConfig:
    """IOC配置数据模型"""

    def __init__(self, data: dict[str, Any]):
        self.services = data.get('services', {})
        self.scan_packages = data.get('scan_packages', [])
        self.exclude_packages = data.get('exclude_packages', [])


class IOCConfigLoader:
    """
    IOC配置加载器
    
    支持从YAML文件加载服务定义
    
    配置示例：
    ```yaml
    # config/container.yaml
    scan_packages:
      - myapp.services
      - myapp.repositories
    
    exclude_packages:
      - myapp.tests
    
    services:
      # Bean工厂方式（推荐）
      db_config:
        factory: myapp.config.DatabaseConfig.create
        singleton: true
      
      # 直接类名方式（不推荐，建议用@Component）
      user_service:
        class: myapp.services.UserService
        singleton: true
        dependencies:
          user_repo: user_repository
    ```
    """

    def __init__(self, config_path: (str) | None = None):
        """
        Args:
            config_path: 配置文件路径，默认为 config/container.yaml
        """
        self.config_path = config_path or self._find_default_config()
        self.config: (IOCConfig) | None = None

    def _find_default_config(self) -> str:
        """查找默认配置文件"""
        possible_paths = [
            'config/container.yaml',
            'config/ioc.yaml',
            'src/config/container.yaml',
        ]

        for path in possible_paths:
            if os.path.exists(path):
                return path

        # 默认返回第一个路径
        return possible_paths[0]

    def load(self) -> IOCConfig:
        """
        加载配置
        
        Returns:
            IOCConfig: 配置对象
        """
        if not os.path.exists(self.config_path):
            logger.warning(f"⚠️  配置文件不存在: {self.config_path}，使用默认配置")
            self.config = IOCConfig({})
            return self.config

        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f) or {}
                self.config = IOCConfig(data)
                logger.debug(f"✅ 加载IOC配置: {self.config_path}")
                return self.config
        except Exception as e:
            logger.error(f"❌ 加载配置文件失败: {e}")
            self.config = IOCConfig({})
            return self.config

    def get_health_config(self) -> dict[str, Any]:
        """
        获取健康检查配置
        
        Returns:
            Dict: 健康检查配置，包含 enabled 和 indicators
        """
        if not os.path.exists(self.config_path):
            return {'enabled': True}  # 默认启用

        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f) or {}
                return data.get('health', {'enabled': True})
        except Exception as e:
            logger.warning(f"⚠️  读取健康检查配置失败: {e}")
            return {'enabled': True}

    def get_scan_packages(self) -> list[str]:
        """获取要扫描的包列表"""
        if not self.config:
            self.load()
        assert self.config is not None
        return self.config.scan_packages

    def get_service_definitions(self) -> dict[str, dict[str, Any]]:
        """获取服务定义"""
        if not self.config:
            self.load()
        assert self.config is not None
        return self.config.services

    def apply_to_container(self, container):
        """
        将配置应用到容器
        
        Args:
            container: IOC容器
        """
        if not self.config:
            self.load()
        assert self.config is not None

        # 扫描包
        if self.config.scan_packages:
            logger.debug(f"📦 从配置文件扫描包: {self.config.scan_packages}")
            container.scan(self.config.scan_packages)

        # 注册配置中的服务（不推荐，建议用@Component）
        for name, service_def in self.config.services.items():
            self._register_service_from_config(container, name, service_def)

    def _register_service_from_config(self, container, name: str, service_def: dict[str, Any]):
        """
        从配置注册服务
        
        Args:
            container: IOC容器
            name: 服务名称
            service_def: 服务定义
        """
        try:
            # 如果定义了factory，使用工厂方法
            if 'factory' in service_def:
                factory_path = service_def['factory']
                factory = self._resolve_factory(factory_path)
                scope = Scope.SINGLETON if service_def.get('singleton', True) else Scope.PROTOTYPE

                # 使用Bean方式注册
                from pyspring.core.ioc.registry.registry import ServiceDefinition
                definition = ServiceDefinition(
                    name=name,
                    service_type=type(None),  # factory模式不需要类型
                    factory=factory,
                    scope=scope,
                    is_bean=True
                )
                container.registry.register(definition)
                logger.debug(f"✅ 从配置注册Bean: {name}")

            # 如果定义了class，使用类实例化（不推荐）
            elif 'class' in service_def:
                logger.warning(f"⚠️  不推荐在配置文件中直接定义类，建议使用@Component装饰器: {name}")
                # TODO: 实现类实例化逻辑（暂不支持）

        except Exception as e:
            logger.error(f"❌ 注册服务失败 {name}: {e}")

    def _resolve_factory(self, factory_path: str):
        """
        解析工厂方法路径
        
        Args:
            factory_path: 工厂路径，如 'myapp.config.DatabaseConfig.create'
            
        Returns:
            工厂方法
        """
        parts = factory_path.split('.')
        module_path = '.'.join(parts[:-2])
        class_name = parts[-2]
        method_name = parts[-1]

        import importlib
        module = importlib.import_module(module_path)
        cls = getattr(module, class_name)
        factory = getattr(cls, method_name)

        return factory


__all__ = ['IOCConfigLoader', 'IOCConfig']
