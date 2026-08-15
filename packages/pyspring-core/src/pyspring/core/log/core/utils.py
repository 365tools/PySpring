"""
日志系统公共工具模块

提供框架级的通用工具函数
"""
from pathlib import Path

# 全局缓存
_cached_project_root: (Path) | None = None


def detect_project_root(cache: bool = True) -> Path:
    """
    检测项目根目录
    
    检测策略：
    1. 如果路径包含'src'目录，则src的父目录为项目根
    2. 否则向上查找标志文件（pyproject.toml, setup.py, .git）
    3. 如果都找不到，则使用默认规则
    
    Args:
        cache: 是否使用缓存（默认True）
        
    Returns:
        Path: 项目根目录路径
    """
    global _cached_project_root

    # 使用缓存
    if cache and _cached_project_root is not None:
        return _cached_project_root

    try:
        p = Path(__file__).resolve()
    except NameError:
        p = Path.cwd()

    # 策略1: 检测src目录
    if "src" in p.parts:
        project_root = Path(*p.parts[:p.parts.index("src")])
    else:
        # 策略2: 向上查找标志文件
        current = p
        project_root = None

        while current != current.parent:
            if (current / "pyproject.toml").exists() or \
                    (current / "setup.py").exists() or \
                    (current / ".git").exists():
                project_root = current
                break
            current = current.parent

        # 策略3: 默认规则
        if project_root is None:
            project_root = p.parents[5] if len(p.parents) >= 6 else p.parent.parent.parent

    # 缓存结果
    if cache:
        _cached_project_root = project_root

    return project_root


def get_cached_project_root() -> (Path) | None:
    """
    获取缓存的项目根目录
    
    Returns:
        (Path) | None: 缓存的项目根路径，如果未缓存则返回None
    """
    return _cached_project_root


def set_project_root(root: Path) -> None:
    """
    设置项目根目录缓存
    
    Args:
        root: 项目根目录路径
    """
    global _cached_project_root
    _cached_project_root = root


def clear_project_root_cache() -> None:
    """
    清除项目根目录缓存
    
    主要用于测试场景
    """
    global _cached_project_root
    _cached_project_root = None
