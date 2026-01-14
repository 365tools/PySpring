import importlib
import json
import pkgutil
from pathlib import Path
from typing import List, Tuple

from pyspring.log.instance import logger


class ModuleScanner:
    """模块扫描器"""

    CACHE_DIR = Path(".pyspring_cache")

    def __init__(self, registrar):
        self.registrar = registrar

    @staticmethod
    def get_package_info(package_path_list: List[str]) -> Tuple[float, int]:
        """获取包路径下最新的修改时间和文件数量"""
        max_mtime = 0.0
        file_count = 0
        for path_str in package_path_list:
            path = Path(path_str)
            if not path.exists(): continue
            if path.is_file():
                mtime = path.stat().st_mtime
                if mtime > max_mtime: max_mtime = mtime
                file_count += 1
            else:
                for p in path.rglob("*.py"):
                    mtime = p.stat().st_mtime
                    if mtime > max_mtime: max_mtime = mtime
                    file_count += 1
        return max_mtime, file_count

    def scan_and_register_services(self, base_package: str, config: dict):
        """
        扫描包并注册服务
        
        Args:
            base_package: 基础包名
            config: 配置字典
        """
        try:
            # 导入基础包
            package = importlib.import_module(base_package)

            # --- 缓存逻辑 ---
            cache_enabled = config.get('container', {}).get('scan_cache', True)
            path_list = getattr(package, '__path__', [])
            if not path_list and getattr(package, '__file__', None):
                # 处理单文件模块的情况
                path_list = [package.__file__]

            cache_modules = None
            current_mtime = 0.0
            current_count = 0

            if cache_enabled and path_list:
                try:
                    current_mtime, current_count = self.get_package_info(path_list)
                    cache_file = self.CACHE_DIR / f"{base_package}.json"
                    if cache_file.exists():
                        with open(cache_file, 'r') as f:
                            data = json.load(f)
                            # 校验: 时间戳一致 AND 文件数量一致
                            cached_mtime = data.get('mtime', 0)
                            cached_count = data.get('count', 0)

                            if abs(cached_mtime - current_mtime) < 0.001 and cached_count == current_count:
                                cache_modules = data.get('modules')
                                logger.debug(f"🚀 Using scan cache for {base_package}")
                except Exception as e:
                    logger.warning(f"Cache load failed: {e}")

            # 命中缓存：直接加载指定模块
            if cache_modules is not None:
                for modname in cache_modules:
                    try:
                        m = importlib.import_module(modname)
                        self.registrar.scan_module(m)
                    except Exception:
                        pass
                return

            # --- 未命中缓存：执行完整扫描 ---
            useful_modules = []

            # 如果是单个模块文件而不是包，直接扫描该模块
            if not hasattr(package, '__path__'):
                if self.registrar.scan_module(package):
                    useful_modules.append(package.__name__)
            else:
                # 使用pkgutil递归扫描所有子模块
                for importer, modname, ispkg in pkgutil.walk_packages(
                        path=package.__path__,
                        prefix=package.__name__ + ".",
                        onerror=lambda x: None
                ):
                    try:
                        # 导入模块
                        module = importlib.import_module(modname)
                        if self.registrar.scan_module(module):
                            useful_modules.append(modname)
                    except Exception as e:
                        logger.error(f"Warning: Could not process module {modname}: {e}")

            # --- 保存缓存 ---
            if cache_enabled and path_list and useful_modules:
                try:
                    self.CACHE_DIR.mkdir(exist_ok=True)
                    with open(self.CACHE_DIR / f"{base_package}.json", 'w') as f:
                        json.dump({
                            'mtime': current_mtime,
                            'count': current_count,
                            'modules': useful_modules
                        }, f)
                        logger.debug(f"💾 Saved scan cache for {base_package}")
                except Exception:
                    pass

        except ImportError as e:
            logger.debug(f"Error importing base package {base_package}: {e}")
