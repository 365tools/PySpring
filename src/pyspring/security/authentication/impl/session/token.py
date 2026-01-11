import json
from datetime import datetime, timedelta, UTC
from jose import JWTError, jwt
from pyspring.core.interfaces.ISingleton import ISingletonService
from pyspring.log.instance import logger
from pyspring.repositories.cache.manager import CacheManagerService
from pyspring.repositories.db.manager import DBManagerService
from pyspring.security.authorization.rabc.orm.token_tables import TokenBlacklistTable, RefreshTokenTable
from pyspring.security.authorization.rabc.schema.constant import RevokeTokenReason
from pyspring.core.service import SystemService
from sqlalchemy import select, and_
from typing import Optional, Dict, Any


class TokenManagerService(ISingletonService):
    """
    Token 管理服务
    
    负责 JWT Token 的生成、验证、刷新和撤销管理
    
    [两级存储架构]
    1. Redis层(L1缓存): 快速访问, 持久化存储, TTL自动过期
    2. 数据库层(持久化): 最终存储, 防止Redis数据丢失
    
    [读取顺序]Redis -> 数据库(未命中则回写Redis)
    [写入顺序]同时写入Redis + 数据库
    
    [存储内容]
    - Token 黑名单: 已撤销的token
    - Refresh token: 用于刷新access token
    
    [重启影响]
    - 服务重启: 自动从数据库预加载到Redis
    - Redis故障: 自动降级到仅使用数据库
    - Access Token(JWT): 无状态, 重启不影响(除非在黑名单中)
    """

    def __init__(self, system_service: SystemService, cache: CacheManagerService, db: DBManagerService):
        """
        初始化Token管理服务
        
        两级存储架构（懒加载模式）:
        1. Redis层(L1缓存): 快速访问, 持久化存储, TTL自动过期
        2. 数据库层(持久化): 最终存储, 防止Redis数据丢失
        
        读取顺序: Redis -> 数据库(未命中则回写Redis)
        写入顺序: 同时写入Redis + 数据库
        
        为什么不预加载？
        - JWT 是无状态的，验证只需要密钥，不需要数据库
        - 黑名单/refresh token 采用懒加载，首次查询后自动缓存
        - 避免启动时的数据库依赖和初始化顺序问题
        - 大多数 token 可能永远不会被查询（已过期或未使用）
        
        Args:
            system_service: 系统配置服务(获取JWT密钥、过期时间等配置)
            cache: 缓存管理服务(Redis, 单例且由IoC保证注册)
            db: 数据库管理服务(持久化存储)
        """
        self.system_service = system_service
        self.cache = cache
        self.db = db

        # 初始化 JWT 加密管理器（通过 IoC 容器）
        from pyspring.security.authentication.encryption import JWTEncryptionManager
        from pyspring.ioc.manager import AppContainerManager
        container = AppContainerManager()
        self.jwt_encryption = container.get(JWTEncryptionManager)

        if self.jwt_encryption.is_enabled():
            logger.info("🔐 JWT 加密已启用 - Token 将被加密返回")

        logger.info("🔧 TokenManagerService 初始化完成 - 两级架构(懒加载): Redis + 数据库")

    def create_access_token(self, data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
        """
        创建访问 Token
        
        Args:
            data: Token 载荷数据
            expires_delta: 过期时间增量（可选）
            
        Returns:
            JWT token 字符。
        """
        to_encode = data.copy()

        # 设置过期时间
        if expires_delta:
            expire = datetime.now(UTC) + expires_delta
        else:
            expire = datetime.now(UTC) + timedelta(
                seconds=self.system_service.get().authentication.jwt.access_token_expire
            )

        to_encode.update({
            "exp": expire,
            "iat": datetime.now(UTC),  # 签发时间
            "type": "access"  # Token 类型
        })

        # 编码 token
        encoded_jwt = jwt.encode(
            to_encode,
            self.system_service.get().authentication.jwt.secret_key,
            algorithm="HS256"
        )

        # 加密 token（如果启用）
        encrypted_token = self.jwt_encryption.encrypt(encoded_jwt)

        logger.debug(f"✅ 创建 Access Token: {data.get('email', 'unknown')}")
        return encrypted_token

    async def create_refresh_token(self, data: Dict[str, Any]) -> str:
        """
        创建刷新 Token（异步版本，支持数据库持久化。
        
        Args:
            data: Token 载荷数据
            
        Returns:
            Refresh token 字符。
            
        两层存储。
            1. 写入数据库（持久化）
            2. 写入Redis（快速访问，TTL自动过期
        """
        to_encode = data.copy()

        # 刷新 token 有效期为 7 。
        expire = datetime.now(UTC) + timedelta(days=7)

        to_encode.update({
            "exp": expire,
            "iat": datetime.now(UTC),
            "type": "refresh"  # 标记为刷。token
        })

        # 编码 token
        encoded_jwt = jwt.encode(
            to_encode,
            self.system_service.get().authentication.jwt.secret_key,
            algorithm="HS256"
        )

        # 加密 token（如果启用）
        encrypted_token = self.jwt_encryption.encrypt(encoded_jwt)

        # Token 信息
        token_info = {
            "user_id": data.get("sub"),
            "created_at": datetime.now(UTC).isoformat(),
            "expires_at": expire.isoformat()
        }

        try:
            # 1. 持久化到数据库（存储原始JWT，不存加密后的）
            async with await self.db.get_session() as session:
                db_record = RefreshTokenTable(
                    token=encoded_jwt,  # 注意：数据库存储未加密的JWT
                    user_id=data.get("sub"),
                    user_email=data.get("email", ""),
                    roles=json.dumps(data.get("roles", [])),
                    issued_at=datetime.now(UTC),
                    expires_at=expire,
                    active=True
                )
                session.add(db_record)
                await session.commit()
                logger.debug(f"✅ Refresh Token 已持久化到数据库: {data.get('email', 'unknown')}")

            # 2. 写入Redis缓存（使用原始JWT作为key。
            try:
                cache_ins = self.cache.ins
                ttl = 7 * 24 * 3600  # 7 天（秒）
                cache_key = f"token:refresh:{encoded_jwt}"  # 注意：缓存key使用未加密的JWT
                await cache_ins.set(cache_key, json.dumps(token_info), ex=ttl)
                logger.debug(f"✅ Refresh Token 已写入Redis: {data.get('email', 'unknown')}")
            except Exception as e:
                logger.warning(f"⚠️ Redis写入失败（数据库已保存）: {e}")

            logger.info(f"✅ 创建 Refresh Token (两级存储): {data.get('email', 'unknown')}")

        except Exception as e:
            logger.error(f"🚨 创建 Refresh Token 失败: {e}")
            raise

        return encrypted_token  # 返回加密后的token

    async def verify_token(self, token: str, token_type: str = "access") -> Optional[Dict[str, Any]]:
        """
        验证 JWT token
        
        Args:
            token: JWT token 字符串（可能加密。
            token_type: Token 类型（access 。refresh。
            
        Returns:
            Token 载荷，如果无效返。None
        """
        try:
            # 解密 token（如果启用了加密。
            decrypted_token = self.jwt_encryption.decrypt(token)
        except Exception as e:
            logger.warning(f"⚠️ Token 解密失败: {e}")
            return None

        # 检查是否在黑名单中（使用解密后的JWT。
        if await self.is_token_revoked(decrypted_token):
            logger.warning("⚠️ Token 已被撤销")
            return None

        try:
            # 解码 token
            payload = jwt.decode(
                decrypted_token,
                self.system_service.get().authentication.jwt.secret_key,
                algorithms=["HS256"]
            )

            # 验证 token 类型
            if payload.get("type") != token_type:
                logger.warning(f"⚠️ Token 类型不匹。 期望 {token_type}, 实际 {payload.get('type')}")
                return None

            return payload

        except JWTError as e:
            logger.warning(f"⚠️ Token 验证失败: {e}")
            return None

    async def refresh_access_token(self, refresh_token: str) -> Optional[str]:
        """
        使用 refresh token 刷新 access token
        
        Args:
            refresh_token: Refresh token 字符。
            
        Returns:
            新的 access token，如果refresh token 无效返回 None
            
        查询顺序。
            1. 验证JWT签名和过期时。
            2. 查询 Redis -> 数据库（未命中则回写Redis。
            3. 确认token有效且未撤销
        """
        # 验证 refresh token
        payload = await self.verify_token(refresh_token, token_type="refresh")

        if not payload:
            logger.warning("⚠️ Refresh token 无效")
            return None

        # 检。refresh token 是否存在（两级查询）
        token_exists = False

        # 1. 查询Redis
        try:
            cache_ins = self.cache.ins
            cache_key = f"token:refresh:{refresh_token}"
            token_exists = await cache_ins.exists(cache_key)
        except Exception as e:
            logger.warning(f"⚠️ Redis查询失败: {e}")

        # 2. 查询数据库（兜底。
        if not token_exists:
            try:
                async with await self.db.get_session() as session:
                    stmt = select(RefreshTokenTable).where(
                        and_(
                            RefreshTokenTable.token == refresh_token,
                            RefreshTokenTable.active == True,
                            RefreshTokenTable.expires_at > datetime.now(UTC)
                        )
                    )
                    result = await session.execute(stmt)
                    record = result.scalar_one_or_none()

                    if record:
                        token_exists = True
                        # 回写到Redis
                        try:
                            cache_ins = self.cache.ins
                            cache_key = f"token:refresh:{refresh_token}"
                            ttl = int((record.expires_at - datetime.now(UTC)).total_seconds())
                            if ttl > 0:
                                token_info = {
                                    "user_id": record.user_id,
                                    "created_at": record.issued_at.isoformat(),
                                    "expires_at": record.expires_at.isoformat()
                                }
                                await cache_ins.set(cache_key, json.dumps(token_info), ex=ttl)
                                logger.debug("✅ 从数据库加载并回写Redis")
                        except Exception as e:
                            logger.warning(f"⚠️ 回写Redis失败: {e}")
            except Exception as e:
                logger.error(f"🚨 数据库查询失败: {e}")

        if not token_exists:
            logger.warning("⚠️ Refresh token 不存在或已失效")
            return None

        # 创建新的 access token（复用原有数据）
        new_access_token = self.create_access_token(
            data={
                "sub": payload.get("sub"),
                "email": payload.get("email"),
                "user_id": payload.get("user_id"),
                "roles": payload.get("roles", [])
            }
        )

        logger.info(f"✅ 刷新 Access Token: {payload.get('email', 'unknown')}")
        return new_access_token

    async def revoke_token(self, token: str, reason: str = "用户登出") -> bool:
        """
        撤销 token（加入黑名单。
        
        Args:
            token: 要撤销。token
            reason: 撤销原因
            
        Returns:
            是否成功撤销
            
        两层存储。
            1. 写入数据库（持久化）
            2. 写入Redis（快速查询，TTL自动过期
        """
        try:
            # 解析token获取信息
            payload = jwt.decode(
                token,
                self.system_service.get().authentication.jwt.secret_key,
                algorithms=["HS256"],
                options={"verify_signature": False}
            )
            exp = payload.get("exp", 0)
            ttl = max(int(exp - datetime.now(UTC).timestamp()), 0)

            if ttl <= 0:
                logger.warning("⚠️ Token已过期，无需撤销")
                return True

            # 1. 持久化到数据。
            async with await self.db.get_session() as session:
                db_record = TokenBlacklistTable(
                    token=token,
                    user_id=payload.get("sub", 0),
                    expires_at=datetime.fromtimestamp(exp),
                    reason=reason
                )
                session.add(db_record)
                await session.commit()
                logger.debug(f"✅ Token黑名单已持久化: user_id={payload.get('sub')}")

            # 2. 写入Redis缓存
            try:
                cache_ins = self.cache.ins
                cache_key = f"token:blacklist:{token}"
                await cache_ins.set(cache_key, "1", ex=ttl)
                logger.debug("✅ Token已加入Redis黑名单")
            except Exception as e:
                logger.warning(f"⚠️ Redis写入失败(数据库已保存): {e}")

            logger.info(f"✅ Token已撤销(两级存储): reason={reason}")
            return True

        except Exception as e:
            logger.error(f"🚨 撤销Token失败: {e}")
            return False

    async def is_token_revoked(self, token: str) -> bool:
        """
        检。token 是否已被撤销
        
        Args:
            token: Token 字符。
            
        Returns:
            是否已被撤销
            
        查询顺序。
            1. Redis（快速）
            2. 数据库（保底，未命中则回写Redis。
        """
        # 1. 查询Redis
        try:
            cache_ins = self.cache.ins
            cache_key = f"token:blacklist:{token}"
            exists = await cache_ins.exists(cache_key)
            if exists:
                return True
        except Exception as e:
            logger.warning(f"⚠️ Redis查询失败: {e}")

        # 2. 查询数据库（兜底。
        try:
            async with await self.db.get_session() as session:
                stmt = select(TokenBlacklistTable).where(
                    and_(
                        TokenBlacklistTable.token == token,
                        TokenBlacklistTable.expires_at > datetime.now(UTC)
                    )
                )
                result = await session.execute(stmt)
                record = result.scalar_one_or_none()

                if record:
                    # 回写到Redis
                    try:
                        cache_ins = self.cache.ins
                        cache_key = f"token:blacklist:{token}"
                        ttl = int((record.expires_at - datetime.now(UTC)).total_seconds())
                        if ttl > 0:
                            await cache_ins.set(cache_key, "1", ex=ttl)
                            logger.debug("✅ 从数据库加载并回写Redis")
                    except Exception as e:
                        logger.warning(f"⚠️ 回写Redis失败: {e}")

                    return True
        except Exception as e:
            logger.error(f"🚨 数据库查询失。 {e}")

        return False

    async def revoke_refresh_token(self, refresh_token: str) -> bool:
        """
        撤销 refresh token
        
        Args:
            refresh_token: 要撤销。refresh token
            
        Returns:
            是否成功撤销
            
        两层更新
            1. 更新数据库（标记为无效）
            2. 删除Redis缓存
        """
        try:
            # 1. 更新数据库（标记为无效，不删除记录）
            async with await self.db.get_session() as session:
                stmt = select(RefreshTokenTable).where(
                    RefreshTokenTable.token == refresh_token
                )
                result = await session.execute(stmt)
                record = result.scalar_one_or_none()

                if record:
                    record.active = False
                    record.modifier = "system"
                    record.modified_time = datetime.now(UTC)
                    await session.commit()
                    logger.debug(f"✅ Refresh Token已标记为无效: user_id={record.user_id}")

            # 2. 删除Redis缓存
            try:
                cache_ins = self.cache.ins
                cache_key = f"token:refresh:{refresh_token}"
                await cache_ins.delete(cache_key)
                logger.debug("✅ 已从Redis删除Refresh Token")
            except Exception as e:
                logger.warning(f"⚠️ Redis删除失败: {e}")

            logger.info("✅ Refresh Token已撤销（两级存储）")
            return True

        except Exception as e:
            logger.error(f"🚨 撤销Refresh Token失败: {e}")
            return False

    async def cleanup_expired_tokens(self) -> int:
        """
        清理数据库中过期的token记录（定期任务）
        
        Returns:
            清理。token 数量
            
        注意。
            - Redis：TTL自动过期，无需手动清理
            - 数据库：建议每天执行一次清理，删除过期记录节省空间
        """
        try:
            async with await self.db.get_session() as session:
                now = datetime.now(UTC)

                # 清理过期的黑名单
                from sqlalchemy import delete
                blacklist_stmt = delete(TokenBlacklistTable).where(
                    TokenBlacklistTable.expires_at < now
                )
                blacklist_result = await session.execute(blacklist_stmt)

                # 清理过期的refresh token
                refresh_stmt = delete(RefreshTokenTable).where(
                    RefreshTokenTable.expires_at < now
                )
                refresh_result = await session.execute(refresh_stmt)

                await session.commit()

                total_deleted = blacklist_result.rowcount + refresh_result.rowcount
                logger.info(f"🧹 清理过期Token - 黑名。 {blacklist_result.rowcount}, Refresh: {refresh_result.rowcount}")
                return total_deleted
        except Exception as e:
            logger.error(f"🚨 清理过期Token失败: {e}")
            return 0

    async def get_token_info(self, token: str) -> Optional[Dict[str, Any]]:
        """
        获取 token 的详细信息（不验证签名，仅解析）
        
        Args:
            token: Token 字符。
            
        Returns:
            Token 信息字典
        """
        try:
            # 不验证签名，仅解。
            payload = jwt.decode(
                token,
                self.system_service.get().authentication.jwt.secret_key,
                algorithms=["HS256"],
                options={"verify_signature": False}
            )

            return {
                "user_id": payload.get("sub"),
                "email": payload.get("email"),
                "roles": payload.get("roles", []),
                "issued_at": datetime.fromtimestamp(payload.get("iat", 0)),
                "expires_at": datetime.fromtimestamp(payload.get("exp", 0)),
                "type": payload.get("type"),
                "is_expired": datetime.fromtimestamp(payload.get("exp", 0)) < datetime.now(UTC),
                "is_revoked": await self.is_token_revoked(token)
            }
        except Exception as e:
            logger.warning(f"⚠️ 解析 Token 失败: {e}")
            return None

    async def revoke_user_refresh_tokens(self, session, user_id: int, reason: str = RevokeTokenReason.USER_LOGIN) -> int:
        """
        撤销用户所有活跃的 Refresh Token（再次登录时调用。

        Args:
            session: 数据库会。
            user_id: 用户ID
            reason: 撤销原因

        Returns:
            撤销。token 数量
        """
        try:
            # 查询该用户所有活跃的 refresh token
            stmt = select(RefreshTokenTable).where(
                RefreshTokenTable.user_id == user_id,
                RefreshTokenTable.active == True,
                RefreshTokenTable.deleted == False
            )
            result = await session.execute(stmt)
            active_tokens = result.scalars().all()

            if not active_tokens:
                return 0

            # 标记为失。
            for token_record in active_tokens:
                token_record.active = False
                token_record.deleted = True
                token_record.revoke_reason = reason
                token_record.modifier = "system"
                token_record.modified_time = datetime.now(UTC)

                # 。Redis 中删除（如果存在
                try:
                    cache_key = f"token:refresh:{token_record.token}"
                    deleted = await self.cache.ins.delete(cache_key)
                    logger.debug(f"🔍 Redis删除结果: {deleted}")
                except Exception as e:
                    logger.warning(f"⚠️ 删除Redis缓存失败: {e}")

            # 提交撤销操作到数据库
            await session.commit()
            await session.flush()
            logger.debug("💾 已提交撤销(Token)操作到数据库")
            logger.info(f"✅ 撤销用户 {user_id} 。{len(active_tokens)} 个旧 Refresh Token")
            return len(active_tokens)

        except Exception as e:
            logger.error(f"🚨 撤销。token 失败: {e}")
            return 0

    @classmethod
    async def cancel_background_tasks(cls):
        """
        取消所有后台任务（已废弃）
        
        TokenManagerService 已改为懒加载模式，不再使用后台任务。
        此方法仅为兼容性保留。
        """
        pass  # 不再需要任何操作
