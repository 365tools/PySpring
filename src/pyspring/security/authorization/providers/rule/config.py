"""
默认路径权限规则提供者（基于配置文件）

从security.yaml读取路径权限映射规则
"""
from typing import Dict, List

from pyspring.log.instance import logger
from pyspring.security.authorization.contracts.rule import IPathPermissionProvider
from pyspring.security.core.config.loader import SecurityConfigManager


class DefaultPathPermissionProvider(IPathPermissionProvider):
    """
    默认的路径权限规则提供者（基于配置文件）
    
    从security.yaml中读取authorization.role_mappings配置
    格式示例：
    ```yaml
    authorization:
      role_mappings:
        "/api/admin/users": ["admin"]
        "/api/admin/settings": ["admin", "super_admin"]
        "/api/user/profile": ["user"]
    ```
    
    用户可以通过实现IPathPermissionProvider接口并注册@Bean来替换此实现
    """

    def __init__(self, config_manager: SecurityConfigManager):
        """
        初始化路径规则提供者
        
        Args:
            config_manager: 安全配置管理器
        """
        self.config_manager = config_manager
        self._rules: Dict[str, List[str]] = {}
        self._load_rules()

    def _load_rules(self):
        """
        从配置文件加载路径权限规则
        
        配置结构：
        authorization.role_mappings (字典格式)
        """
        try:
            # 获取授权配置
            authz_config = self.config_manager.get_authorization_config()

            # 使用role_mappings（字典格式）
            role_mappings = authz_config.get("role_mappings", {})
            if isinstance(role_mappings, dict) and role_mappings:
                self._rules = role_mappings
                logger.info(f"[PathRuleProvider] 已加载 {len(self._rules)} 条路径权限规则")
                return

            # 没有配置规则
            logger.warning("[PathRuleProvider] 未找到路径权限规则配置")

        except Exception as e:
            logger.error(f"[PathRuleProvider] 加载路径权限规则失败: {e}")
            self._rules = {}

    def get_path_rules(self) -> Dict[str, List[str]]:
        """
        获取路径规则映射
        
        Returns:
            Dict[str, List[str]]: 路径 -> 所需角色列表的映射
            例如: {
                "/api/admin/users": ["admin"],
                "/api/user/profile": ["user", "admin"]
            }
        """
        return self._rules

    def reload_rules(self):
        """重新加载规则（可用于配置热更新）"""
        logger.info("[PathRuleProvider] 重新加载路径权限规则")
        self._load_rules()
