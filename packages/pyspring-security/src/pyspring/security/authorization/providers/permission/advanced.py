"""
高级权限服务
结合缓存、规则引擎和传统权限检查的综合权限服务
"""
from typing import Any, Dict
from pyspring.core.log.instance import logger
from pyspring.security.authorization.contracts.permission import IPermissionService
from pyspring.security.authorization.contracts.role import IRoleProvider
from pyspring.security.authorization.contracts.rule_engine import IRuleEngine
from pyspring.security.authorization.providers.permission.default import DefaultPermissionService
from pyspring.repositories.cache.manager import CacheManagerService


class AdvancedPermissionService(IPermissionService):
    """
    高级权限服务
    结合了：
    1. 传统权限检查（通过委托）
    2. 动态规则引擎
    3. 多级缓存机制
    """
    
    def __init__(
        self, 
        role_provider: IRoleProvider,
        rule_engine: IRuleEngine | None = None,
        cache: CacheManagerService | None = None,
        cache_ttl: int = 300
    ):
        """
        初始化高级权限服务
        
        Args:
            role_provider: 角色提供者
            rule_engine: 规则引擎（可选）
            cache: 缓存服务（可选）
            cache_ttl: 缓存过期时间
        """
        self.default_service = DefaultPermissionService(role_provider)
        self.rule_engine = rule_engine
        self.cache = cache
        self.cache_ttl = cache_ttl
        
        # 本地内存缓存
        self._local_cache = {}
        self._cache_timestamps = {}
        
        logger.info("[AdvancedPermissionService] 高级权限服务已初始化")
    
    async def has_permission(self, user_id: Any, permission: str) -> bool:
        """
        检查用户是否拥有权限
        
        评估顺序：
        1. 本地缓存
        2. 分布式缓存
        3. 规则引擎
        4. 传统权限检查
        """
        # 1. 解析权限字符串为资源和动作
        resource, action = self._parse_permission(permission)
        
        # 2. 本地缓存检查
        local_key = f"perm:{user_id}:{permission}"
        result = self._check_local_cache(local_key)
        if result is not None:
            logger.debug(f"[AdvancedPermissionService] 本地缓存命中: {local_key}")
            return result
        
        # 3. 分布式缓存检查（如果有缓存服务）
        # cache_key 提前定义，避免 self.cache 为 None 时后续引用未绑定
        cache_key = f"adv_perm:{user_id}:{permission}"
        if self.cache:
            try:
                cached = await self.cache.get(cache_key)
                if cached is not None:
                    result = cached == "1"
                    self._update_local_cache(local_key, result)
                    logger.debug(f"[AdvancedPermissionService] 分布式缓存命中: {cache_key}")
                    return result
            except Exception as e:
                logger.warning(f"[AdvancedPermissionService] 分布式缓存查询失败: {e}")
        
        # 4. 规则引擎检查（如果有规则引擎）
        if self.rule_engine:
            try:
                context = {
                    "permission": permission,
                    "timestamp": self._get_current_timestamp()
                }
                rule_result = await self.rule_engine.evaluate(user_id, resource, action, context)
                if rule_result is not None:
                    self._update_both_caches(local_key, cache_key, rule_result)
                    logger.debug(f"[AdvancedPermissionService] 规则引擎评估: user={user_id}, perm={permission}, result={rule_result}")
                    return rule_result
            except Exception as e:
                logger.warning(f"[AdvancedPermissionService] 规则引擎评估失败: {e}")
        
        # 5. 传统权限检查
        result = await self.default_service.has_permission(user_id, permission)
        self._update_both_caches(local_key, cache_key, result)
        
        logger.debug(f"[AdvancedPermissionService] 传统权限检查: user={user_id}, perm={permission}, result={result}")
        return result
    
    async def has_role(self, user_id: Any, role: str) -> bool:
        """
        检查用户是否拥有角色
        
        评估顺序：
        1. 本地缓存
        2. 分布式缓存
        3. 传统角色检查
        """
        # 1. 本地缓存检查
        local_key = f"role:{user_id}:{role}"
        result = self._check_local_cache(local_key)
        if result is not None:
            logger.debug(f"[AdvancedPermissionService] 本地角色缓存命中: {local_key}")
            return result
        
        # 2. 分布式缓存检查（如果有缓存服务）
        # cache_key 提前定义，避免后续 if self.cache 分支引用未绑定
        cache_key = f"adv_role:{user_id}:{role}"
        if self.cache:
            try:
                cached = await self.cache.get(cache_key)
                if cached is not None:
                    result = cached == "1"
                    self._update_local_cache(local_key, result)
                    logger.debug(f"[AdvancedPermissionService] 分布式角色缓存命中: {cache_key}")
                    return result
            except Exception as e:
                logger.warning(f"[AdvancedPermissionService] 分布式角色缓存查询失败: {e}")
        
        # 3. 传统角色检查
        result = await self.default_service.has_role(user_id, role)
        if self.cache:
            try:
                await self.cache.set(cache_key, "1" if result else "0", ttl=self.cache_ttl)
            except Exception as e:
                logger.warning(f"[AdvancedPermissionService] 分布式角色缓存写入失败: {e}")
        
        self._update_local_cache(local_key, result)
        
        logger.debug(f"[AdvancedPermissionService] 传统角色检查: user={user_id}, role={role}, result={result}")
        return result
    
    def _parse_permission(self, permission: str) -> tuple[str, str]:
        """
        解析权限字符串为资源和动作
        
        Args:
            permission: 权限字符串，格式如 'user:read', 'article:create'
            
        Returns: tuple[Any, ...]: (resource, action)
        """
        parts = permission.split(':', 1)
        if len(parts) >= 2:
            return parts[0], parts[1]
        else:
            return permission, "access"
    
    def _check_local_cache(self, key: str) -> bool | None:
        """检查本地缓存（未命中返回 None）"""
        import time
        current_time = time.time()
        
        if key in self._local_cache:
            timestamp = self._cache_timestamps.get(key, 0)
            # 本地缓存有效期30秒
            if current_time - timestamp < 30:
                return self._local_cache[key]
            else:
                # 清除过期缓存
                del self._local_cache[key]
                del self._cache_timestamps[key]
        
        return None
    
    def _update_local_cache(self, key: str, value: bool):
        """更新本地缓存"""
        import time
        self._local_cache[key] = value
        self._cache_timestamps[key] = time.time()
    
    def _update_both_caches(self, local_key: str, distributed_key: str, value: bool):
        """同时更新本地和分布式缓存"""
        self._update_local_cache(local_key, value)
        
        if self.cache and distributed_key:
            try:
                import asyncio
                # 使用异步任务更新分布式缓存，避免阻塞
                asyncio.create_task(self._async_update_cache(distributed_key, value))
            except Exception as e:
                logger.warning(f"[AdvancedPermissionService] 异步缓存更新失败: {e}")
    
    async def _async_update_cache(self, key: str, value: bool):
        """异步更新缓存"""
        if self.cache is None:
            return
        try:
            await self.cache.set(key, "1" if value else "0", ttl=self.cache_ttl)
        except Exception as e:
            logger.warning(f"[AdvancedPermissionService] 缓存更新失败: {e}")
    
    def _get_current_timestamp(self) -> int:
        """获取当前时间戳"""
        import time
        return int(time.time())
    
    async def invalidate_user_cache(self, user_id: Any):
        """
        使用户的所有缓存失效
        
        Args:
            user_id: 用户ID
        """
        # 清除本地缓存
        keys_to_remove = [key for key in self._local_cache.keys() if str(user_id) in key]
        for key in keys_to_remove:
            if key in self._local_cache:
                del self._local_cache[key]
            if key in self._cache_timestamps:
                del self._cache_timestamps[key]
        
        # 清除分布式缓存
        if self.cache:
            try:
                # 使用模式匹配清除相关缓存
                patterns = [f"adv_perm:{user_id}:*", f"adv_role:{user_id}:*"]
                
                for pattern in patterns:
                    cursor = 0
                    while True:
                        cursor, keys = await self.cache.scan(cursor, match=pattern, count=100)
                        if keys:
                            await self.cache.delete(*keys)
                        if cursor == 0:
                            break
                
                logger.info(f"[AdvancedPermissionService] 用户缓存已清除: user={user_id}")
            except Exception as e:
                logger.error(f"[AdvancedPermissionService] 分布式缓存清除失败: {e}")
        
        logger.info(f"[AdvancedPermissionService] 用户本地缓存已清除: user={user_id}")


# 便捷的工厂方法
def create_advanced_permission_service(
    role_provider: IRoleProvider,
    rule_engine: IRuleEngine | None = None,
    cache: CacheManagerService | None = None
) -> AdvancedPermissionService:
    """
    创建高级权限服务的便捷方法
    
    Args:
        role_provider: 角色提供者
        rule_engine: 规则引擎
        cache: 缓存服务
        
    Returns:
        AdvancedPermissionService: 高级权限服务实例
    """
    return AdvancedPermissionService(
        role_provider=role_provider,
        rule_engine=rule_engine,
        cache=cache
    )