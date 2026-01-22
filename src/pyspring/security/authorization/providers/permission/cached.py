"""
缓存权限服务

提供权限查询缓存，提升性能
"""
from typing import Any

from pyspring.log.instance import logger
from pyspring.repositories.cache.manager import CacheManagerService
from pyspring.security.authorization.contracts.permission import IPermissionService


class CachedPermissionService(IPermissionService):
    """
    缓存权限服务（装饰器模式）
    
    在DefaultPermissionService的基础上添加缓存层
    架构：
    - L1缓存：Redis（快速查询）
    - L2数据源：委托给内部的PermissionService
    
    使用场景：
    - 高并发权限检查
    - 频繁访问的权限判定
    """

    def __init__(self, delegate: IPermissionService, cache: CacheManagerService, ttl: int = 300):
        """
        初始化缓存权限服务
        
        Args:
            delegate: 实际的权限服务（被装饰的对象）
            cache: 缓存管理服务
            ttl: 缓存过期时间（秒），默认5分钟
        """
        self.delegate = delegate
        self.cache = cache
        self.ttl = ttl
        logger.info(f"[CachedPermission] 缓存权限服务已初始化 (TTL={ttl}秒)")

    async def has_permission(self, user_id: Any, permission: str) -> bool:
        """
        检查用户是否拥有权限（带缓存）
        
        策略：
        1. 查询缓存
        2. 缓存未命中时查询数据库
        3. 更新缓存
        
        Args:
            user_id: 用户ID
            permission: 权限字符串
            
        Returns:
            bool: 是否拥有权限
        """
        # 1. 构造缓存键
        cache_key = f"perm:{user_id}:{permission}"
        
        # 2. 查询缓存
        try:
            cached = await self.cache.get(cache_key)
            if cached is not None:
                result = cached == "1"
                logger.debug(f"[CachedPermission] 缓存命中: user={user_id}, perm={permission}, result={result}")
                return result
        except Exception as e:
            logger.warning(f"[CachedPermission] 缓存查询失败，降级到数据库: {e}")
        
        # 3. 缓存未命中，查询数据库（委托）
        has_perm = await self.delegate.has_permission(user_id, permission)
        
        # 4. 更新缓存
        try:
            await self.cache.set(cache_key, "1" if has_perm else "0", ttl=self.ttl)
            logger.debug(f"[CachedPermission] 缓存已更新: user={user_id}, perm={permission}")
        except Exception as e:
            logger.warning(f"[CachedPermission] 缓存写入失败: {e}")
        
        return has_perm

    async def has_role(self, user_id: Any, role: str) -> bool:
        """
        检查用户是否拥有角色（带缓存）
        
        Args:
            user_id: 用户ID
            role: 角色字符串
            
        Returns:
            bool: 是否拥有角色
        """
        # 1. 构造缓存键
        cache_key = f"role:{user_id}:{role}"
        
        # 2. 查询缓存
        try:
            cached = await self.cache.get(cache_key)
            if cached is not None:
                result = cached == "1"
                logger.debug(f"[CachedPermission] 角色缓存命中: user={user_id}, role={role}, result={result}")
                return result
        except Exception as e:
            logger.warning(f"[CachedPermission] 角色缓存查询失败: {e}")
        
        # 3. 缓存未命中，查询数据库（委托）
        has_role_result = await self.delegate.has_role(user_id, role)
        
        # 4. 更新缓存
        try:
            await self.cache.set(cache_key, "1" if has_role_result else "0", ttl=self.ttl)
            logger.debug(f"[CachedPermission] 角色缓存已更新: user={user_id}, role={role}")
        except Exception as e:
            logger.warning(f"[CachedPermission] 角色缓存写入失败: {e}")
        
        return has_role_result

    async def invalidate_user_cache(self, user_id: Any):
        """
        使用户的所有权限缓存失效
        
        使用场景：
        - 用户权限变更时
        - 用户角色变更时
        
        Args:
            user_id: 用户ID
        """
        try:
            # 使用Redis SCAN命令实现模式删除（避免阻塞）
            deleted_count = 0
            patterns = [f"perm:{user_id}:*", f"role:{user_id}:*"]
            
            for pattern in patterns:
                cursor = 0
                while True:
                    # SCAN命令分批获取匹配的key
                    cursor, keys = await self.cache.scan(cursor, match=pattern, count=100)
                    if keys:
                        await self.cache.delete(*keys)
                        deleted_count += len(keys)
                    # cursor=0表示扫描完成
                    if cursor == 0:
                        break
            
            logger.info(f"[CachedPermission] 用户缓存失效: user={user_id}, 删除{deleted_count}个key")
