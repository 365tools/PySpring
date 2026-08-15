"""
数据库表结构初始化器

负责在应用启动时自动创建数据库表结构
策略：
1. 优先使用 ORM 模型创建表（Base.metadata.create_all）
2. 可选使用 SQL 脚本补充初始数据
3. 支持表名前缀自定义
"""
import importlib
import sys
from pathlib import Path

from pyspring.core.ioc.context import ApplicationContext
from pyspring.core.ioc.lifecycle.initializer import IStartupInitializer
from pyspring.core.log.instance import logger
from pyspring.repositories.base.config.loader import RepositoriesConfigManager
from pyspring.repositories.db.models.common.define import Base
from pyspring.repositories.db.service import IDBService
from sqlalchemy import text

from ..manager import DBManagerService


class MigrationInitializer(IStartupInitializer):
    """
    数据库表结构初始化器 (Migration)
    
    功能：
    1. 优先使用 ORM 模型自动创建表（Base.metadata.create_all）
    2. 支持框架内置模型 + 用户自定义模型
    3. 支持表名前缀配置（项目名称+表名）
    4. 可选使用 SQL 脚本补充初始数据
    
    策略：
    - 框架内置模型：pyspring.security.orm.tables
    - 用户模型：自动扫描项目的 app/models 或 models 目录
    - 表名前缀：可通过配置自定义（默认无前缀）
    
    注意：
    - 依赖 ConnectionInitializer 先执行完成（需要数据库连接已建立）
    - 自动从 IoC 容器获取 DBManagerService
    - 通过 repositories.yaml 配置控制行为
    """

    def __init__(self, db_manager: DBManagerService, enabled: bool = True):
        """
        Args:
            db_manager: 数据库管理服务实例
            enabled: 是否启用自动初始化
        """
        super().__init__(enabled)
        self.db_manager = db_manager
        self._db_service: (IDBService) | None = None
        self._models_loaded = False

    @property
    def config_manager(self) -> RepositoriesConfigManager:
        return ApplicationContext.get_instance().get_bean(RepositoriesConfigManager)

    def get_name(self) -> str:
        return "MigrationInitializer"

    async def _get_db_service(self):
        """获取数据库服务"""
        if self._db_service is None:
            self._db_service = await self.db_manager.service()
        return self._db_service

    @staticmethod
    def _load_framework_models():
        """加载框架内置的 ORM 模型"""
        try:
            from pyspring.security.orm import tables
            logger.debug(f"✅ 加载框架内置模型: pyspring.security.orm.tables")
            return True
        except Exception as e:
            logger.warning(f"⚠️ 加载框架内置模型失败: {e}")
            return False

    @staticmethod
    def _load_user_models() -> bool:
        """
        加载用户项目的 ORM 模型
        
        搜索 app/models 或 models 目录，自动导入所有 Python 模块
        """
        try:
            project_root = Path.cwd()

            # 可能的模型目录
            possible_dirs = [
                project_root / 'app' / 'models',
                project_root / 'models',
            ]

            models_dir = None
            for dir_path in possible_dirs:
                if dir_path.exists() and dir_path.is_dir():
                    models_dir = dir_path
                    break

            if not models_dir:
                logger.debug("ℹ️ 未找到用户 models 目录，跳过")
                return True

            logger.debug(f"📂 扫描用户模型: {models_dir}")

            # 将项目根目录添加到 sys.path
            if str(project_root) not in sys.path:
                sys.path.insert(0, str(project_root))

            # 导入所有 Python 文件
            loaded_count = 0
            for py_file in models_dir.glob('*.py'):
                if py_file.name.startswith('_'):
                    continue

                try:
                    # 构建模块路径
                    if 'app/models' in str(models_dir) or 'app\\models' in str(models_dir):
                        module_name = f"app.models.{py_file.stem}"
                    else:
                        module_name = f"models.{py_file.stem}"

                    importlib.import_module(module_name)
                    loaded_count += 1
                    logger.debug(f"   ✅ {module_name}")
                except Exception as e:
                    logger.warning(f"   ⚠️ 加载失败 {py_file.name}: {e}")

            if loaded_count > 0:
                logger.debug(f"✅ 加载用户模型: {loaded_count} 个")
            return True

        except Exception as e:
            logger.warning(f"⚠️ 加载用户模型失败: {e}")
            return False

    @staticmethod
    def _apply_table_prefix(prefix: (str) | None):
        """
        为所有表应用前缀

        注意：
        - 直接修改 Table.name 不会同步 Base.metadata.tables 的 dict key 及 ORM __tablename__，
          因此仅适用于"建表阶段"且后续不按旧表名查询的场景。
        - 更稳妥的表名前缀方案是使用 SQLAlchemy 命名约定（metadata 参数），本方法保留作为
          兼容旧配置的辅助手段。

        Args:
            prefix: 表名前缀（如项目名称）
        """
        if not prefix:
            return

        try:
            modified_count = 0
            for table in Base.metadata.tables.values():
                original_name = table.name
                if not original_name.startswith(f"{prefix}_"):
                    table.name = f"{prefix}_{original_name}"
                    modified_count += 1
                    logger.debug(f"   {original_name} → {table.name}")

            if modified_count > 0:
                logger.debug(f"✅ 应用表名前缀: {prefix}_ ({modified_count}个表)")
        except Exception as e:
            logger.warning(f"⚠️ 应用表名前缀失败: {e}")

    @staticmethod
    def _remove_duplicate_base_class_tables():
        """
        移除与用户自定义表冲突的框架表
        
        策略：
        - 检查是否有多个表继承同一个基类（如 BaseUserTable）
        - 保留用户自定义的表，移除框架内置的表
        - 识别规则：pyspring_ 前缀的是框架表
        """
        try:
            from pyspring.repositories.db.models.common.define import (
                BaseUserTable, BaseRoleTable, BasePermissionTable,
                BaseUserRoleTable, BaseRolePermissionTable,
                BaseTokenBlacklistTable, BaseRefreshTokenTable
            )
            from pyspring.security.orm.tables import (
                UserTable, RoleTable, PermissionTable,
                UserRoleTable, RolePermissionTable,
                TokenBlacklistTable, RefreshTokenTable
            )

            # 动态获取框架表名，避免硬编码
            base_class_map = {
                BaseUserTable: UserTable.__tablename__,
                BaseRoleTable: RoleTable.__tablename__,
                BasePermissionTable: PermissionTable.__tablename__,
                BaseUserRoleTable: UserRoleTable.__tablename__,
                BaseRolePermissionTable: RolePermissionTable.__tablename__,
                BaseTokenBlacklistTable: TokenBlacklistTable.__tablename__,
                BaseRefreshTokenTable: RefreshTokenTable.__tablename__,
            }

            # 收集所有表及其基类
            tables_by_base = {}
            for table_name, table in list(Base.metadata.tables.items()):
                # 获取表对应的 ORM 类
                for mapper in Base.registry.mappers:
                    # 检查 mapper.local_table 是否有 name 属性
                    local_table_name = getattr(mapper.local_table, 'name', None)
                    if local_table_name and local_table_name == table.name:
                        orm_class = mapper.class_
                        # 检查继承的基类
                        for base_class, framework_table in base_class_map.items():
                            if issubclass(orm_class, base_class) and orm_class != base_class:
                                if base_class not in tables_by_base:
                                    tables_by_base[base_class] = []
                                tables_by_base[base_class].append((table_name, orm_class))
                        break

            # 处理冲突：如果有多个表继承同一基类，移除框架表
            removed_count = 0
            for base_class, tables in tables_by_base.items():
                if len(tables) > 1:
                    framework_table_name = base_class_map.get(base_class)
                    if framework_table_name and framework_table_name in Base.metadata.tables:
                        # 找到用户自定义的表
                        user_tables = [t for t in tables if not t[0].startswith('pyspring_')]
                        if user_tables:
                            # 移除框架表
                            Base.metadata.remove(Base.metadata.tables[framework_table_name])
                            removed_count += 1
                            logger.debug(f"   🔄 检测到用户自定义表 {user_tables[0][0]}，移除框架默认表 {framework_table_name}")

            if removed_count > 0:
                logger.debug(f"✅ 移除冲突的框架默认表: {removed_count} 个")
            
        except Exception as e:
            logger.debug(f"检查表冲突失败（可忽略）: {e}")

    async def _create_tables_from_orm(self) -> bool:
        """使用 ORM 模型创建数据库表"""
        try:
            # 获取数据库服务（Manager 会自动验证 auto 模式的连接）
            db_service = await self._get_db_service()
            engine = await db_service.engine()

            logger.debug("🔨 创建数据库表（ORM模式）...")

            # 加载模型
            if not self._models_loaded:
                self._load_framework_models()
                self._load_user_models()

                # 移除与用户自定义表冲突的框架表
                MigrationInitializer._remove_duplicate_base_class_tables()

                # 应用表名前缀
                init_config = self.config_manager.get_database_initialization_config()
                table_prefix = init_config.get('table_prefix')
                if table_prefix:
                    MigrationInitializer._apply_table_prefix(table_prefix)

                self._models_loaded = True

            # 显示表列表
            table_names = list(Base.metadata.tables.keys())
            logger.debug(f"📋 发现 {len(table_names)} 个表:")
            for name in sorted(table_names):
                logger.debug(f"   - {name}")

            # 创建所有表（IF NOT EXISTS）
            async with engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)

            logger.debug(f"✅ 数据库表创建完成")
            return True

        except Exception as e:
            logger.error(f"❌ 创建数据库表失败: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return False

    async def _execute_sql_script(self) -> bool:
        """
        可选：执行 SQL 脚本补充初始数据
        
        查找优先级：
        1. 用户项目 scripts/db/init_data.sql
        2. 跳过（SQL 脚本是可选的）
        """
        try:
            project_root = Path.cwd()
            sql_file = project_root / 'scripts' / 'db' / 'init_data.sql'

            if not sql_file.exists():
                logger.debug("ℹ️ 未找到 init_data.sql，跳过")
                return True

            logger.debug(f"📝 执行初始数据脚本: {sql_file}")

            # 读取并执行
            sql_content = sql_file.read_text(encoding='utf-8')
            db_service = await self._get_db_service()
            engine = await db_service.engine()

            async with engine.begin() as conn:
                # 简单分割语句（以分号分隔）
                statements = [s.strip() for s in sql_content.split(';') if s.strip()]

                for stmt in statements:
                    if stmt and not stmt.startswith('--'):
                        await conn.execute(text(stmt))

            logger.debug("✅ 初始数据脚本执行完成")
            return True
            
        except Exception as e:
            logger.warning(f"⚠️ 执行 SQL 脚本失败: {e}")
            return True  # SQL 脚本失败不影响整体初始化

    async def initialize(self) -> bool:
        """
        执行数据库表结构初始化
        
        Returns:
            bool: 初始化是否成功
        """
        init_config = self.config_manager.get_database_initialization_config()

        if not init_config.get('enabled', False):
            logger.debug("⏭️  数据库初始化已禁用")
            return True

        logger.debug("🚀 开始数据库初始化...")

        # 1. 使用 ORM 模型创建表（主要方式）
        orm_success = await self._create_tables_from_orm()
        if not orm_success:
            logger.error("❌ ORM 创建表失败")
            return False

        # 2. 可选执行 SQL 脚本（补充初始数据）
        use_sql_script = init_config.get('use_sql_script', False)
        if use_sql_script:
            await self._execute_sql_script()

        logger.debug("✅ 数据库初始化完成")
        return True
