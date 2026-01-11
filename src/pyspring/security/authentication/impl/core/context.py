from typing import List, Dict, Any
from pyspring.log.instance import logger
from pyspring.core.interfaces.ISingleton import ISingletonService
from pyspring.security.authentication.interfaces.validator import ISecurityContextValidator

from dataclasses import dataclass, field

@dataclass
class ContextEvaluationResult:
    claims: Dict[str, Any] = field(default_factory=dict)
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    
    @property
    def is_valid(self) -> bool:
        return len(self.errors) == 0

class SecurityContextManagerService(ISingletonService):
    """
    安全上下文管理器
    管理所有的上下文验证器，并汇总验证结果
    """
    
    def __init__(self):
        super().__init__()
        self.validators: List[ISecurityContextValidator] = []
        logger.info("🔧 SecurityContextManagerService 初始化完成")

    def register(self, validator: ISecurityContextValidator):
        """注册验证器"""
        self.validators.append(validator)
        logger.debug(f"✅ 注册安全验证器: {validator.name}")

    async def evaluate(self, context: Dict[str, Any]) -> ContextEvaluationResult:
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
                
                if not res.get('success', True):
                    # 如果不是阻断性的，通常记录为 warning 或 error
                    # 这里假设 explicit success=False 为阻断性错误
                    errors.append(f"{v.name}: {res.get('reason', 'Check failed')}")
                
                if 'claims' in res:
                    final_claims.update(res['claims'])
                    
                if 'warnings' in res:
                    warnings.extend(res['warnings'])
                    
            except Exception as e:
                logger.error(f"❌ 验证器 {v.name} 执行异常: {e}")
                errors.append(f"{v.name} execution error")

        return ContextEvaluationResult(
            claims=final_claims,
            errors=errors,
            warnings=warnings
        )
