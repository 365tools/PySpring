"""
动态规则引擎
提供灵活的权限验证机制，支持运行时规则配置
"""

import asyncio
from abc import ABC, abstractmethod
from datetime import datetime
from enum import Enum
from typing import Any


class RuleResult(Enum):
    ALLOW = "allow"
    DENY = "deny"
    ABSTAIN = "abstain"  # 不表态，由其他规则决定


class IRule(ABC):
    """规则接口"""

    @abstractmethod
    async def evaluate(self, user_id: Any, resource: str, action: str, context: dict[str, Any]) -> RuleResult:
        """
        评估规则

        Args:
            user_id: 用户ID
            resource: 资源
            action: 动作
            context: 上下文信息

        Returns:
            RuleResult: 规则评估结果
        """
        pass

    @abstractmethod
    def get_name(self) -> str:
        """获取规则名称"""
        pass


class CompositeRule(IRule):
    """复合规则 - 支持AND/OR逻辑组合"""

    def __init__(self, rules: list[IRule], operator: str = "and"):
        """
        Args:
            rules: 子规则列表
            operator: "and" 或 "or"
        """
        self.rules = rules
        self.operator = operator.lower()

    async def evaluate(self, user_id: Any, resource: str, action: str, context: dict[str, Any]) -> RuleResult:
        results = await asyncio.gather(*[rule.evaluate(user_id, resource, action, context) for rule in self.rules])

        if self.operator == "and":
            # AND逻辑：所有规则必须允许
            if RuleResult.DENY in results:
                return RuleResult.DENY
            elif RuleResult.ABSTAIN in results:
                return RuleResult.ABSTAIN
            else:
                return RuleResult.ALLOW
        else:  # OR逻辑
            # OR逻辑：任一规则允许即可
            if RuleResult.ALLOW in results:
                return RuleResult.ALLOW
            elif RuleResult.DENY in results:
                return RuleResult.DENY
            else:
                return RuleResult.ABSTAIN

    def get_name(self) -> str:
        return f"CompositeRule({self.operator})"


class TimeBasedRule(IRule):
    """基于时间的规则"""

    def __init__(self, allowed_hours: list[tuple[int, int]] | None = None, allowed_days: list[int] | None = None):
        """
        Args:
            allowed_hours: 允许的时间段 [(start_hour, end_hour), ...]
            allowed_days: 允许的星期几 [0=周一, 6=周日]
        """
        self.allowed_hours = allowed_hours or [(0, 24)]  # 默认24小时允许
        self.allowed_days = allowed_days or list(range(7))  # 默认一周七天允许

    async def evaluate(self, user_id: Any, resource: str, action: str, context: dict[str, Any]) -> RuleResult:
        now = datetime.now()
        current_day = now.weekday()  # 0=Monday, 6=Sunday
        current_hour = now.hour

        # 检查日期
        if current_day not in self.allowed_days:
            return RuleResult.DENY

        # 检查时间
        allowed = False
        for start_hour, end_hour in self.allowed_hours:
            if start_hour <= current_hour < end_hour:
                allowed = True
                break

        if not allowed:
            return RuleResult.DENY

        return RuleResult.ABSTAIN  # 时间规则不直接允许，交由其他规则决定

    def get_name(self) -> str:
        return "TimeBasedRule"


class ResourceBasedRule(IRule):
    """基于资源的规则"""

    def __init__(self, resource_patterns: list[dict[str, Any]]):
        """
        Args:
            resource_patterns: 资源模式配置
                [
                    {
                        "pattern": "user:*",  # 资源模式
                        "actions": ["read", "write"],  # 允许的动作
                        "effect": "allow"  # allow/deny
                    }
                ]
        """
        self.resource_patterns = resource_patterns

    async def evaluate(self, user_id: Any, resource: str, action: str, context: dict[str, Any]) -> RuleResult:
        for pattern_config in self.resource_patterns:
            pattern = pattern_config["pattern"]
            actions = pattern_config.get("actions", [])
            effect = pattern_config.get("effect", "allow")

            # 简单的模式匹配（支持通配符）
            if self._match_pattern(resource, pattern):
                if action in actions:
                    return RuleResult.ALLOW if effect == "allow" else RuleResult.DENY

        return RuleResult.ABSTAIN

    def _match_pattern(self, resource: str, pattern: str) -> bool:
        """简单的模式匹配"""
        if pattern == "*":
            return True

        # 简单的通配符匹配
        if "*" in pattern:
            pattern_parts = pattern.split("*")
            if len(pattern_parts) == 2:
                if pattern_parts[0] == "":
                    # *suffix 匹配
                    return resource.endswith(pattern_parts[1])
                elif pattern_parts[1] == "":
                    # prefix* 匹配
                    return resource.startswith(pattern_parts[0])
                else:
                    # prefix*suffix 匹配
                    return resource.startswith(pattern_parts[0]) and resource.endswith(pattern_parts[1])

        return resource == pattern

    def get_name(self) -> str:
        return "ResourceBasedRule"


class UserBasedRule(IRule):
    """基于用户的规则"""

    def __init__(self, user_rules: list[dict[str, Any]]):
        """
        Args:
            user_rules: 用户规则配置
                [
                    {
                        "users": ["user1", "user2"],  # 用户列表
                        "resources": ["admin:*"],     # 资源模式
                        "actions": ["*"],             # 动作列表
                        "effect": "allow"             # allow/deny
                    }
                ]
        """
        self.user_rules = user_rules

    async def evaluate(self, user_id: Any, resource: str, action: str, context: dict[str, Any]) -> RuleResult:
        for rule_config in self.user_rules:
            users = rule_config.get("users", [])
            resources = rule_config.get("resources", [])
            actions = rule_config.get("actions", [])
            effect = rule_config.get("effect", "allow")

            # 检查用户
            if str(user_id) not in users:
                continue

            # 检查资源
            resource_match = False
            for res_pattern in resources:
                if self._match_pattern(resource, res_pattern):
                    resource_match = True
                    break

            if not resource_match:
                continue

            # 检查动作
            action_match = False
            for act_pattern in actions:
                if act_pattern == "*" or act_pattern == action:
                    action_match = True
                    break

            if not action_match:
                continue

            return RuleResult.ALLOW if effect == "allow" else RuleResult.DENY

        return RuleResult.ABSTAIN

    def _match_pattern(self, value: str, pattern: str) -> bool:
        """简单的模式匹配"""
        if pattern == "*":
            return True
        return value == pattern

    def get_name(self) -> str:
        return "UserBasedRule"


class RuleEngine:
    """规则引擎主类"""

    def __init__(self, rules: list[IRule]):
        self.rules = rules

    async def evaluate(self, user_id: Any, resource: str, action: str, context: dict[str, Any] | None = None) -> bool:
        """
        评估权限

        Args:
            user_id: 用户ID
            resource: 资源
            action: 动作
            context: 上下文信息

        Returns:
            bool: 是否允许
        """
        if context is None:
            context = {}

        results = await asyncio.gather(*[rule.evaluate(user_id, resource, action, context) for rule in self.rules])

        # DENY 优先原则：如果有DENY，则拒绝
        if RuleResult.DENY in results:
            return False

        # 如果有ALLOW且没有DENY，则允许
        if RuleResult.ALLOW in results:
            return True

        # 如果都是ABSTAIN，默认拒绝
        return False


# 预定义的常用规则引擎
class PredefinedRuleEngines:
    """预定义的规则引擎"""

    @staticmethod
    def create_admin_only_engine():
        """创建仅管理员引擎"""
        admin_rule = UserBasedRule(
            [{"users": ["admin", "root"], "resources": ["*"], "actions": ["*"], "effect": "allow"}]
        )

        deny_all_others = ResourceBasedRule([{"pattern": "*", "actions": ["*"], "effect": "deny"}])

        return RuleEngine([admin_rule, deny_all_others])

    @staticmethod
    def create_business_hours_engine():
        """创建工作时间引擎"""
        time_rule = TimeBasedRule(
            allowed_hours=[(9, 18)],  # 工作时间 9-18点
            allowed_days=[0, 1, 2, 3, 4],  # 工作日
        )

        return RuleEngine([time_rule])
