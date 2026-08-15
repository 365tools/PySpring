"""
新版IOC容器管理器

全局容器的单例访问点
"""

from __future__ import annotations

from pyspring.core.ioc.container.container import Container


class ApplicationContext:
    """
    应用上下文（全局IOC容器）
    
    提供全局访问点，简化容器的使用。
    建议在应用启动时初始化一次，之后通过 get_instance() 获取。
    """

    _instance: ApplicationContext | None = None
    _container: Container | None = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    @classmethod
    def initialize(cls, base_packages: (list[str]) | None = None, config_file: (str) | None = None, enable_aop: bool = True):
        """
        初始化应用上下文
        
        Args:
            base_packages: 要扫描的包路径列表（可选，如果提供config_file则可为None）
            config_file: 配置文件路径（可选）
            enable_aop: 是否启用AOP（默认启用）
            
        框架级组件自动加载：
            框架会自动优先扫描以下包，确保框架级服务可用：
            - pyspring.security (安全模块：DBManagerService、IPasswordEncoder等)
            - pyspring.repositories (数据库模块)
            用户无需在 base_packages 中手动添加这些包
        """
        instance = cls()
        instance._container = Container(enable_aop=enable_aop)

        # 如果提供了配置文件，从配置文件加载
        if config_file:
            from pyspring.core.ioc.config.loader import IOCConfigLoader
            loader = IOCConfigLoader(config_file)
            loader.apply_to_container(instance._container)

        # 自动扫描框架级别的包和用户包
        # 关键顺序：框架包先扫描 → 用户包后扫描
        # 原因：
        # 1. 用户的实现可能依赖框架的底层服务（DBManagerService, IPasswordEncoder等）
        # 2. 框架的 @ConditionalOnMissingBean Bean 先注册
        # 3. 用户的 Bean 后注册时，Registry 检测到旧Bean是conditional → 允许替换
        from pyspring.core.log.instance import logger
        framework_packages = cls._load_framework_packages()
        all_packages = []

        # 1️⃣ 优先扫描框架包（提供底层服务和默认实现）
        if framework_packages:
            logger.debug(f"📦 优先扫描框架级别的包: {framework_packages}")
            all_packages.extend(framework_packages)

        # 2️⃣ 然后扫描用户包（用户的 Bean 可以替换框架的 @ConditionalOnMissingBean Bean）
        if base_packages:
            user_packages = [pkg for pkg in base_packages if pkg not in framework_packages]
            if user_packages:
                logger.debug(f"📦 扫描用户包: {user_packages}")
                all_packages.extend(user_packages)

            # 如果用户手动指定了框架包，给出警告
            duplicate_packages = [pkg for pkg in base_packages if pkg in framework_packages]
            if duplicate_packages:
                logger.warning(f"⚠️  用户配置中包含框架包 {duplicate_packages}，已自动去重。框架包会自动扫描，无需手动配置。")

        # 一次性扫描所有包
        if all_packages:
            instance._container.scan(all_packages)

        # 如果既没有配置文件也没有包列表，报错
        if not config_file and not base_packages:
            raise ValueError("必须提供 base_packages 或 config_file 中的至少一个")
        
        return instance

    @classmethod
    def _load_framework_packages(cls) -> list[str]:
        """通过 AutoConfigurationLoader 收集所有已装配 starter 的框架包。

        替代原先的 framework.yaml 集中式硬编码扫描：
        - 引入 starter 即自动装配（即插即用）。
        - 未引入的 starter 不参与扫描。

        Returns:
            按装配顺序排列的框架包列表
        """
        from pyspring.core.autoconfigure.loader import AutoConfigurationLoader
        from pyspring.core.log.instance import logger

        try:
            return AutoConfigurationLoader().collect_scan_packages()
        except Exception as exc:
            logger.warning(f"[autoconfigure] 装配失败: {exc}")
            return []


    @classmethod
    def get_instance(cls) -> 'ApplicationContext':
        """获取应用上下文实例"""
        if cls._instance is None or cls._instance._container is None:
            raise RuntimeError("ApplicationContext未初始化，请先调用 initialize()")
        return cls._instance

    @property
    def container(self) -> Container:
        """获取IOC容器"""
        if self._container is None:
            raise RuntimeError("Container未初始化")
        return self._container

    def get(self, name: str):
        """获取服务（快捷方法）"""
        return self.container.get(name)

    def get_by_type(self, service_type: type):
        """根据类型获取服务（快捷方法）"""
        return self.container.get_by_type(service_type)

    def get_bean(self, service_type: type):
        """根据类型获取Bean（别名方法）"""
        return self.get_by_type(service_type)

    def get_all_of_type(self, service_type: type):
        """获取某类型的所有实例（快捷方法）"""
        return self.container.get_all_of_type(service_type)

    def get_all_instances_of(self, service_type: type):
        """获取某类型的所有实例（get_all_of_type 的语义化别名）"""
        return self.container.get_all_of_type(service_type)


    @staticmethod
    def service(service_type: type):
        """
        静态方法：根据类型获取服务实例
        
        ApplicationContext.service() 的用法，可在 FastAPI Depends 中直接使用：
        
        Example:
            from fastapi import Depends
            from typing import Annotated
            
            @app.post("/login")
            async def login(
                login_service: Annotated[ILoginService, Depends(lambda: ApplicationContext.service(ILoginService))]
            ):
                ...
        
        Args:
            service_type: 服务类型（可以是接口或具体类）
            
        Returns:
            服务实例
        """
        return ApplicationContext.get_instance().get_by_type(service_type)

    @classmethod
    def reset(cls):
        """重置应用上下文（主要用于测试）"""
        cls._instance = None
        cls._container = None


def inject(service_type: type):
    """
    依赖注入快捷函数
    
    用于快速从 ApplicationContext 获取服务实例，
    特别适合在 FastAPI Depends 中使用。
    
    Example:
        from pyspring.core.ioc import inject
        from fastapi import Depends
        from typing import Annotated
        
        @app.post("/login")
        async def login(
            login_service: Annotated[ILoginService, Depends(lambda: inject(ILoginService))]
        ):
            ...
    
    Args:
        service_type: 服务类型（可以是接口或具体类）
        
    Returns:
        服务实例
    """
    return ApplicationContext.service(service_type)


# 大写别名（推荐用于 FastAPI Depends，保持命名一致性）
Inject = inject

__all__ = ['ApplicationContext', 'Inject']
