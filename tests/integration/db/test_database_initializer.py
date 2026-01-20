"""
测试数据库自动初始化功能
"""
import asyncio
import sys
import tempfile
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from pyspring.core.abstracts.interfaces.initializer.startup import StartupInitializerManager
from pyspring.log.instance import logger
from pyspring.repositories.db.initializer.migration import MigrationInitializer
from pyspring.repositories.db.providers.sqlite.services.service import SqliteService


@pytest.mark.asyncio
async def test_database_initializer():
    """测试数据库初始化器"""

    # 创建临时数据库
    temp_db = Path(tempfile.mkdtemp()) / "test.db"
    logger.info(f"测试数据库: {temp_db}")

    # 创建临时 SQL 脚本
    script_dir = temp_db.parent / "scripts" / "db"
    script_dir.mkdir(parents=True, exist_ok=True)

    sql_script = script_dir / "init_sqlite.sql"
    sql_content = """
                  -- 测试数据库初始化脚本

                  CREATE TABLE IF NOT EXISTS users
                  (
                      id
                      INTEGER
                      PRIMARY
                      KEY
                      AUTOINCREMENT,
                      email
                      VARCHAR
                  (
                      255
                  ) UNIQUE NOT NULL,
                      name VARCHAR
                  (
                      100
                  ) NOT NULL,
                      created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                      );

                  CREATE TABLE IF NOT EXISTS roles
                  (
                      id
                      INTEGER
                      PRIMARY
                      KEY
                      AUTOINCREMENT,
                      code
                      VARCHAR
                  (
                      50
                  ) UNIQUE NOT NULL,
                      name VARCHAR
                  (
                      100
                  ) NOT NULL
                      );

-- 初始化数据
                  INSERT
                  OR IGNORE INTO roles (code, name) VALUES
    ('admin', '管理员'),
    ('user', '普通用户'); \
                  """
    sql_script.write_text(sql_content, encoding='utf-8')
    logger.info(f"SQL 脚本: {sql_script}")

    # 创建 SQLite 服务
    db_service = SqliteService(database=str(temp_db))

    print("\n" + "=" * 80)
    print("测试 1: 增量模式（第一次执行）")
    print("=" * 80)

    # 创建初始化器管理器
    manager = StartupInitializerManager()

    # Mock DBManagerService
    from unittest.mock import MagicMock
    from pyspring.repositories.db.manager import DBManagerService
    mock_db_manager = MagicMock(spec=DBManagerService)

    # Make await db_manager.service() return db_service
    async def get_service():
        return db_service

    mock_db_manager.service.side_effect = get_service

    # 注册数据库初始化器
    db_initializer = MigrationInitializer(db_manager=mock_db_manager, enabled=True)

    # Mock config_manager
    db_initializer.config_manager = MagicMock()
    db_initializer.config_manager.get_database_initialization_config.return_value = {
        'enabled': True,
        'mode': 'incremental',
        'script_path': str(sql_script),
        'auto_detect': False
    }

    manager.register(db_initializer)

    # 执行初始化
    # 切换到脚本目录以便自动检测工作
    import os
    original_cwd = os.getcwd()
    os.chdir(temp_db.parent)

    try:
        success = await manager.execute_all()
        logger.info(f"初始化结果: {'成功' if success else '失败'}")
    finally:
        os.chdir(original_cwd)

    # 验证表是否创建
    engine = await db_service.get_engine()
    async with engine.connect() as conn:
        from sqlalchemy import text
        result = await conn.execute(text("SELECT name FROM sqlite_master WHERE type='table'"))
        tables = [row[0] for row in result]
        logger.info(f"创建的表: {tables}")

        # 查询角色数据
        result = await conn.execute(text("SELECT code, name FROM roles"))
        roles = [dict(row._mapping) for row in result]
        logger.info(f"角色数据: {roles}")

    print("\n" + "=" * 80)
    print("测试 2: 增量模式（第二次执行，应跳过已存在的表）")
    print("=" * 80)

    # 重新执行，应该跳过
    manager2 = StartupInitializerManager()
    db_initializer2 = MigrationInitializer(db_manager=mock_db_manager, enabled=True)
    db_initializer2.config_manager = MagicMock()
    db_initializer2.config_manager.get_database_initialization_config.return_value = {
        'enabled': True,
        'mode': 'incremental',
        'script_path': str(sql_script),
        'auto_detect': False
    }

    manager2.register(db_initializer2)

    success2 = await manager2.execute_all()
    logger.info(f"第二次初始化结果: {'成功' if success2 else '失败'}")

    # 清理
    await db_service.close()

    print("\n" + "=" * 80)
    print("✅ 测试完成！")
    print("=" * 80)
    logger.info(f"测试数据库: {temp_db}")
    logger.info(f"SQL 脚本: {sql_script}")


if __name__ == "__main__":
    asyncio.run(test_database_initializer())
