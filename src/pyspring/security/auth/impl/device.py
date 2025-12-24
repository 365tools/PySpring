"""
设备认证服务

负责设备指纹的验证、注册、审批管理
"""
from datetime import datetime, timedelta, UTC
from fastapi import HTTPException, status
from pyspring.interfaces.ISingleton import ISingletonService
from pyspring.log.loguru.ins import logger
from pyspring.repositories.db.manager import DBManagerService
from pyspring.security.auth.models.rabc.orm.tables import UserDeviceTable, UserTable
from pyspring.security.auth.models.rabc.schema.requests import UserDevice
from sqlalchemy import select, and_
from typing import Optional, Dict, Any


class DeviceAuthService(ISingletonService):
    """
    设备认证服务
    
    功能:
    1. 验证设备指纹是否已注册
    2. 注册新设备(待审批状态)
    3. 检查设备权限是否有效
    4. 审批/撤销设备权限
    """

    def __init__(self, db: DBManagerService):
        """
        初始化设备认证服务
        
        Args:
            db: 数据库管理服务
        """
        self.db = db
        logger.info("🔧 DeviceAuthService 初始化完成")

    async def verify_device(self, user_id: int, device_fingerprint: str) -> Dict[str, Any]:
        """
        验证设备指纹是否有权限访问
        
        Args:
            user_id: 用户数据库ID
            device_fingerprint: 设备指纹
            
        Returns:
            验证结果:
            {
                "is_authorized": bool,  # 是否已授权
                "is_expired": bool,     # 是否已过期
                "device": UserDevice,   # 设备信息(如果存在)
                "status": str           # "approved", "pending", "expired", "not_found"
            }
        """
        try:
            async with await self.db.get_session() as session:
                stmt = select(UserDeviceTable).where(
                    and_(
                        UserDeviceTable.user_id == user_id,
                        UserDeviceTable.fingerprint == device_fingerprint,
                        UserDeviceTable.status == True
                    )
                )
                result = await session.execute(stmt)
                db_device = result.scalar_one_or_none()

                # 设备不存在
                if not db_device:
                    return {
                        "is_authorized": False,
                        "is_expired": False,
                        "device": None,
                        "status": "not_found"
                    }

                # 设备存在但未审批
                if not db_device.approved:
                    device = UserDevice.model_validate(db_device)
                    return {
                        "is_authorized": False,
                        "is_expired": False,
                        "device": device,
                        "status": "pending"
                    }

                # 检查是否过期
                now = datetime.now(UTC)
                if db_device.expires_at and db_device.expires_at < now:
                    device = UserDevice.model_validate(db_device)
                    return {
                        "is_authorized": False,
                        "is_expired": True,
                        "device": device,
                        "status": "expired"
                    }

                # 设备已授权且未过期
                device = UserDevice.model_validate(db_device)
                return {
                    "is_authorized": True,
                    "is_expired": False,
                    "device": device,
                    "status": "approved"
                }

        except Exception as e:
            logger.error(f"🚨 验证设备失败: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"验证设备失败: {str(e)}"
            )

    async def register_device(
            self,
            user_id: int,
            device_fingerprint: str,
            device_name: str,
            requested_duration_days: int = 7,
            auto_approve: bool = False
    ) -> UserDevice:
        """
        注册新设备
        
        Args:
            user_id: 用户数据库ID
            device_fingerprint: 设备指纹
            device_name: 设备名称
            requested_duration_days: 申请访问时长（天）
            auto_approve: 是否自动审批（默认False，需要管理员审批）
            
        Returns:
            注册的设备信息
        """
        try:
            async with await self.db.get_session() as session:
                # 检查设备是否已存在
                stmt = select(UserDeviceTable).where(
                    and_(
                        UserDeviceTable.user_id == user_id,
                        UserDeviceTable.fingerprint == device_fingerprint
                    )
                )
                result = await session.execute(stmt)
                existing_device = result.scalar_one_or_none()

                if existing_device:
                    # 设备已存在, 更新申请时长
                    existing_device.requested_duration_days = requested_duration_days
                    existing_device.name = device_name  # 更新设备名称

                    if auto_approve:
                        existing_device.approved = True
                        existing_device.approved_at = datetime.now(UTC)
                        existing_device.expires_at = datetime.now(UTC) + timedelta(days=requested_duration_days)

                    await session.commit()
                    await session.refresh(existing_device)

                    logger.info(f"✅ 设备已更新: {device_name} (用户ID: {user_id})")
                    return UserDevice.model_validate(existing_device)

                # 创建新设备
                new_device = UserDeviceTable(
                    user_id=user_id,
                    name=device_name,
                    fingerprint=device_fingerprint,
                    status=True,
                    approved=auto_approve,
                    requested_duration_days=requested_duration_days
                )

                if auto_approve:
                    new_device.approved_at = datetime.now(UTC)
                    new_device.expires_at = datetime.now(UTC) + timedelta(days=requested_duration_days)

                session.add(new_device)
                await session.commit()
                await session.refresh(new_device)

                logger.info(f"✅ 设备已注册: {device_name} (用户ID: {user_id}), 状态: {'已审批' if auto_approve else '待审批'}")
                return UserDevice.model_validate(new_device)

        except Exception as e:
            logger.error(f"🚨 注册设备失败: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"注册设备失败: {str(e)}"
            )

    async def approve_device(self, device_id: int, duration_days: Optional[int] = None) -> UserDevice:
        """
        审批设备访问权限
        
        Args:
            device_id: 设备数据库ID
            duration_days: 授权时长(天), 如果不提供则使用申请时长
            
        Returns:
            更新后的设备信息
        """
        try:
            async with await self.db.get_session() as session:
                stmt = select(UserDeviceTable).where(UserDeviceTable.id == device_id)
                result = await session.execute(stmt)
                db_device = result.scalar_one_or_none()

                if not db_device:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail="设备不存在"
                    )

                # 使用指定时长或申请时长
                actual_duration = duration_days if duration_days else db_device.requested_duration_days

                # 审批设备
                db_device.approved = True
                db_device.approved_at = datetime.now(UTC)
                db_device.expires_at = datetime.now(UTC) + timedelta(days=actual_duration)
                db_device.status = True

                await session.commit()
                await session.refresh(db_device)

                logger.info(f"✅ 设备已审批: {db_device.name} (ID: {device_id}), 有效期: {actual_duration}天")
                return UserDevice.model_validate(db_device)

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"🚨 审批设备失败: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"审批设备失败: {str(e)}"
            )

    async def revoke_device(self, device_id: int) -> bool:
        """
        撤销设备访问权限
        
        Args:
            device_id: 设备数据库ID
            
        Returns:
            是否撤销成功
        """
        try:
            async with await self.db.get_session() as session:
                stmt = select(UserDeviceTable).where(UserDeviceTable.id == device_id)
                result = await session.execute(stmt)
                db_device = result.scalar_one_or_none()

                if not db_device:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail="设备不存在"
                    )

                # 撤销权限
                db_device.status = False
                db_device.approved = False

                await session.commit()

                logger.info(f"✅ 设备权限已撤销: {db_device.name} (ID: {device_id})")
                return True

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"🚨 撤销设备失败: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"撤销设备失败: {str(e)}"
            )

    async def get_user_devices(self, user_id: int, include_inactive: bool = False) -> list[UserDevice]:
        """
        获取用户的所有设备
        
        Args:
            user_id: 用户数据库ID
            include_inactive: 是否包含已禁用的设备
            
        Returns:
            设备列表
        """
        try:
            async with await self.db.get_session() as session:
                if include_inactive:
                    stmt = select(UserDeviceTable).where(UserDeviceTable.user_id == user_id)
                else:
                    stmt = select(UserDeviceTable).where(
                        and_(
                            UserDeviceTable.user_id == user_id,
                            UserDeviceTable.status == True
                        )
                    )

                result = await session.execute(stmt)
                devices = result.scalars().all()

                return [UserDevice.model_validate(device) for device in devices]

        except Exception as e:
            logger.error(f"🚨 获取用户设备失败: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"获取用户设备失败: {str(e)}"
            )

    async def get_pending_devices(self, limit: int = 50) -> list[Dict[str, Any]]:
        """
        获取待审批的设备列表
        
        Args:
            limit: 返回数量限制
            
        Returns:
            待审批设备列表(包含用户信息)
        """
        try:
            async with await self.db.get_session() as session:
                stmt = select(UserDeviceTable, UserTable).join(
                    UserTable, UserDeviceTable.user_id == UserTable.id
                ).where(
                    and_(
                        UserDeviceTable.approved == False,
                        UserDeviceTable.status == True
                    )
                ).limit(limit)

                result = await session.execute(stmt)
                rows = result.all()

                pending_devices = []
                for device_record, user_record in rows:
                    device = UserDevice.model_validate(device_record)
                    pending_devices.append({
                        "device": device,
                        "user_email": user_record.email,
                        "user_id": user_record.user_id,
                        "requested_at": device_record.created_at.isoformat() if device_record.created_at else None
                    })

                return pending_devices

        except Exception as e:
            logger.error(f"🚨 获取待审批设备失败: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"获取待审批设备失败: {str(e)}"
            )
