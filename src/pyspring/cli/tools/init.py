"""
PySpring 框架初始化工具

提供命令行工具帮助用户快速创建配置文件
"""
import shutil
import sys
from pathlib import Path
from typing import Optional

# Import UI utilities from core
from pyspring.cli.core.ui import (
    Colors, print_header, print_success, print_info,
    print_warning, print_error
)


def get_template_dir() -> Path:
    """获取模板目录"""
    # 从 cli/tools/init.py 向上到 pyspring/templates
    # __file__ -> cli/tools/init.py
    # parent -> cli/tools/
    # parent.parent -> cli/
    # parent.parent.parent -> pyspring/
    return Path(__file__).parent.parent.parent / "templates"


def get_config_files_from_templates(minimal: bool = False) -> list[tuple[str, str]]:
    """
    从模板目录自动扫描配置文件
    
    Args:
        minimal: 是否只返回最小必需配置
    
    Returns:
        配置文件列表 [(filename, description), ...]
        
    Raises:
        FileNotFoundError: 模板目录不存在或缺少必需的配置文件
    """
    template_config_dir = get_template_dir() / "config"
    if not template_config_dir.exists():
        raise FileNotFoundError(f"模板配置目录不存在: {template_config_dir}")

    config_descriptions = {
        "container.yaml": "IoC 容器配置",
        "logging.yaml": "日志配置",
        "repositories.yaml": "数据库与缓存配置",
        "security.yaml": "认证与授权配置",
    }

    # 必需的配置文件
    required_configs = ["security.yaml"]
    if not minimal:
        required_configs.extend(["logging.yaml", "repositories.yaml"])

    # 扫描所有 .yaml 文件
    config_files = []
    found_files = set()

    for yaml_file in sorted(template_config_dir.glob("*.yaml")):
        filename = yaml_file.name
        found_files.add(filename)
        description = config_descriptions.get(filename, f"{filename} 配置")
        config_files.append((filename, description))

    # 检查必需的配置文件是否存在
    missing_configs = [cfg for cfg in required_configs if cfg not in found_files]
    if missing_configs:
        raise FileNotFoundError(
            f"缺少必需的配置文件模板: {', '.join(missing_configs)}\n"
            f"请检查模板目录: {template_config_dir}"
        )

    # 如果是最小化模式，只返回必需的配置
    if minimal:
        config_files = [(f, d) for f, d in config_files if f in required_configs]

    return config_files


def create_config_file(target_path: Path, template_name: str, force: bool = False, template_subdir: str = "config") -> bool:
    """
    创建配置文件
    
    Args:
        target_path: 目标文件路径
        template_name: 模板文件名
        force: 是否强制覆盖
        template_subdir: 模板子目录（config, app, project）
        
    Returns:
        是否成功创建
    """
    if target_path.exists() and not force:
        print_warning(f"文件已存在，跳过: {target_path}")
        return False

    template_dir = get_template_dir() / template_subdir
    template_path = template_dir / template_name

    if not template_path.exists():
        print_error(f"模板文件不存在: {template_subdir}/{template_name}")
        return False

    # 确保目标目录存在
    target_path.parent.mkdir(parents=True, exist_ok=True)

    # 复制文件
    shutil.copy2(template_path, target_path)
    print_success(f"已创建: {target_path}")
    return True


def generate_jwt_secret() -> str:
    """生成 JWT 密钥"""
    import secrets
    return secrets.token_urlsafe(32)


def generate_encryption_key() -> str:
    """生成 JWT 加密密钥"""
    try:
        from cryptography.fernet import Fernet
        return Fernet.generate_key().decode('utf-8')
    except ImportError:
        print_warning("cryptography 库未安装，跳过加密密钥生成")
        return ""


def create_env_file(target_dir: Path, jwt_secret: str, encryption_key: str, force: bool = False):
    """创建 .env 文件"""
    env_path = target_dir / ".env.example"

    content = f"""# PySpring 框架环境变量配置
# 复制此文件为 .env 并修改相应的值

# ==================== JWT 配置 ====================
# JWT 签名密钥（必须设置，用于 Token 签名）
JWT_SECRET_KEY={jwt_secret}

# JWT 算法（可选，默认 HS256）
# JWT_ALGORITHM=HS256

# Access Token 过期时间（秒，可选）
# ACCESS_TOKEN_EXPIRE=3600

# Refresh Token 过期时间（秒，可选）
# REFRESH_TOKEN_EXPIRE=2592000

# ==================== JWT 加密配置 ====================
# 是否启用 JWT 加密（可选，默认 false）
# JWT_ENCRYPTION_ENABLED=true

# JWT 加密密钥（启用加密时必须设置）
{"JWT_ENCRYPTION_KEY=" + encryption_key if encryption_key else "# JWT_ENCRYPTION_KEY=your-encryption-key"}

# ==================== 数据库配置 ====================
# PostgreSQL 配置
# POSTGRES_HOST=localhost
# POSTGRES_PORT=5432
# POSTGRES_USER=postgres
# POSTGRES_PASSWORD=your-password
# POSTGRES_DB=your-database

# MySQL 配置
# MYSQL_HOST=localhost
# MYSQL_PORT=3306
# MYSQL_USER=root
# MYSQL_PASSWORD=your-password
# MYSQL_DB=your-database

# ==================== Redis 配置 ====================
# Redis 主机
# REDIS_HOST=localhost
# REDIS_PORT=6379
# REDIS_PASSWORD=your-password
# REDIS_DB=0

# ==================== 应用配置 ====================
# 应用环境（development, testing, production）
# APP_ENV=development

# 日志级别（DEBUG, INFO, WARNING, ERROR）
# LOG_LEVEL=INFO
"""

    env_path.write_text(content, encoding='utf-8')
    print_success(f"已创建: {env_path}")

    # 同时创建 .env 文件
    env_real_path = target_dir / ".env"
    if not env_real_path.exists() or force:
        shutil.copy2(env_path, env_real_path)
        print_success(f"已创建: {env_real_path}")


def create_database_scripts(target_dir: Path):
    """创建数据库初始化脚本（从 ORM 模型生成）"""
    db_dir = target_dir / "scripts" / "db"
    db_dir.mkdir(parents=True, exist_ok=True)
    print_success(f"已创建目录: {db_dir}")

    try:
        # 尝试从 SQLAlchemy 模型生成 SQL 脚本
        from pyspring.security.authorization.rabc.orm.tables import (
            UserTable, RoleTable, PermissionTable, UserRoleTable,
            RolePermissionTable
        )
        from pyspring.security.authorization.rabc.orm.token_tables import (
            RefreshTokenTable, TokenBlacklistTable
        )
        from pyspring.repositories.db.models.common.define import Base
        from sqlalchemy import create_engine, MetaData
        from sqlalchemy.schema import CreateTable

        print_info("从 ORM 模型生成数据库脚本...")

        # PostgreSQL 脚本生成
        pg_engine = create_engine('postgresql://localhost/dummy', strategy='mock', executor=lambda sql, *_: None)
        pg_scripts = []

        for table in [UserTable, RoleTable, PermissionTable, UserRoleTable,
                      RolePermissionTable, RefreshTokenTable, TokenBlacklistTable]:
            create_table = CreateTable(table.__table__, if_not_exists=True)
            pg_scripts.append(str(create_table.compile(dialect=pg_engine.dialect)) + ';')

        # SQLite 脚本生成
        sqlite_engine = create_engine('sqlite:///dummy.db', strategy='mock', executor=lambda sql, *_: None)
        sqlite_scripts = []

        for table in [UserTable, RoleTable, PermissionTable, UserRoleTable,
                      RolePermissionTable, RefreshTokenTable, TokenBlacklistTable]:
            create_table = CreateTable(table.__table__, if_not_exists=True)
            sqlite_scripts.append(str(create_table.compile(dialect=sqlite_engine.dialect)) + ';')

        print_success("已从 ORM 模型生成 SQL 脚本")

    except ImportError as e:
        print_warning(f"无法导入 ORM 模型，使用默认脚本: {e}")
        # 如果导入失败，使用默认脚本
        pg_scripts = []
        sqlite_scripts = []

    # PostgreSQL 完整脚本
    pg_init_script = """-- PySpring 框架数据库初始化脚本 (PostgreSQL)
-- 自动生成于: {date}
-- 基于 PySpring ORM 模型定义

-- ==================== 表结构 ====================
{table_definitions}

-- ==================== 初始化数据 ====================
-- 插入默认角色
INSERT INTO role (code, name, description, status, active, deleted, creator, created_time, modifier, modified_time) VALUES
    ('admin', '管理员', '系统管理员，拥有所有权限', TRUE, TRUE, FALSE, 'system', CURRENT_TIMESTAMP, 'system', CURRENT_TIMESTAMP),
    ('user', '普通用户', '普通用户角色', TRUE, TRUE, FALSE, 'system', CURRENT_TIMESTAMP, 'system', CURRENT_TIMESTAMP)
ON CONFLICT (code) DO NOTHING;

-- 插入默认权限
INSERT INTO permission (code, name, description, status, active, deleted, creator, created_time, modifier, modified_time) VALUES
    ('user:read', '查看用户', '查看用户信息', TRUE, TRUE, FALSE, 'system', CURRENT_TIMESTAMP, 'system', CURRENT_TIMESTAMP),
    ('user:write', '编辑用户', '创建和编辑用户', TRUE, TRUE, FALSE, 'system', CURRENT_TIMESTAMP, 'system', CURRENT_TIMESTAMP),
    ('user:delete', '删除用户', '删除用户', TRUE, TRUE, FALSE, 'system', CURRENT_TIMESTAMP, 'system', CURRENT_TIMESTAMP),
    ('role:read', '查看角色', '查看角色信息', TRUE, TRUE, FALSE, 'system', CURRENT_TIMESTAMP, 'system', CURRENT_TIMESTAMP),
    ('role:write', '编辑角色', '创建和编辑角色', TRUE, TRUE, FALSE, 'system', CURRENT_TIMESTAMP, 'system', CURRENT_TIMESTAMP),
    ('role:delete', '删除角色', '删除角色', TRUE, TRUE, FALSE, 'system', CURRENT_TIMESTAMP, 'system', CURRENT_TIMESTAMP)
ON CONFLICT (code) DO NOTHING;

-- 为管理员角色分配所有权限
INSERT INTO role_permission (role_code, permission_code, active, deleted, creator, created_time, modifier, modified_time)
SELECT r.code, p.code, TRUE, FALSE, 'system', CURRENT_TIMESTAMP, 'system', CURRENT_TIMESTAMP
FROM role r, permission p
WHERE r.code = 'admin'
ON CONFLICT DO NOTHING;

-- 完成
SELECT '✅ 数据库初始化完成' AS status;
"""

    # SQLite 完整脚本
    sqlite_init_script = """-- PySpring 框架数据库初始化脚本 (SQLite)
-- 自动生成于: {date}
-- 基于 PySpring ORM 模型定义

-- ==================== 表结构 ====================
{table_definitions}

-- ==================== 初始化数据 ====================
-- 插入默认角色
INSERT OR IGNORE INTO role (code, name, description, status, active, deleted, creator, created_time, modifier, modified_time) VALUES
    ('admin', '管理员', '系统管理员，拥有所有权限', 1, 1, 0, 'system', CURRENT_TIMESTAMP, 'system', CURRENT_TIMESTAMP),
    ('user', '普通用户', '普通用户角色', 1, 1, 0, 'system', CURRENT_TIMESTAMP, 'system', CURRENT_TIMESTAMP);

-- 插入默认权限
INSERT OR IGNORE INTO permission (code, name, description, status, active, deleted, creator, created_time, modifier, modified_time) VALUES
    ('user:read', '查看用户', '查看用户信息', 1, 1, 0, 'system', CURRENT_TIMESTAMP, 'system', CURRENT_TIMESTAMP),
    ('user:write', '编辑用户', '创建和编辑用户', 1, 1, 0, 'system', CURRENT_TIMESTAMP, 'system', CURRENT_TIMESTAMP),
    ('user:delete', '删除用户', '删除用户', 1, 1, 0, 'system', CURRENT_TIMESTAMP, 'system', CURRENT_TIMESTAMP),
    ('role:read', '查看角色', '查看角色信息', 1, 1, 0, 'system', CURRENT_TIMESTAMP, 'system', CURRENT_TIMESTAMP),
    ('role:write', '编辑角色', '创建和编辑角色', 1, 1, 0, 'system', CURRENT_TIMESTAMP, 'system', CURRENT_TIMESTAMP),
    ('role:delete', '删除角色', '删除角色', 1, 1, 0, 'system', CURRENT_TIMESTAMP, 'system', CURRENT_TIMESTAMP);

-- 为管理员角色分配所有权限
INSERT OR IGNORE INTO role_permission (role_code, permission_code, active, deleted, creator, created_time, modifier, modified_time)
SELECT r.code, p.code, 1, 0, 'system', CURRENT_TIMESTAMP, 'system', CURRENT_TIMESTAMP
FROM role r, permission p
WHERE r.code = 'admin';
"""

    from datetime import datetime
    current_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # 格式化表定义
    pg_table_defs = '\n\n'.join(pg_scripts) if pg_scripts else "-- 无法从 ORM 生成，请手动定义表结构"
    sqlite_table_defs = '\n\n'.join(sqlite_scripts) if sqlite_scripts else "-- 无法从 ORM 生成，请手动定义表结构"

    # 创建 PostgreSQL 脚本
    pg_script_path = db_dir / "init_postgresql.sql"
    pg_script_path.write_text(
        pg_init_script.format(date=current_date, table_definitions=pg_table_defs),
        encoding='utf-8'
    )
    print_success(f"已创建: {pg_script_path}")

    # 创建 SQLite 脚本
    sqlite_script_path = db_dir / "init_sqlite.sql"
    sqlite_script_path.write_text(
        sqlite_init_script.format(date=current_date, table_definitions=sqlite_table_defs),
        encoding='utf-8'
    )
    print_success(f"已创建: {sqlite_script_path}")

    # 创建 README
    readme_content = """# 数据库脚本

本目录包含 PySpring 框架的数据库初始化脚本。

## 文件说明

- `init_postgresql.sql`: PostgreSQL 数据库初始化脚本
- `init_sqlite.sql`: SQLite 数据库初始化脚本

## 使用方法

### PostgreSQL

```bash
# 创建数据库
createdb your_database_name

# 执行初始化脚本
psql -U your_username -d your_database_name -f init_postgresql.sql
```

### SQLite

```bash
# 执行初始化脚本
sqlite3 your_database.db < init_sqlite.sql
```

## 数据库表说明

### 核心表

- **users**: 用户表
- **roles**: 角色表
- **user_roles**: 用户角色关联表
- **permissions**: 权限表
- **role_permissions**: 角色权限关联表

### 安全相关表

- **refresh_tokens**: Refresh Token 表

## 默认数据

脚本会自动创建以下默认数据：

### 角色
- `admin`: 管理员（拥有所有权限）
- `user`: 普通用户

### 权限
- `user:read`: 查看用户
- `user:write`: 编辑用户
- `user:delete`: 删除用户
- `role:read`: 查看角色
- `role:write`: 编辑角色
- `role:delete`: 删除角色

## 注意事项

1. 执行脚本前请确保数据库已创建
2. 脚本支持重复执行，不会覆盖已有数据
3. 生产环境请根据实际需求调整表结构和索引
4. 建议定期备份数据库
"""

    readme_path = db_dir / "README.md"
    readme_path.write_text(readme_content, encoding='utf-8')
    print_success(f"已创建: {readme_path}")


def create_project_structure(target_dir: Path):
    """创建标准化的项目目录结构"""
    print_info("\n创建项目目录结构...")

    # 创建主要目录
    directories = [
        "app",  # 应用代码
        "app/api",  # API路由
        "app/models",  # 数据模型
        "app/services",  # 业务逻辑
        "app/schemas",  # Pydantic schemas
        "config",  # 配置文件
        "scripts",  # 脚本文件
        "scripts/db",  # 数据库脚本
        "tests",  # 测试文件
        "logs",  # 日志文件
        "data",  # 数据文件
    ]

    for dir_name in directories:
        dir_path = target_dir / dir_name
        dir_path.mkdir(parents=True, exist_ok=True)

        # 在Python包目录中创建 __init__.py
        if dir_name.startswith("app"):
            init_file = dir_path / "__init__.py"
            if not init_file.exists():
                init_file.write_text('"""PySpring Application"""\n', encoding='utf-8')

    print_success("项目目录结构已创建")


def create_main_file(target_dir: Path, force: bool = False):
    """创建主程序入口文件（从模板读取）"""
    main_path = target_dir / "main.py"

    if main_path.exists() and not force:
        print_info(f"main.py 已存在: {main_path}")
        return

    # 从模板目录读取
    template_path = get_template_dir() / "app" / "main.py.template"

    if not template_path.exists():
        print_error(f"模板文件不存在: app/main.py.template")
        return

    # 直接复制内容
    content = template_path.read_text(encoding='utf-8')
    main_path.write_text(content, encoding='utf-8')
    print_success(f"已创建: {main_path}")


def create_pyproject_toml(target_dir: Path, force: bool = False):
    """创建 pyproject.toml 配置文件（从模板读取）"""
    pyproject_path = target_dir / "pyproject.toml"

    if pyproject_path.exists() and not force:
        print_info(f"pyproject.toml 已存在: {pyproject_path}")
        return

    # 从模板目录读取
    template_path = get_template_dir() / "project" / "pyproject.toml.template"

    if not template_path.exists():
        print_error(f"模板文件不存在: project/pyproject.toml.template")
        return

    # 读取模板并替换项目名称
    content = template_path.read_text(encoding='utf-8')
    # 替换项目名称
    content = content.replace('name = "pyspring"', 'name = "my-pyspring-app"')
    # 替换作者信息为占位符
    content = content.replace(
        '{ name="Yingchun", email="allureyc@gmail.com" }',
        '{ name="Your Name", email="your.email@example.com" }'
    )
    # 替换项目 URL
    content = content.replace(
        '"Homepage" = "https://github.com/365tools/PySpring"',
        '"Homepage" = "https://github.com/yourusername/my-pyspring-app"'
    )
    content = content.replace(
        '"Bug Tracker" = "https://github.com/365tools/PySpring/issues"',
        '"Bug Tracker" = "https://github.com/yourusername/my-pyspring-app/issues"'
    )
    # 移除 pyspring CLI 入口
    content = content.replace(
        '[project.scripts]\npyspring = "pyspring.cli:main"\n\n',
        ''
    )

    pyproject_path.write_text(content, encoding='utf-8')
    print_success(f"已创建: {pyproject_path}")


def create_gitignore(target_dir: Path, force: bool = False):
    """创建 .gitignore（从模板读取）"""
    gitignore_path = target_dir / ".gitignore"

    if gitignore_path.exists() and not force:
        print_info(f".gitignore 已存在: {gitignore_path}")
        return

    # 从模板目录读取
    template_path = get_template_dir() / "project" / ".gitignore.template"

    if not template_path.exists():
        print_error(f"模板文件不存在: project/.gitignore.template")
        return

    # 直接复制内容
    content = template_path.read_text(encoding='utf-8')
    gitignore_path.write_text(content, encoding='utf-8')
    print_success(f"已创建: {gitignore_path}")


def init_project(
        target_dir: Optional[str] = None,
        force: bool = False,
        minimal: bool = False,
        skip_env: bool = False
):
    """
    初始化 PySpring 项目配置
    
    Args:
        target_dir: 目标目录（默认为当前目录）
        force: 是否强制覆盖已存在的文件
        minimal: 是否只创建最小配置
        skip_env: 是否跳过 .env 文件生成
    """
    print_header("PySpring 框架初始化")

    # 确定目标目录
    if target_dir:
        target_path = Path(target_dir).resolve()
    else:
        target_path = Path.cwd()

    print_info(f"目标目录: {target_path}")

    # 创建项目目录结构
    if not minimal:
        create_project_structure(target_path)

    # 创建 config 目录
    config_dir = target_path / "config"
    config_dir.mkdir(parents=True, exist_ok=True)
    print_success(f"已创建目录: {config_dir}")

    # 配置文件列表 - 自动扫描（会自动验证必需文件）
    config_files = get_config_files_from_templates(minimal=minimal)

    print_info("\n开始创建配置文件...")

    # 创建配置文件
    created_count = 0
    for filename, description in config_files:
        print(f"\n→ {description}")
        if create_config_file(config_dir / filename, filename, force):
            created_count += 1

    # 创建数据库脚本
    if not minimal:
        print_info("\n创建数据库初始化脚本...")
        create_database_scripts(target_path)

    # 生成密钥
    print_info("\n生成安全密钥...")
    jwt_secret = generate_jwt_secret()
    encryption_key = generate_encryption_key()

    print_success(f"JWT 签名密钥: {jwt_secret}")
    if encryption_key:
        print_success(f"JWT 加密密钥: {encryption_key[:20]}...")

    # 创建 .env 文件
    if not skip_env:
        print_info("\n创建环境变量文件...")
        create_env_file(target_path, jwt_secret, encryption_key, force)

    # 创建其他项目文件
    if not minimal:
        print_info("\n创建项目文件...")
        create_main_file(target_path, force)
        create_pyproject_toml(target_path, force)

    # 创建 .gitignore
    print_info("\n创建 .gitignore...")
    create_gitignore(target_path, force)

    # 完成
    print_header("初始化完成")
    print_success(f"共创建 {created_count} 个配置文件")

    # 项目结构展示
    if not minimal:
        print(f"\n{Colors.BOLD}项目结构:{Colors.ENDC}")
        print(f"""
  {target_path.name}/
  ├── app/              # 应用代码
  │   ├── api/          # API路由
  │   ├── models/       # 数据模型
  │   ├── services/     # 业务逻辑
  │   └── schemas/      # Pydantic schemas
  ├── config/           # 配置文件
  ├── scripts/          # 脚本文件
  │   └── db/           # 数据库初始化脚本
  ├── tests/            # 测试文件
  ├── logs/             # 日志文件
  ├── data/             # 数据文件
  ├── main.py           # 应用入口
  ├── pyproject.toml    # 项目配置和依赖
  ├── .env              # 环境变量
  └── .gitignore        # Git忽略文件
        """)

    # 后续步骤提示
    print(f"\n{Colors.BOLD}后续步骤:{Colors.ENDC}")
    print(f"  1. 安装依赖: pip install -e .")
    print(f"  2. 或安装开发依赖: pip install -e .[dev]")
    print(f"  3. 检查并修改配置文件: {config_dir}")
    print(f"  4. 检查并修改环境变量: {target_path / '.env'}")
    print(f"  5. 初始化数据库: 执行 scripts/db/ 下的SQL脚本")
    print(f"  6. 启动应用: python main.py")

    print(f"\n{Colors.BOLD}数据库初始化:{Colors.ENDC}")
    print(f"  PostgreSQL: psql -U user -d dbname -f scripts/db/init_postgresql.sql")
    print(f"  SQLite:     sqlite3 data/app.db < scripts/db/init_sqlite.sql")

    print(f"\n{Colors.BOLD}重要提醒:{Colors.ENDC}")
    print(f"  {Colors.WARNING}• 请勿将 .env 文件提交到代码仓库{Colors.ENDC}")
    print(f"  {Colors.WARNING}• 生产环境请更换 JWT 密钥{Colors.ENDC}")
    print(f"  {Colors.WARNING}• 建议启用 JWT 加密（生产环境）{Colors.ENDC}")
    print(f"  {Colors.WARNING}• 初始化数据库前请先创建数据库{Colors.ENDC}")

    print(f"\n{Colors.BOLD}文档参考:{Colors.ENDC}")
    print(f"  • 快速开始: https://github.com/365tools/PySpring/docs/")
    print(f"  • 认证配置: https://github.com/365tools/PySpring/docs/SECURITY_CONFIG_GUIDE.md")
    print(f"  • JWT 加密: https://github.com/365tools/PySpring/docs/JWT_ENCRYPTION_GUIDE.md")
    print(f"  • 数据库配置: https://github.com/365tools/PySpring/docs/REPOSITORIES_CONFIG_GUIDE.md")

    print()


def register_subcommand(subparsers):
    """注册 init 子命令"""
    import argparse
    parser = subparsers.add_parser(
        'init',
        help='Initialize PySpring project configuration',
        description="""
Initialize PySpring Project Structure and Configuration Files.

Examples:
  # Initialize current directory
  pyspring init

  # Initialize specific directory
  pyspring init /path/to/project

  # Force overwrite existing files
  pyspring init --force
  
  # Create minimal configuration
  pyspring init --minimal
  
  # Skip .env file generation
  pyspring init --skip-env
        """,
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    parser.add_argument(
        'target_dir',
        nargs='?',
        default=None,
        help='Target directory (default: current directory)'
    )

    parser.add_argument(
        '-f', '--force',
        action='store_true',
        help='Force overwrite existing files'
    )

    parser.add_argument(
        '-m', '--minimal',
        action='store_true',
        help='Create minimal configuration only'
    )

    parser.add_argument(
        '--skip-env',
        action='store_true',
        help='Skip .env file generation'
    )

    parser.set_defaults(func=run)


def run(args):
    """运行初始化命令"""
    # 处理 target_dir 为 None 的情况
    target_dir = getattr(args, 'target_dir', None)
    
    try:
        init_project(
            target_dir=target_dir,
            force=args.force,
            minimal=args.minimal,
            skip_env=args.skip_env
        )
    except KeyboardInterrupt:
        print_error("\nUpdate cancelled")
        sys.exit(1)
    except Exception as e:
        print_error(f"\nInitialization failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


def main():
    """Independent entry point (legacy support)"""
    import argparse
    parser = argparse.ArgumentParser(description='PySpring Project Initialization Tool')

    parser.add_argument('target_dir', nargs='?', default=None, help='Target directory')
    parser.add_argument('-f', '--force', action='store_true', help='Force overwrite')
    parser.add_argument('-m', '--minimal', action='store_true', help='Minimal config')
    parser.add_argument('--skip-env', action='store_true', help='Skip .env')

    args = parser.parse_args()
    run(args)


if __name__ == "__main__":
    main()
