"""
上下文变量解析器 - 解析和注册上下文变量

职责：处理YAML中的上下文配置，合并代码注册的变量
"""
import importlib
from typing import Dict, Any, List, Tuple

from pyspring.core.context.registry import ContextRegistry

from ..config.patcher import set_context_vars_definitions, _CONTEXT_VARS_DEFINITIONS


class ContextResolver:
    """
    上下文变量解析器
    
    负责解析YAML配置中的上下文变量，并与代码注册的变量合并。
    """

    @classmethod
    def get_active_context_vars(cls) -> List[Tuple[str, Any, Any]]:
        """
        合并YAML配置和核心注册表的上下文变量
        
        Returns:
            List[Tuple[str, ContextVar, Any]]: (key, context_var, default) 列表
        """
        # 从核心获取所有代码注册的变量
        registry_vars = ContextRegistry.get_all()

        # 使用字典去重
        merged = {}

        # 1. 先放Global Definitions（YAML加载的）
        for key, var_path, default_val in _CONTEXT_VARS_DEFINITIONS:
            try:
                if var_path:
                    module_name, var_name = var_path.rsplit('.', 1)
                    module = importlib.import_module(module_name)
                    ctx_var = getattr(module, var_name)
                    merged[key] = (key, ctx_var, default_val)
            except Exception:
                pass

        # 2. 再放Core Registry的（覆盖前者）
        for item in registry_vars:
            merged[item[0]] = item

        return list(merged.values())

    @classmethod
    def resolve_context_vars(cls, logging_config: Dict[str, Any]) -> List[Tuple[str, str, Any]]:
        """
        解析上下文变量配置
        
        Args:
            logging_config: 日志配置字典
            
        Returns:
            List[Tuple[str, str, Any]]: (key, var_path, default) 列表
        """
        context_vars_definitions = []

        context_config = logging_config.get('context', {})
        fields = context_config.get('fields', [])

        # 默认回退：始终确保trace_id存在（除非YAML已显式定义）
        has_trace_id = any(f.get('key') == 'trace_id' for f in fields)
        if not has_trace_id:
            fields.append({
                "key": "trace_id",
                "var": "pyspring.log.providers.loguru.utils.trace_context._trace_id_ctx",
                "default": "sys"
            })

        for field in fields:
            key = field.get('key')
            var_path = field.get('var')
            default_val = field.get('default', "")

            if not key or not var_path:
                continue

            context_vars_definitions.append((key, var_path, default_val))

        return context_vars_definitions

    @classmethod
    def apply_context_config(cls, definitions: List[Tuple[str, str, Any]]) -> None:
        """
        应用上下文配置到patcher
        
        Args:
            definitions: 上下文变量定义列表
        """
        set_context_vars_definitions(definitions)
