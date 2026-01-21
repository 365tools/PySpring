"""
数据库表结构初始化器

负责在应用启动时自动创建数据库表结构
注意：必须在 DBInitializer 之后执行（依赖数据库连接已建立）
"""
from pathlib import Path
from typing import Optional

from pyspring.ioc.manager import AppContainerManager
from sqlalchemy import text

from pyspring.core.abstracts.interfaces.initializer.startup import IStartupInitializer
from pyspring.log.instance import logger
from pyspring.repositories.base.config.loader import RepositoriesConfigManager
from pyspring.repositories.db.service import IDBService
from pyspring.utils.config.finder import detect_project_root
from ..manager import DBManagerService


class MigrationInitializer(IStartupInitializer):
    """
    数据库表结构初始化器 (Migration)
    
    功能：
    1. 从 SQL 脚本文件读取 DDL 语句
    2. 在应用启动时自动执行，创建缺失的数据库表
    3. 支持增量模式（只创建不存在的表）和全覆盖模式（重建所有表）
    
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
        # self.config_manager = RepositoriesConfigManager()
        self._db_service: Optional[IDBService] = None

    @property
    def config_manager(self) -> RepositoriesConfigManager:
        return AppContainerManager().get(RepositoriesConfigManager)

    def get_name(self) -> str:
        return "MigrationInitializer"

    async def _get_db_service(self):
        """
        从 IoC 容器获取数据库服务
        
        Returns:
            数据库服务实例
        """
        if self._db_service is None:
            self._db_service = await self.db_manager.service()

        return self._db_service

    def _detect_script_path(self) -> Optional[Path]:
        """
        自动检测 SQL 脚本路径（递归搜索）
        
        搜索策略：
        1. 优先从当前工作目录开始递归搜索
        2. 其次从项目根目录搜索
        3. 查找 scripts/db/ 或 scripts/ 目录下的脚本
        
        Returns:
            找到的脚本路径，未找到则返回 None
        """
        # 从配置获取数据库类型
        db_config = self.config_manager.get_database_config()
        db_type = db_config.get('type', 'sqlite').lower()

        # 如果是 auto，根据实际连接的数据库判断
        if db_type == 'auto':
            if self._db_service and hasattr(self._db_service, 'url'):
                url_str = str(self._db_service.url).lower()
                if 'postgresql' in url_str:
                    db_type = 'postgresql'
                elif 'sqlite' in url_str:
                    db_type = 'sqlite'
                else:
                    db_type = 'sqlite'  # 默认
            else:
                db_type = 'sqlite'

        script_name = f"init_{db_type}.sql"

        # 使用递归搜索查找脚本
        project_root = detect_project_root()
        script_path = self._search_sql_script(script_name, Path.cwd(), max_depth=4)

        # 如果当前目录没找到，从项目根目录搜索
        if not script_path and Path.cwd() != project_root:
            script_path = self._search_sql_script(script_name, project_root, max_depth=4)

        if script_path:
            logger.info(f"🔍 自动检测到 SQL 脚本: {script_path}")
            return script_path

        logger.warning(f"⚠️  未找到数据库初始化脚本: {script_name}")
        logger.info(f"💡 请在以下位置创建脚本: scripts/db/{script_name}")
        return None

    def _search_sql_script(
            self,
            filename: str,
            path: Path,
            max_depth: int,
            current_depth: int = 0
    ) -> Optional[Path]:
        """
        递归搜索 SQL 脚本文件
        
        Args:
            filename: 脚本文件名
            path: 搜索路径
            max_depth: 最大搜索深度
            current_depth: 当前深度
            
        Returns:
            找到的文件路径或 None
        """
        if current_depth > max_depth:
            return None

        # 优先查找 scripts/db/ 目录
        scripts_db_dir = path / 'scripts' / 'db'
        if scripts_db_dir.is_dir():
            script_file = scripts_db_dir / filename
            if script_file.exists():
                return script_file

        # 查找 scripts/ 目录
        scripts_dir = path / 'scripts'
        if scripts_dir.is_dir():
            script_file = scripts_dir / filename
            if script_file.exists():
                return script_file

        # 查找 db/ 目录
        db_dir = path / 'db'
        if db_dir.is_dir():
            script_file = db_dir / filename
            if script_file.exists():
                return script_file

        # 查找当前目录
        script_file = path / filename
        if script_file.exists():
            return script_file

        # 递归搜索子目录
        try:
            for subdir in path.iterdir():
                if not subdir.is_dir():
                    continue

                # 跳过这些目录
                skip_dirs = {
                    '__pycache__', '.git', '.venv', 'venv', 'env',
                    'node_modules', '.idea', '.vscode', 'build', 'dist',
                    '.pytest_cache', '.mypy_cache', '.tox', 'htmlcov',
                    'eggs', '.eggs', '*.egg-info', 'logs', 'data'
                }
                if subdir.name.startswith('.') or subdir.name in skip_dirs:
                    continue

                result = self._search_sql_script(filename, subdir, max_depth, current_depth + 1)
                if result:
                    return result
        except PermissionError:
            pass

        return None

    def _get_script_path(self) -> Optional[Path]:
        """
        获取 SQL 脚本路径
        
        Returns:
            Path: SQL 脚本路径
        """
        # 读取配置
        init_config = self.config_manager.get_database_initialization_config()
        script_path = init_config.get('script_path')
        auto_detect = init_config.get('auto_detect', True)

        # 1. 优先使用配置的路径
        if script_path:
            path = Path(script_path)
            if path.exists():
                logger.debug(f"使用配置的脚本路径: {path}")
                return path
            else:
                logger.warning(f"配置的脚本路径不存在: {path}")

        # 2. 自动检测
        if auto_detect:
            detected_path = self._detect_script_path()
            if detected_path:
                logger.debug(f"自动检测到脚本路径: {detected_path}")
                return detected_path

        return None

    async def _read_sql_script(self, script_path: Path) -> Optional[str]:
        """
        读取 SQL 脚本文件
        
        Args:
            script_path: 脚本文件路径
            
        Returns:
            str: SQL 脚本内容
        """
        try:
            content = script_path.read_text(encoding='utf-8')
            logger.debug(f"读取脚本文件成功: {script_path} ({len(content)} 字符)")
            return content
        except Exception as e:
            logger.error(f"读取脚本文件失败: {e}")
            return None

    def _split_sql_statements(self, sql_content: str) -> list[str]:
        """
        分割 SQL 语句（支持多行语句）
        
        Args:
            sql_content: SQL 脚本内容
            
        Returns:
            list[str]: SQL 语句列表
        """
        statements = []
        current_statement = []

        for line in sql_content.split('\n'):
            # 移除首尾空白
            line = line.strip()

            # 跳过空行
            if not line:
                continue

            # 跳过纯注释行
            if line.startswith('--'):
                continue

            # 移除行内注释
            if '--' in line:
                line = line.split('--')[0].strip()
                if not line:
                    continue

            # 添加到当前语句
            current_statement.append(line)

            # 以分号结尾表示语句结束
            if line.endswith(';'):
                stmt = ' '.join(current_statement)
                # 移除分号
                stmt = stmt.rstrip(';').strip()
                if stmt:
                    statements.append(stmt)
                current_statement = []

        # 处理最后一条未结束的语句
        if current_statement:
            stmt = ' '.join(current_statement).strip()
            if stmt:
                statements.append(stmt)

        return statements

    async def _execute_sql_script(self, sql_content: str) -> bool:
        """
        执行 SQL 脚本
        
        Args:
            sql_content: SQL 脚本内容
            
        Returns:
            bool: 是否执行成功
        """
        try:
            # 获取数据库服务和模式
            db_service = await self._get_db_service()
            init_config = self.config_manager.get_database_initialization_config()
            mode = init_config.get('mode', 'incremental')

            # 分割 SQL 语句
            statements = self._split_sql_statements(sql_content)
            logger.info(f"解析到 {len(statements)} 条 SQL 语句")

            # 获取数据库引擎
            engine = await db_service.engine()

            executed_count = 0
            skipped_count = 0

            async with engine.begin() as conn:
                for idx, stmt in enumerate(statements, 1):
                    stmt_stripped = stmt.strip()
                    if not stmt_stripped:
                        continue

                    # 判断语句类型
                    stmt_upper = stmt_stripped.upper()
                    is_ddl = any(stmt_upper.startswith(prefix) for prefix in ['CREATE', 'DROP', 'ALTER'])
                    is_dml = any(stmt_upper.startswith(prefix) for prefix in ['INSERT', 'UPDATE', 'DELETE'])

                    # 增量模式：只对DDL语句检查是否需要跳过
                    if mode == "incremental" and is_ddl:
                        # 提取表名
                        table_name = self._extract_table_name(stmt_stripped)

                        if table_name:
                            # 检查表是否已存在
                            exists = await self._table_exists(conn, table_name, db_service)

                            if exists:
                                logger.debug(f"⏭️  跳过已存在的表: {table_name}")
                                skipped_count += 1
                                continue

                    # 执行语句
                    try:
                        logger.debug(f"📝 执行第 {idx} 条语句: {stmt_stripped[:80]}...")
                        result = await conn.execute(text(stmt_stripped))
                        executed_count += 1

                        # 对于DML语句，显示影响的行数
                        if is_dml:
                            rowcount = getattr(result, 'rowcount', -1)
                            if rowcount == 0:
                                logger.warning(f"⚠️  执行成功但未影响任何行（可能缺少必填字段或违反约束）")
                            else:
                                logger.debug(f"✅ 执行成功，影响 {rowcount} 行")
                        else:
                            logger.debug(f"✅ 执行成功")
                    except Exception as e:
                        # 增量模式下，如果是"表已存在"错误，可以忽略
                        if mode == "incremental" and ("already exists" in str(e).lower() or
                                                      "already exist" in str(e).lower()):
                            logger.debug(f"⏭️  表已存在，跳过")
                            skipped_count += 1
                        else:
                            logger.error(f"❌ 执行失败 (第 {idx} 条): {stmt_stripped[:100]}...")
                            logger.error(f"   错误信息: {e}")
                            if mode == "full":
                                # 全覆盖模式下，遇到错误直接失败
                                raise

            logger.info(f"SQL 执行完成: 执行 {executed_count} 条, 跳过 {skipped_count} 条")
            return True

        except Exception as e:
            logger.error(f"执行 SQL 脚本失败: {e}", exc_info=True)
            return False

    async def _table_exists(self, conn, table_name: str, db_service) -> bool:
        """
        检查表是否存在
        
        Args:
            conn: 数据库连接
            table_name: 表名
            db_service: 数据库服务
            
        Returns:
            bool: 表是否存在
        """
        try:
            # 根据数据库类型使用不同的查询
            url_str = str(db_service.url).lower()

            if 'postgresql' in url_str:
                # PostgreSQL
                result = await conn.execute(text(
                    f"SELECT EXISTS (SELECT FROM pg_tables WHERE tablename = '{table_name}')"
                ))
                return result.scalar()
            else:
                # SQLite
                result = await conn.execute(text(
                    f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table_name}'"
                ))
                return result.first() is not None
        except Exception as e:
            logger.warning(f"检查表存在性失败: {e}")
            return False

    def _extract_table_name(self, create_statement: str) -> Optional[str]:
        """
        从 CREATE TABLE 语句中提取表名
        
        Args:
            create_statement: CREATE TABLE 语句
            
        Returns:
            str: 表名
        """
        try:
            # 简单的表名提取逻辑
            statement = create_statement.upper()
            if "CREATE TABLE" in statement:
                parts = statement.split("CREATE TABLE")[1].split("(")[0].strip()
                parts = parts.replace("IF NOT EXISTS", "").strip()
                return parts.strip('"').strip("'").strip()
        except Exception:
            pass
        return None

    async def initialize(self) -> bool:
        """
        执行数据库表结构初始化
        
        Returns:
            bool: 初始化是否成功
        """
        # 读取配置
        init_config = self.config_manager.get_database_initialization_config()

        if not init_config.get('enabled', False):
            logger.info("⏭️  数据库表初始化已禁用")
            return True

        mode = init_config.get('mode', 'incremental')
        logger.info(f"🗄️  开始数据库表结构初始化 (模式: {mode})")

        # 获取数据库服务
        try:
            db_service = await self._get_db_service()

            # 输出数据库连接信息用于调试
            if hasattr(db_service, 'url'):
                logger.debug(f"📍 当前数据库连接: {db_service.url}")
            if hasattr(db_service, 'database'):
                logger.info(f"📁 数据库文件位置: {db_service.database}")
        except Exception as e:
            logger.error(f"❌ 获取数据库服务失败: {e}")
            return False

        # 获取脚本路径
        script_path = self._get_script_path()
        if not script_path:
            logger.warning("⚠️  未配置或未找到 SQL 脚本，跳过初始化")
            return True

        # 读取 SQL 脚本
        sql_content = await self._read_sql_script(script_path)
        if not sql_content:
            return False

        # 执行 SQL 脚本
        result = await self._execute_sql_script(sql_content)

        if result:
            logger.info(f"✅ 数据库表结构初始化完成")
        else:
            logger.error(f"❌ 数据库表结构初始化失败")

        return result
