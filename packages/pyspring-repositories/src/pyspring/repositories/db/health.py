"""
数据库健康检查服务
提供详细的数据库连接健康状况监控
"""
from typing import Any
from datetime import datetime, timedelta

from pyspring.core.ioc.annotations.component import Component
from pyspring.core.ioc.annotations.scope import Singleton
from pyspring.core.log.instance import logger

from .factory import DBServiceFactory
from .service import IDBService


@Component
@Singleton
class DatabaseHealthChecker:
    """数据库健康检查服务"""
    
    def __init__(self, db_factory: DBServiceFactory):
        self.db_factory = db_factory
        self._last_check_time = None
        self._last_status = None
        self._last_error = None
        self._checks_history = []
    
    async def check_health(self) -> dict[str, Any]:
        """
        检查数据库健康状况
        
        Returns:
            Dict: 包含健康状态信息的字典
        """
        start_time = datetime.now()
        
        try:
            # 获取数据库服务
            db_service: IDBService = await self.db_factory.get_service()
            
            # 执行健康检查
            is_healthy = await db_service.ping()
            
            # 记录检查时间
            check_duration = (datetime.now() - start_time).total_seconds()
            
            health_info = {
                "status": "healthy" if is_healthy else "unhealthy",
                "database_type": self.db_factory._service_type or "unknown",
                "check_duration": check_duration,
                "timestamp": datetime.now().isoformat(),
                "error": None
            }
            
            if not is_healthy:
                health_info["error"] = "Ping test failed"
            
            # 更新内部状态
            self._last_check_time = datetime.now()
            self._last_status = is_healthy
            self._last_error = health_info["error"]
            
            # 记录历史
            self._checks_history.append(health_info)
            if len(self._checks_history) > 100:  # 只保留最近100次检查
                self._checks_history.pop(0)
            
            logger.info(f"[DatabaseHealth] Status: {health_info['status']}, Duration: {check_duration:.3f}s")
            return health_info
            
        except Exception as e:
            error_time = datetime.now()
            check_duration = (error_time - start_time).total_seconds()
            
            health_info = {
                "status": "unhealthy",
                "database_type": self.db_factory._service_type or "unknown",
                "check_duration": check_duration,
                "timestamp": error_time.isoformat(),
                "error": str(e)
            }
            
            # 更新内部状态
            self._last_check_time = error_time
            self._last_status = False
            self._last_error = str(e)
            
            logger.error(f"[DatabaseHealth] Error: {e}, Duration: {check_duration:.3f}s")
            return health_info
    
    def get_health_stats(self) -> dict[str, Any]:
        """
        获取健康统计信息
        
        Returns:
            Dict: 健康统计信息
        """
        if not self._checks_history:
            return {"message": "No health checks performed yet"}
        
        recent_checks = self._checks_history[-10:]  # 最近10次检查
        healthy_count = sum(1 for check in recent_checks if check["status"] == "healthy")
        total_checks = len(recent_checks)
        
        avg_duration = sum(check["check_duration"] for check in recent_checks) / total_checks
        
        return {
            "total_checks": len(self._checks_history),
            "recent_healthy_ratio": f"{healthy_count}/{total_checks}",
            "average_response_time": f"{avg_duration:.3f}s",
            "last_check_time": self._last_check_time.isoformat() if self._last_check_time else None,
            "current_status": "healthy" if self._last_status else "unhealthy",
            "last_error": self._last_error
        }
    
    async def get_connection_pool_info(self) -> dict[str, Any]:
        """
        获取连接池信息（如果支持）
        
        Returns:
            Dict: 连接池信息
        """
        try:
            db_service = await self.db_factory.get_service()
            pool_info_method = getattr(db_service, 'get_pool_info', None)
            if pool_info_method is not None:
                return await pool_info_method()
            else:
                return {"message": "Connection pool info not available for this database type"}
        except Exception as e:
            logger.error(f"[DatabaseHealth] Failed to get pool info: {e}")
            return {"error": str(e)}