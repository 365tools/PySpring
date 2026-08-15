'''
Memcached 缓存服务实现
'''
from typing import Any
import asyncio

from pyspring.core.log.instance import logger
from ....service import ICacheService


class MemcachedService(ICacheService):
    '''Memcached 缓存服务实现'''
    
    def __init__(self, config):
        '''
        初始化 Memcached 服务
        
        Args:
            config: 缓存配置对象
        '''
        self.config = config
        self.client = None
        self._connected = False
        
        try:
            import pymemcache  # pyright: ignore[reportMissingImports]  # 可选依赖
            memcached_config = getattr(config, 'memcached', None)
            if memcached_config:
                self.client = pymemcache.Client(
                    (memcached_config.host, memcached_config.port),
                    connect_timeout=memcached_config.connect_timeout,
                    timeout=memcached_config.timeout,
                    no_delay=True
                )
            else:
                # 默认配置
                self.client = pymemcache.Client(('localhost', 11211))
            
            logger.info("✅ Memcached 服务初始化完成")
            self._connected = True
        except ImportError:
            logger.warning("❌ pymemcache 未安装，无法使用 Memcached 服务")
            self._connected = False
        except Exception as e:
            logger.error(f"❌ Memcached 服务初始化失败: {e}")
            self._connected = False
    
    async def ping(self) -> bool:
        '''
        检查 Memcached 连接状态
        
        Returns:
            bool: 连接是否正常
        '''
        if not self._connected or not self.client:
            return False
        
        try:
            # 使用一个临时键进行测试
            test_key = "__health_check__"
            test_value = "test"
            
            # 设置并获取测试值
            self.client.set(test_key, test_value, expire=1)  # 1秒后过期
            result = self.client.get(test_key)
            
            return result == test_value
        except Exception as e:
            logger.error(f"Memcached ping 测试失败: {e}")
            return False
    
    async def get(self, key: str) -> (Any) | None:
        '''
        获取缓存值
        
        Args:
            key: 缓存键
            
        Returns:
            (Any) | None: 缓存值，不存在则返回 None
        '''
        if not self.client:
            return None
        
        try:
            value = self.client.get(key)
            logger.debug(f"[Memcached] GET: {key} -> {value is not None}")
            return value
        except Exception as e:
            logger.error(f"[Memcached] GET 失败 {key}: {e}")
            return None
    
    async def set(self, key: str, value: Any, ttl: (int) | None = None) -> bool:
        '''
        设置缓存值
        
        Args:
            key: 缓存键
            value: 缓存值
            ttl: 过期时间（秒），None 表示永不过期
            
        Returns:
            bool: 是否设置成功
        '''
        if not self.client:
            return False
        
        try:
            expire = ttl if ttl is not None else 0  # 0 表示永不过期
            result = self.client.set(key, value, expire=expire)
            logger.debug(f"[Memcached] SET: {key} -> {result}")
            return result
        except Exception as e:
            logger.error(f"[Memcached] SET 失败 {key}: {e}")
            return False
    
    async def exists(self, key: str) -> bool:
        '''
        检查键是否存在
        
        Args:
            key: 缓存键
            
        Returns:
            bool: 是否存在
        '''
        if not self.client:
            return False
        
        try:
            value = self.client.get(key)
            exists = value is not None
            logger.debug(f"[Memcached] EXISTS: {key} -> {exists}")
            return exists
        except Exception as e:
            logger.error(f"[Memcached] EXISTS 失败 {key}: {e}")
            return False
    
    async def delete(self, *keys: str) -> bool:
        '''
        删除缓存键
        
        Args:
            keys: 要删除的键列表
            
        Returns:
            bool: 是否删除成功
        '''
        if not self.client or not keys:
            return False
        
        try:
            # Memcached 的 delete_multi 方法
            result = self.client.delete_many(list(keys))
            deleted_count = len([k for k in keys if k not in result])  # 删除失败的键不在 result 中
            logger.debug(f"[Memcached] DELETE: {len(keys)} keys, {deleted_count} deleted")
            return deleted_count > 0
        except Exception as e:
            logger.error(f"[Memcached] DELETE 失败: {e}")
            return False
    
    async def scan(self, cursor: int = 0, match: str | None = None, count: int = 100) -> tuple[int, list[str]]:
        '''
        扫描缓存键（Memcached 不原生支持，返回空结果）
        
        Args:
            cursor: 游标位置
            match: 匹配模式
            count: 返回数量
            
        Returns:
            tuple[int, list[str]]: (下一个游标, 键列表)
        '''
        # Memcached 不支持扫描操作，返回空结果
        logger.warning("[Memcached] Scan operation not supported, returning empty result")
        return 0, []
    
    async def keys(self, pattern: str = "*") -> list[str]:
        '''
        获取匹配模式的所有键（Memcached 不支持，返回空列表）
        
        Args:
            pattern: 键模式
            
        Returns:
            list[str]: 键列表
        '''
        logger.warning("[Memcached] Keys operation not supported, returning empty list")
        return []
    
    async def flush(self) -> bool:
        '''
        清空所有缓存
        
        Returns:
            bool: 是否清空成功
        '''
        if not self.client:
            return False
        
        try:
            result = self.client.flush_all()
            logger.info("[Memcached] Flush all executed")
            return result
        except Exception as e:
            logger.error(f"[Memcached] Flush 失败: {e}")
            return False
    
    async def close(self) -> None:
        '''关闭连接'''
        if self.client:
            try:
                # pymemcache 没有显式的关闭方法，但我们可以清空连接
                self.client = None
                self._connected = False
                logger.info("[Memcached] 连接已关闭")
            except Exception as e:
                logger.error(f"[Memcached] 关闭连接时出错: {e}")
    
    async def save(self, key: str, value: Any, ttl: (int) | None = None) -> Any:
        '''保存缓存值'''
        return await self.set(key, value, ttl)
    
    async def update(self, key: str, value: Any, ttl: (int) | None = None) -> Any:
        '''更新缓存值'''
        return await self.set(key, value, ttl)
    
    async def clear(self) -> None:
        '''清空所有缓存'''
        if self.client:
            try:
                result = self.client.flush_all()
                return result
            except Exception as e:
                logger.error(f"[Memcached] Clear 失败: {e}")
                return None

