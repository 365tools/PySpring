"""
PySpring CLI 版本号统一入口

版本号唯一来源：
- 优先读取已安装包元数据 (importlib.metadata.version)
- 安装缺失（如源码直接运行时）则回退到 pyproject.toml 中的版本

使用方式：
    from pyspring.cli._version import __version__
"""

from importlib import metadata

__all__ = ["__version__", "DISTRIBUTION_NAME"]


# 发行包名（必须与 pyproject.toml 的 [project].name 一致）
DISTRIBUTION_NAME = "pyspring-cli"

# 回退版本：仅在未安装或元数据异常时使用，须与 pyproject.toml 版本保持一致
_FALLBACK_VERSION = "0.0.1"


def _resolve_version() -> str:
    """解析 CLI 自身版本号（而非所依赖的核心框架版本）。"""
    try:
        return metadata.version(DISTRIBUTION_NAME)
    except Exception:
        # 未安装为可分发包时（如直接从源码运行）回退到默认版本
        return _FALLBACK_VERSION


__version__ = _resolve_version()
