"""
import os

配置验证

提供配置验证的通用功能
"""
import os
from typing import Any, Callable, Dict, List

from pydantic import ValidationError

from pyspring.log.instance import logger


class ConfigValidator:
    """
    配置验证
    
    提供配置验证和检查功。
    """

    def __init__(self):
        """初始化验证器"""
        self._custom_validators: Dict[str, Callable[[Any], bool]] = {}

    def register_validator(
            self,
            name: str,
            validator: Callable[[Any], bool]
    ) -> None:
        """
        注册自定义验证器
        
        Args:
            name: 验证器名。
            validator: 验证函数，接收配置值，返回是否有效
        """
        self._custom_validators[name] = validator
        logger.debug(f"✅ 已注册验证器: {name}")

    def validate(self, config: Any, strict: bool = False) -> tuple[bool, List[str]]:
        """
        验证配置
        
        Args:
            config: 配置对象
            strict: 是否严格模式（严格模式下任何错误都会导致验证失败
            
        Returns:
            tuple[bool, List[str]]: (是否有效, 错误列表)
        """
        errors = []

        # 如果是Pydantic模型，使用其内置验证
        if hasattr(config, 'model_validate'):
            try:
                config.model_validate(config.model_dump())
            except ValidationError as e:
                errors.extend([str(err) for err in e.errors()])

        # 运行自定义验证器
        for name, validator in self._custom_validators.items():
            try:
                if not validator(config):
                    errors.append(f"自定义验证失败: {name}")
            except Exception as e:
                errors.append(f"验证器 {name} 执行错误: {e}")

        is_valid = len(errors) == 0

        if not is_valid:
            logger.warning(f"⚠️  配置验证发现 {len(errors)} 个问题")
            for error in errors:
                logger.warning(f"  - {error}")

        return is_valid, errors

    def check_required_fields(
            self,
            config: Any,
            required_fields: List[str]
    ) -> tuple[bool, List[str]]:
        """
        检查必需字段是否存在
        
        Args:
            config: 配置对象
            required_fields: 必需字段列表
            
        Returns:
            tuple[bool, List[str]]: (是否有效, 缺失字段列表)
        """
        missing = []

        for field in required_fields:
            if not hasattr(config, field) or getattr(config, field) is None:
                missing.append(field)

        is_valid = len(missing) == 0

        if not is_valid:
            logger.warning(f"⚠️  缺失必需字段: {', '.join(missing)}")

        return is_valid, missing

    def check_env_vars(self, required_vars: List[str]) -> tuple[bool, List[str]]:
        """
        检查必需的环境变量是否存。
        
        Args:
            required_vars: 必需的环境变量列。
            
        Returns:
            tuple[bool, List[str]]: (是否有效, 缺失变量列表)
        """
        missing = []

        for var in required_vars:
            if var not in os.environ:
                missing.append(var)

        is_valid = len(missing) == 0

        if not is_valid:
            logger.warning(f"⚠️  缺失环境变量: {', '.join(missing)}")

        return is_valid, missing


# 全局验证器实。
validator = ConfigValidator()

__all__ = ["ConfigValidator", "validator"]
