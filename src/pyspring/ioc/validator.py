"""
IoC 验证器，用于检测循环依赖等问题
"""
from typing import Dict, List

from pyspring.core.exceptions import CircularDependencyError
from pyspring.log.instance import logger


class IoCValidator:

    @staticmethod
    def validate_dependencies(dependencies_map: Dict[str, List[str]]):
        """
        验证依赖关系，检测循环依赖
        
        Args:
           dependencies_map: 服务名 -> 依赖服务名列表 的映射
        """
        logger.debug("Running circular dependency check...")
        visited = set()
        path = []
        path_set = set()

        def dfs(current: str):
            visited.add(current)
            path.append(current)
            path_set.add(current)

            deps = dependencies_map.get(current, [])
            for dep in deps:
                if dep not in dependencies_map:
                    continue  # 忽略未知的依赖（可能是外部或延迟解析的）

                if dep in path_set:
                    # 发现循环
                    cycle_path = path[path.index(dep):] + [dep]
                    raise CircularDependencyError(f"Detected circular dependency: {' -> '.join(cycle_path)}", cycle=cycle_path)

                if dep not in visited:
                    dfs(dep)

            path_set.remove(current)
            path.pop()

        for service_name in dependencies_map:
            if service_name not in visited:
                dfs(service_name)

        logger.debug("✅ No circular dependencies detected.")
