"""
认证链管理器
实现责任链模式，按优先级顺序执行多个认证提供者

"""

from fastapi import Request

from pyspring.core.ioc.annotations.component import Component
from pyspring.core.ioc.annotations.scope import Singleton
from pyspring.core.ioc.interfaces.core import IManaged
from pyspring.core.log.instance import logger
from pyspring.security.authentication.contracts.request_auth import (
    IRequestAuthenticationProvider,
    RequestAuthenticationResult
)
from pyspring.security.authentication.infrastructure.path_matcher import PathMatcher
from pyspring.security.core.config.loader import SecurityConfigManager


@Component
@Singleton
class AuthenticationChain(IManaged):
    """认证链（责任链模式）- 由IOC容器管理单例"""

    def __init__(self, config_manager: SecurityConfigManager):
        """
        初始化认证链
        
        Args:
            config_manager: 安全配置管理器（通过IOC注入）
        """
        self.providers: list[IRequestAuthenticationProvider] = []
        self.config_manager = config_manager
        logger.info("🔧 AuthenticationChain 初始化完成")

    @property
    def whitelist_config(self) -> list[str]:
        """获取白名单配置"""
        return self.config_manager.get_whitelist_config()

    def register_provider(self, provider: IRequestAuthenticationProvider):
        """
        注册认证提供者
        
        Args:
            provider: 认证提供者实例
        """
        if not provider.is_enabled():
            logger.info(f"[Skip] 跳过已禁用的提供者: {provider.get_name()}")
            return

        self.providers.append(provider)
        logger.info(f"[Success] 注册认证提供者: {provider.get_name()} (优先级: {provider.get_priority()})")

    def register_providers(self, providers: list[IRequestAuthenticationProvider]):
        """
        批量注册认证提供者
        
        Args:
            providers: 认证提供者列表
        """
        for provider in providers:
            self.register_provider(provider)

        # 按优先级排序（数字越小优先级越高）
        self.providers.sort(key=lambda p: p.get_priority())

        logger.info(f"[Info] 认证提供者链已构建，共 {len(self.providers)} 个提供者")
        for idx, provider in enumerate(self.providers, 1):
            logger.info(f"  {idx}. {provider.get_name()} (优先级: {provider.get_priority()})")

    def is_public_path(self, path: str) -> bool:
        """
        检查路径是否在白名单中
        
        Args:
            path: 请求路径
            
        Returns:
            bool: 是否为公开路径（无需认证）
        """
        return PathMatcher.is_match(path, self.whitelist_config)

    async def authenticate(self, request: Request) -> RequestAuthenticationResult:
        """
        执行认证链
        
        按优先级顺序执行所有启用的认证提供者，直到：
        1. 某个提供者认证成功 -> 返回成功结果
        2. 所有提供者都失败 -> 返回失败结果
        
        Args:
            request: FastAPI Request 对象
            
        Returns:
            RequestAuthenticationResult: 认证结果
        """
        if not self.providers:
            logger.warning("[Warning]  没有可用的认证提供者")
            return RequestAuthenticationResult(
                success=False,
                error_message="未配置认证提供者",
                provider_name="system"
            )

        # 检查是否为公开路径
        path = request.url.path
        if self.is_public_path(path):
            logger.debug(f"[Success] 公开路径，跳过认证: {path}")
            return RequestAuthenticationResult(
                success=True,
                provider_name="whitelist"
            )

        # 收集所有失败信息
        failures: list[str] = []

        # 按优先级顺序执行认证
        for provider in self.providers:
            logger.debug(f"[Debug] 尝试认证提供者: {provider.get_name()}")

            try:
                result = await provider.authenticate(request)

                if result.success:
                    logger.info(f"[Success] 认证成功: {provider.get_name()} - 用户: {result.display_name}")
                    return result
                else:
                    # 记录失败原因
                    failures.append(f"{provider.get_name()}: {result.error_message}")
                    logger.debug(f"[Error] 认证失败: {provider.get_name()} - {result.error_message}")

            except Exception as e:
                failures.append(f"{provider.get_name()}: {str(e)}")
                logger.error(f"[Error] 认证提供者异常: {provider.get_name()} - {e}")

        # 所有提供者都失败
        error_summary = " | ".join(failures)
        logger.warning(f"[Error] 所有认证提供者都失败: {error_summary}")

        return RequestAuthenticationResult(
            success=False,
            error_message=f"认证失败: {error_summary}",
            provider_name="chain"
        )

    def get_provider_count(self) -> int:
        """获取已注册的提供者数量"""
        return len(self.providers)

    def get_providers(self) -> list[IRequestAuthenticationProvider]:
        """获取所有已注册的提供者"""
        return self.providers.copy()

    def clear_providers(self):
        """清除所有提供者"""
        self.providers.clear()
        logger.info("[Clear] 已清除所有认证提供者")

    def reload_whitelist(self):
        """重新加载白名单配置"""
        self.config_manager.reload()
        # whitelist_config 为只读 property，reload 后自动读取最新配置
        logger.info("[reload] 白名单配置已重新加载")
