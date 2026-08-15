from dataclasses import dataclass, field
from typing import Any

from pyspring.core.ioc.annotations.component import Component
from pyspring.core.ioc.annotations.scope import Singleton
from pyspring.core.ioc.interfaces.core import IManaged
from pyspring.core.log.instance import logger
from pyspring.security.authentication.contracts.validator import ISecurityContextValidator


@dataclass
class ContextEvaluationResult:
    claims: dict[str, Any] = field(default_factory=dict)
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    @property
    def is_valid(self) -> bool:
        return len(self.errors) == 0


@Component
@Singleton
class SecurityContextManagerService(IManaged):
    """
    安全上下文管理器（由IOC容器管理单例）
    管理所有的上下文验证器，并汇总验证结果
    """

    def __init__(self):
        super().__init__()
        self.validators: list[ISecurityContextValidator] = []
        logger.info("🔧 SecurityContextManagerService 初始化完成")

    def register(self, validator: ISecurityContextValidator):
        """注册验证器"""
        self.validators.append(validator)
        logger.debug(f"[Success] 注册安全验证器: {validator.name}")

    async def evaluate(self, context: dict[str, Any]) -> ContextEvaluationResult:
        """
        评估安全上下文
        
        Args:
            context: 上下文数据
            
        Returns:
            ContextEvaluationResult: 评估结果对象
        """
        final_claims = {}
        errors = []
        warnings = []

        for v in self.validators:
            try:
                res = await v.validate(context)

                if not res.success:
                    # 如果不是阻断性的，通常记录为 warning 或 error
                    # 这里假设 explicit success=False 为阻断性错误
                    errors.append(f"{v.name}: {res.reason or 'Check failed'}")

                if res.claims:
                    # 只有当 key 不存在，或者值为 list 时才合并？
                    # 简单策略：update (后者覆盖前者)
                    # 改进策略：对于 list 类型的 claim (如 roles, permissions)，进行 append/extend
                    for key, value in res.claims.items():
                        if key in final_claims and isinstance(final_claims[key], list) and isinstance(value, list):
                            final_claims[key].extend(value)
                        else:
                            final_claims[key] = value

                if res.warnings:
                    warnings.extend(res.warnings)

            except Exception as e:
                logger.error(f"[Error] 验证器 {v.name} 执行异常: {e}")
                errors.append(f"{v.name} execution error")

        return ContextEvaluationResult(
            claims=final_claims,
            errors=errors,
            warnings=warnings
        )