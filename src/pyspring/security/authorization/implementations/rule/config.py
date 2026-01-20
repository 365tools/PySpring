from typing import Dict, List

from pyspring.security.authorization.contracts.rule import IPathPermissionProvider
from pyspring.security.core.config.loader import SecurityConfigManager


class DefaultPathPermissionProvider(IPathPermissionProvider):
    """
    默认的路径权限规则提供者（基于配置文件）
    读取 security.yaml 中的 authorization.rules 配置
    允许用户通过实现 IPathPermissionProvider 接口并注册 Bean 来替换此默认实现
    """

    def __init__(self, config_manager: SecurityConfigManager):
        self.config_manager = config_manager
        self._rules: Dict[str, List[str]] = {}
        self._load_rules()

    def _load_rules(self):
        """加载规则"""
        # 假设配置结构:
        # authorization:
        #   rules:
        #     - path: /api/user/
        #       roles: ["admin", "user"]
        #     - path: /api/admin/
        #       roles: ["admin"]

        auth_config = self.config_manager.get_config().get("authorization", {})
        rules_config = auth_config.get("rules", [])

        # 兼容字典格式 (旧格式) 或列表格式 (新推荐格式)
        if isinstance(rules_config, dict):
            self._rules = rules_config
        elif isinstance(rules_config, list):
            for item in rules_config:
                path = item.get("path")
                roles = item.get("roles", [])
                if path:
                    self._rules[path] = roles

    def get_path_rules(self) -> Dict[str, List[str]]:
        return self._rules
