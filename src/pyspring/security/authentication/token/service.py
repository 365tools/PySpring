"""
重构后的 Token 管理服务

使用策略模式，支持多种 Token 类型
职责明确：编排 Token 生成器、黑名单、存储服务
"""
from datetime import datetime, UTC
from typing import Optional, Dict, Any

from pyspring.ioc.annotations.component import Component
from pyspring.ioc.annotations.scope import Singleton
from pyspring.ioc.context import ApplicationContext
from pyspring.log.instance import logger
from pyspring.repositories.cache.manager import CacheManagerService
from pyspring.repositories.db.manager import DBManagerService
from pyspring.security.authentication.contracts.constant import RevokeTokenReason
from pyspring.security.authentication.contracts.token import ITokenService, ITokenGenerator
from pyspring.security.authentication.factories.token_generator.factory import TokenGeneratorFactory
from pyspring.security.orm.tables import TokenBlacklistTable, RefreshTokenTable
from sqlalchemy import select, and_


@Component()
@Singleton
class TokenService(ITokenService):
    """
    Token 管理服务
    
    【架构设计】
    1. 使用策略模式：Token 生成委托给 ITokenGenerator
    2. 职责分离：生成、验证、撤销、存储逻辑分离
    3. 配置驱动：通过工厂根据配置选择 Token 类型
    
    【两级存储架构】
    - Redis层(L1缓存): 快速访问
    - 数据库层(持久化): 最终存储
    """

    def __init__(self):
        """初始化 Token 服务（懒加载依赖）"""
        self._token_generator: Optional[ITokenGenerator] = None
        self._cache: Optional[CacheManagerService] = None
        self._db: Optional[DBManagerService] = None

        logger.info("[TokenService] Token 服务初始化（策略模式）")

    @property
    def token_generator(self) -> ITokenGenerator:
        """懒加载 Token 生成器（通过工厂模式获取）"""
        if self._token_generator is None:
            # 通过工厂获取默认生成器（可通过配置扩展）
            self._token_generator = TokenGeneratorFactory.get_default_generator()
            logger.info(f"[TokenService] 使用 Token 生成器: {self._token_generator.get_token_type()}")
        return self._token_generator

    @property
    def cache(self) -> CacheManagerService:
        """懒加载缓存服务"""
        if self._cache is None:
            self._cache = ApplicationContext.get_instance().get_by_type(CacheManagerService)
        return self._cache

    @property
    def db(self) -> DBManagerService:
        """懒加载数据库服务"""
        if self._db is None:
            self._db = ApplicationContext.get_instance().get_by_type(DBManagerService)
        return self._db

    def create_access_token(self, data: Dict[str, Any], expires_delta: Optional[Any] = None) -> str:
        """
        创建访问 Token
        
        职责：编排Token生成流程
        - 准备载荷（添加type标记）
        - 委托给Generator进行编码
        
        Args:
            data: Token 载荷数据
            expires_delta: 过期时间增量
            
        Returns:
            str: Token 字符串
        """
        # 准备载荷（标记Token类型）
        payload = data.copy()
        payload["type"] = "access"

        # 委托给Generator编码
        return self.token_generator.encode(payload, expires_delta)

    async def create_refresh_token(self, data: Dict[str, Any], expires_delta: Optional[Any] = None) -> str:
        """
        创建刷新 Token
        
        职责：
        1. 编排Token生成（委托Generator）
        2. 持久化存储（数据库 + Redis）
        
        Args:
            data: Token 载荷数据
            expires_delta: 过期时间增量
            
        Returns:
            str: Refresh Token 字符串
        """
        # 1. 准备载荷
        payload = data.copy()
        payload["type"] = "refresh"

        # 2. 生成 Token（委托给Generator）
        refresh_token = self.token_generator.encode(payload, expires_delta)

        # 3. 解析Token获取过期时间（用于存储）
        decoded = self.token_generator.decode(refresh_token)
        if not decoded:
            raise ValueError("生成的Refresh Token无法解码")

        # 4. 持久化到存储（两级架构）
        try:
            user_id = payload.get("sub")
            exp_timestamp = decoded.get("exp")
            expires_at = datetime.fromtimestamp(int(exp_timestamp), UTC) if exp_timestamp else datetime.now(UTC)

            # 4.1 写入数据库
            async with await self.db.session() as session:
                refresh_record = RefreshTokenTable(
                    user_id=int(user_id) if user_id else 0,
                    refresh_token=refresh_token,
                    expires_at=expires_at,
                    is_revoked=False
                )
                session.add(refresh_record)
                await session.commit()
                logger.debug(f"[TokenService] Refresh Token 已持久化到数据库")

            # 4.2 写入 Redis
            try:
                refresh_key = f"token:refresh:{user_id}:{refresh_token[:16]}"
                await self.cache.set(refresh_key, refresh_token, ttl=7 * 24 * 3600)
                logger.debug(f"[TokenService] Refresh Token 已写入Redis")
            except Exception as e:
                logger.warning(f"[TokenService] Redis写入失败（数据库已保存）: {e}")

            logger.info(f"[TokenService] 创建 Refresh Token (两级存储)")
            return refresh_token

        except Exception as e:
            logger.error(f"[TokenService] 创建 Refresh Token 失败: {e}")
            raise

    async def verify_token(self, token: str) -> Optional[Dict[str, Any]]:
        """
        验证 Token
        
        职责：
        1. 解码Token（委托Generator）
        2. 检查黑名单（服务层逻辑）
        
        Args:
            token: Token 字符串
            
        Returns:
            Optional[Dict]: Token 载荷数据
        """
        try:
            # 1. 解码 Token（委托给Generator）
            payload = self.token_generator.decode(token)
            if not payload:
                return None

            # 2. 检查黑名单（服务层逻辑）
            token_id = payload.get("jti")
            if token_id and await self._is_token_blacklisted(token_id):
                logger.warning("[TokenService] Token 已被撤销")
                return None

            return payload

        except Exception as e:
            logger.warning(f"[TokenService] Token 验证失败: {e}")
            return None

    async def _is_token_blacklisted(self, token_id: str) -> bool:
        """
        检查 Token 是否在黑名单中（容错降级策略）
        
        策略：
        1. 优先检查Redis（快速路径）
        2. Redis失败时检查数据库
        3. 双重故障时采用安全优先策略（拒绝访问）
        """
        redis_available = True

        # 1. 检查 Redis（快速路径）
        try:
            blacklist_key = f"token:blacklist:{token_id}"
            if await self.cache.exists(blacklist_key):
                return True
        except Exception as e:
            logger.error(f"[TokenService][Critical] Redis查询失败: {e}")
            redis_available = False

        # 2. 检查数据库（持久化数据源）
        try:
            async with await self.db.session() as session:
                query = select(TokenBlacklistTable).where(
                    and_(
                        TokenBlacklistTable.token_id == token_id,
                        TokenBlacklistTable.expires_at > datetime.now(UTC)
                    )
                )
                result = await session.execute(query)
                is_blacklisted = result.scalar_one_or_none() is not None

                # Redis故障时的警告
                if not redis_available and not is_blacklisted:
                    logger.warning(
                        f"[Security] Redis不可用，仅依赖数据库查询。"
                        f"可能存在短暂的黑名单同步延迟。Token ID: {token_id[:8]}..."
                    )

                return is_blacklisted

        except Exception as e:
            logger.critical(f"[TokenService][Critical] 数据库查询失败: {e}")
            # 双重故障：采用安全优先策略（拒绝访问）
            logger.critical(
                "[Security] Redis和数据库同时故障，采用安全优先策略：拒绝Token访问"
            )
            return True  # 故障时拒绝访问（安全优先）

    async def revoke_token(self, token: str, reason: str = "") -> bool:
        """
        撤销 Token（加入黑名单）
        
        职责：
        1. 解码Token（委托Generator）
        2. 黑名单管理（服务层逻辑）
        
        Args:
            token: Token 字符串
            reason: 撤销原因
            
        Returns:
            bool: 是否成功
        """
        try:
            # 1. 解码 Token 获取信息（委托Generator）
            payload = self.token_generator.decode(token)
            if not payload:
                logger.warning("[TokenService] Token已过期，无需撤销")
                return True

            # 2. 验证Token结构
            token_id = payload.get("jti")
            if not token_id:
                logger.error("[Security] Token缺JTI字段，无法精确撤销")
                raise ValueError("Token payload缺少jti字段，无法撤销")
            user_id = payload.get("sub")
            exp_timestamp = payload.get("exp")
            expires_at = datetime.fromtimestamp(float(exp_timestamp), UTC) if exp_timestamp else datetime.now(UTC)

            # 3. 写入黑名单（两级存储 - 服务层逻辑）
            # 3.1 数据库持久化
            async with await self.db.session() as session:
                blacklist_record = TokenBlacklistTable(
                    token_id=token_id,
                    user_id=int(user_id) if user_id else None,
                    token_type="access",
                    reason=reason or RevokeTokenReason.USER_LOGOUT,
                    expires_at=expires_at
                )
                session.add(blacklist_record)
                await session.commit()
                logger.debug(f"[TokenService] Token黑名单已持久化")

            # 3.2 Redis缓存
            try:
                blacklist_key = f"token:blacklist:{token_id}"
                ttl = int((expires_at - datetime.now(UTC)).total_seconds())
                await self.cache.set(blacklist_key, "1", ttl=ttl)
                logger.debug("[TokenService] Token已加入Redis黑名单")
            except Exception as e:
                logger.warning(f"[TokenService] Redis写入失败(数据库已保存): {e}")

            logger.info(f"[TokenService] Token已撤销(两级存储): reason={reason}")
            return True

        except Exception as e:
            logger.error(f"[TokenService] 撤销Token失败: {e}")
            return False

    async def revoke_user_refresh_tokens(
            self,
            session: Any,
            user_id: Any,
            reason: str = ""
    ) -> None:
        """
        撤销用户的所有 Refresh Token
        
        Args:
            session: 数据库会话（暂未使用）
            user_id: 用户ID
            reason: 撤销原因
        """
        try:
            # 1. 查询用户所有活跃的 Refresh Token
            async with await self.db.session() as db_session:
                query = select(RefreshTokenTable).where(
                    and_(
                        RefreshTokenTable.user_id == int(user_id),
                        RefreshTokenTable.is_revoked == False
                    )
                )
                result = await db_session.execute(query)
                active_tokens = result.scalars().all()

                if not active_tokens:
                    logger.debug(f"[TokenService] 用户 {user_id} 没有活跃的 Refresh Token")
                    return

                # 2. 标记为已撤销
                for record in active_tokens:
                    record.is_revoked = True
                    record.revoked_at = datetime.now(UTC)
                    record.revoke_reason = reason or RevokeTokenReason.USER_LOGIN
                    logger.debug(f"[TokenService] Refresh Token已标记为无效: user_id={record.user_id}")

                    # 2.1 加入黑名单（防止已撤销的Token被用于刷新）
                    try:
                        # 从payload获取JTI
                        token_jti = None
                        try:
                            payload = self.token_generator.decode(record.refresh_token)
                            if payload:
                                token_jti = payload.get("jti")
                        except Exception:
                            pass

                        if not token_jti:
                            logger.error(f"[Security] Refresh Token缺JTI字段，数据异常: token_id={record.token_id}")
                            raise ValueError(f"Invalid refresh token: missing JTI (token_id={record.token_id})")

                        # 写入黑名单表
                        blacklist_record = TokenBlacklistTable(
                            token_id=token_jti,
                            user_id=int(user_id),
                            token_type="refresh",
                            reason=reason or RevokeTokenReason.USER_LOGIN,
                            expires_at=record.expires_at
                        )
                        db_session.add(blacklist_record)

                        # Redis黑名单
                        try:
                            blacklist_key = f"token:blacklist:{token_jti}"
                            ttl = int((record.expires_at - datetime.now(UTC)).total_seconds())
                            if ttl > 0:
                                await self.cache.set(blacklist_key, "1", ttl=ttl)
                        except Exception as e:
                            logger.warning(f"[TokenService] Redis黑名单写入失败: {e}")
                    except Exception as e:
                        logger.error(f"[TokenService] 黑名单处理失败: {e}")

                # 3. 从 Redis 删除
                try:
                    for record in active_tokens:
                        refresh_key = f"token:refresh:{user_id}:{record.refresh_token[:16]}"
                        await self.cache.delete(refresh_key)
                    logger.debug("[TokenService] 已从Redis删除Refresh Token")
                except Exception as e:
                    logger.warning(f"[TokenService] Redis删除失败: {e}")

                await db_session.commit()
                logger.info(f"[TokenService] 撤销用户 {user_id} 的 {len(active_tokens)} 个 Refresh Token")

        except Exception as e:
            logger.error(f"[TokenService] 撤销refresh token 失败: {e}")
            raise

    def refresh_access_token(self, refresh_token: str) -> str:
        """
        刷新 Access Token
        
        Args:
            refresh_token: Refresh Token 字符串
            
        Returns:
            str: 新的 Access Token
            
        Raises:
            NotImplementedError: 刷新功能待实现（可通过扩展实现）
        """
        raise NotImplementedError("Refresh token功能需要根据业务需求实现")
