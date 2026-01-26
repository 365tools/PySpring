"""
PySpring Project Initialization Core Logic
"""
import shutil
import sys
import traceback
from datetime import datetime
from pathlib import Path
from typing import Optional

from pyspring.cli.core.ui.console import Colors, print_header, print_success, print_info, print_warning, print_error, print_title
from pyspring.cli.core.ui.help import print_standard_command_help
from sqlalchemy import create_engine
from sqlalchemy.schema import CreateTable

from .keygen import generate_jwt_secret, generate_encryption_key
from .templates import (
    ENV_FILE_CONTENT, POSTGRES_INIT_SCRIPT, SQLITE_INIT_SCRIPT,
    DB_README_CONTENT
)


def get_template_dir() -> Path:
    """Get template directory"""
    # From cli/commands/ops/init/core.py up to pyspring/templates
    # core.py -> init -> ops -> commands -> cli -> pyspring
    return Path(__file__).parent.parent.parent.parent.parent / "templates"


def get_config_files_from_templates(minimal: bool = False) -> list[tuple[str, str]]:
    """
    Scan configuration files from template directory automatically
    
    Args:
        minimal: Whether to return only minimal required configurations
    
    Returns:
        List of configuration files [(filename, description), ...]
        
    Raises:
        FileNotFoundError: Template directory does not exist or missing required configurations
    """
    template_config_dir = get_template_dir() / "config"
    if not template_config_dir.exists():
        raise FileNotFoundError(f"Template configuration directory not found: {template_config_dir}")

    config_descriptions = {
        "container.yaml": "IoC Container Configuration",
        "logging.yaml": "Logging Configuration",
        "repositories.yaml": "Database and Cache Configuration",
        "security.yaml": "Authentication and Authorization Configuration",
    }

    # Required configuration files
    required_configs = ["security.yaml"]
    if not minimal:
        required_configs.extend(["logging.yaml", "repositories.yaml"])

    # Scan all .yaml files
    config_files = []
    found_files = set()

    for yaml_file in sorted(template_config_dir.glob("*.yaml")):
        filename = yaml_file.name
        found_files.add(filename)
        description = config_descriptions.get(filename, f"{filename} Configuration")
        config_files.append((filename, description))

    # Check if required configuration files exist
    missing_configs = [cfg for cfg in required_configs if cfg not in found_files]
    if missing_configs:
        raise FileNotFoundError(
            f"Missing required configuration file templates: {', '.join(missing_configs)}\n"
            f"Please check template directory: {template_config_dir}"
        )

    # If minimal mode, return only required configurations
    if minimal:
        config_files = [(f, d) for f, d in config_files if f in required_configs]

    return config_files


def create_config_file(target_path: Path, template_name: str, force: bool = False, template_subdir: str = "config") -> bool:
    """
    Create configuration file
    
    Args:
        target_path: Target file path
        template_name: Template file name
        force: Whether to force overwrite
        template_subdir: Template subdirectory (config, app, project)
        
    Returns:
        Whether creation was successful
    """
    if target_path.exists() and not force:
        print_warning(f"File exists, skipping: {target_path}")
        return False

    template_dir = get_template_dir() / template_subdir
    template_path = template_dir / template_name

    if not template_path.exists():
        print_error(f"Template file not found: {template_subdir}/{template_name}")
        return False

    # Ensure target directory exists
    target_path.parent.mkdir(parents=True, exist_ok=True)

    # Copy file
    shutil.copy2(template_path, target_path)
    print_success(f"Created: {target_path}")
    return True


def create_env_file(target_dir: Path, jwt_secret: str, encryption_key: str, force: bool = False):
    """Create .env file"""
    env_path = target_dir / ".env.example"

    jwt_encryption_key_line = f"JWT_ENCRYPTION_KEY={encryption_key}" if encryption_key else "# JWT_ENCRYPTION_KEY=your-encryption-key"

    content = ENV_FILE_CONTENT.format(
        jwt_secret=jwt_secret,
        jwt_encryption_key_line=jwt_encryption_key_line
    )

    env_path.write_text(content, encoding='utf-8')
    print_success(f"Created: {env_path}")

    # Create .env file as well
    env_real_path = target_dir / ".env"
    if not env_real_path.exists() or force:
        shutil.copy2(env_path, env_real_path)
        print_success(f"Created: {env_real_path}")


def create_database_scripts(target_dir: Path):
    """Create database initialization scripts (generated from ORM models)"""
    db_dir = target_dir / "scripts" / "db"
    db_dir.mkdir(parents=True, exist_ok=True)
    print_success(f"Directory created: {db_dir}")

    try:
        print_info("Generating database scripts from ORM models...")

        # 延迟导入 ORM 表，避免在 CLI 加载时触发表注册
        from pyspring.security.orm.tables import (
            UserTable, RoleTable, PermissionTable, UserRoleTable,
            RolePermissionTable, RefreshTokenTable, TokenBlacklistTable
        )

        # PostgreSQL script generation
        pg_engine = create_engine('postgresql://localhost/dummy', strategy='mock', executor=lambda sql, *_: None)
        pg_scripts = []

        for table in [UserTable, RoleTable, PermissionTable, UserRoleTable,
                      RolePermissionTable, RefreshTokenTable, TokenBlacklistTable]:
            # Explicitly cast to sqlalchemy.sql.schema.Table to satisfy type checker
            create_table = CreateTable(table.__table__, if_not_exists=True)  # type: ignore
            pg_scripts.append(str(create_table.compile(dialect=pg_engine.dialect)) + ';')

        # SQLite script generation
        sqlite_engine = create_engine('sqlite:///dummy.db', strategy='mock', executor=lambda sql, *_: None)
        sqlite_scripts = []

        for table in [UserTable, RoleTable, PermissionTable, UserRoleTable,
                      RolePermissionTable, RefreshTokenTable, TokenBlacklistTable]:
            create_table = CreateTable(table.__table__, if_not_exists=True)  # type: ignore
            sqlite_scripts.append(str(create_table.compile(dialect=sqlite_engine.dialect)) + ';')

        print_success("SQL scripts generated from ORM models")

    except ImportError as e:
        print_warning(f"Could not import ORM models, using default scripts: {e}")
        # If import fails, use default scripts
        pg_scripts = []
        sqlite_scripts = []

    current_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Format table definitions
    pg_table_defs = '\n\n'.join(pg_scripts) if pg_scripts else "-- Could not generate from ORM, please define table structure manually"
    sqlite_table_defs = '\n\n'.join(sqlite_scripts) if sqlite_scripts else "-- Could not generate from ORM, please define table structure manually"

    # Create PostgreSQL script
    pg_script_path = db_dir / "init_postgresql.sql"
    pg_script_path.write_text(
        POSTGRES_INIT_SCRIPT.format(date=current_date, table_definitions=pg_table_defs),
        encoding='utf-8'
    )
    print_success(f"Created: {pg_script_path}")

    # Create SQLite script
    sqlite_script_path = db_dir / "init_sqlite.sql"
    sqlite_script_path.write_text(
        SQLITE_INIT_SCRIPT.format(date=current_date, table_definitions=sqlite_table_defs),
        encoding='utf-8'
    )
    print_success(f"Created: {sqlite_script_path}")

    readme_path = db_dir / "README.md"
    readme_path.write_text(DB_README_CONTENT, encoding='utf-8')
    print_success(f"Created: {readme_path}")


def create_project_structure(target_dir: Path):
    """Create standardized project directory structure"""
    print_info("\nCreating project directory structure...")

    # Create main directories
    directories = [
        "app",  # Application code
        "app/api",  # API routes
        "app/models",  # Data models
        "app/services",  # Business logic
        "app/schemas",  # Pydantic schemas
        "config",  # Configuration files
        "scripts",  # Script files
        "scripts/db",  # Database scripts
        "tests",  # Test files
        "logs",  # Log files
        "data",  # Data files
    ]

    for dir_name in directories:
        dir_path = target_dir / dir_name
        dir_path.mkdir(parents=True, exist_ok=True)

        # Create __init__.py in Python package directories
        if dir_name.startswith("app"):
            init_file = dir_path / "__init__.py"
            if not init_file.exists():
                init_file.write_text('"""PySpring Application"""\n', encoding='utf-8')

    print_success("Project directory structure created")


def create_main_file(target_dir: Path, force: bool = False):
    """Create main entry file (read from template)"""
    main_path = target_dir / "main.py"

    if main_path.exists() and not force:
        print_info(f"main.py exists: {main_path}")
        return

    # Read from template directory
    template_path = get_template_dir() / "app" / "main.py.template"

    if not template_path.exists():
        print_error(f"Template file not found: app/main.py.template")
        return

    # Copy content directly
    content = template_path.read_text(encoding='utf-8')
    main_path.write_text(content, encoding='utf-8')
    print_success(f"Created: {main_path}")


def create_pyproject_toml(target_dir: Path, force: bool = False):
    """Create pyproject.toml configuration file (read from template)"""
    pyproject_path = target_dir / "pyproject.toml"

    if pyproject_path.exists() and not force:
        print_info(f"pyproject.toml exists: {pyproject_path}")
        return

    # Read from template directory
    template_path = get_template_dir() / "project" / "pyproject.toml.template"

    if not template_path.exists():
        print_error(f"Template file not found: project/pyproject.toml.template")
        return

    # Read template and replace project name
    content = template_path.read_text(encoding='utf-8')
    # Replace project name
    content = content.replace('name = "pyspring"', 'name = "my-pyspring-app"')
    # Replace author info with placeholder
    content = content.replace(
        '{ name="Yingchun", email="allureyc@gmail.com" }',
        '{ name="Your Name", email="your.email@example.com" }'
    )
    # Replace project URL
    content = content.replace(
        '"Homepage" = "https://github.com/365tools/PySpring"',
        '"Homepage" = "https://github.com/yourusername/my-pyspring-app"'
    )
    content = content.replace(
        '"Bug Tracker" = "https://github.com/365tools/PySpring/issues"',
        '"Bug Tracker" = "https://github.com/yourusername/my-pyspring-app/issues"'
    )
    # Remove pyspring CLI entry point
    content = content.replace(
        '[project.scripts]\npyspring = "pyspring.cli:main"\n\n',
        ''
    )

    pyproject_path.write_text(content, encoding='utf-8')
    print_success(f"Created: {pyproject_path}")


def create_gitignore(target_dir: Path, force: bool = False):
    """Create .gitignore (read from template)"""
    gitignore_path = target_dir / ".gitignore"

    if gitignore_path.exists() and not force:
        print_info(f".gitignore exists: {gitignore_path}")
        return

    # Read from template directory
    template_path = get_template_dir() / "project" / ".gitignore.template"

    if not template_path.exists():
        print_error(f"Template file not found: project/.gitignore.template")
        return

    # Copy content directly
    content = template_path.read_text(encoding='utf-8')
    gitignore_path.write_text(content, encoding='utf-8')
    print_success(f"Created: {gitignore_path}")


def copy_template_dir_recursive(src_dir: Path, dst_dir: Path, force: bool = False):
    """
    递归复制模板目录，去除 .template 后缀
    
    Args:
        src_dir: 源模板目录
        dst_dir: 目标目录
        force: 是否强制覆盖（默认覆盖已存在文件）
    """
    for item in src_dir.rglob("*"):
        if item.is_file():
            # 计算相对路径
            rel_path = item.relative_to(src_dir)

            # 去除 .template 后缀
            if rel_path.name.endswith('.template'):
                target_name = rel_path.name[:-9]  # 去除 '.template'
                target_path = dst_dir / rel_path.parent / target_name
            else:
                target_path = dst_dir / rel_path

            # 默认覆盖已存在的文件
            if target_path.exists():
                print_info(f"Overwriting: {target_path}")
            
            # 创建目标目录
            target_path.parent.mkdir(parents=True, exist_ok=True)

            # 复制文件
            shutil.copy2(item, target_path)
            print_success(f"Created: {target_path}")



def create_example_project(target_dir: Path, force: bool = False):
    """
    创建完整的示例项目
    
    包含所有 PySpring 功能的可运行示例：
    - IOC 容器和依赖注入
    - 生命周期管理
    - 数据库集成（SQLAlchemy）
    - 缓存服务（Redis）
    - JWT 认证
    - FastAPI 路由
    - 中间件
    - 结构化日志
    
    Args:
        target_dir: 目标目录
        force: 是否强制清空目录后再初始化
    """
    print_header("Creating Complete Example Project")
    print_info(f"Target Directory: {target_dir}")

    # 如果 force=True，清空目标目录（仅保留 .git）
    if force and target_dir.exists():
        print_warning(f"Force mode: Cleaning directory {target_dir}")
        preserved_dirs = {'.git'}

        for item in target_dir.iterdir():
            if item.name in preserved_dirs:
                print_info(f"Preserving: {item}")
                continue

            try:
                if item.is_dir():
                    shutil.rmtree(item)
                    print_info(f"Removed directory: {item}")
                else:
                    item.unlink()
                    print_info(f"Removed file: {item}")
            except Exception as e:
                print_warning(f"Failed to remove {item}: {e}")

    # 检查示例模板目录
    example_template_dir = get_template_dir() / "example"
    if not example_template_dir.exists():
        print_error(f"Example template directory not found: {example_template_dir}")
        print_warning("Please ensure PySpring is properly installed with example templates.")
        return False

    # 复制整个示例项目结构（默认覆盖已存在文件）
    print_info("\nCopying example project files...")
    copy_template_dir_recursive(example_template_dir, target_dir, force)

    print_header("Example Project Created Successfully")

    # 显示项目结构
    print_title("Project Structure")
    print(f"""
  {target_dir.name}/
  ├── app/                         # Application code
  │   ├── main.py                  # FastAPI entry point with lifecycle
  │   ├── api/                     # API endpoints
  │   │   ├── health.py           # Health check endpoints
  │   │   ├── auth.py             # Authentication endpoints
  │   │   └── users.py            # User management endpoints
  │   ├── services/               # Business logic layer
  │   │   ├── user_service.py     # User service with caching
  │   │   ├── auth_service.py     # JWT authentication
  │   │   └── cache_service.py    # Redis cache service
  │   ├── repositories/           # Data access layer
  │   │   └── user_repository.py  # User repository
  │   ├── models/                 # ORM models
  │   │   └── user.py             # User model
  │   ├── database/               # Database configuration
  │   │   ├── session.py          # SQLAlchemy session
  │   │   └── initializer.py      # DB initializer
  │   ├── middleware/             # Middleware
  │   │   ├── request_logger.py   # Request logging
  │   │   ├── timing.py           # Performance monitoring
  │   │   └── error_handler.py    # Global exception handler
  │   └── dependencies/           # FastAPI dependencies
  │       └── auth.py             # Auth dependencies
  ├── config/                     # Configuration files
  │   ├── application.yaml        # Application config
  │   ├── container.yaml          # IOC container config
  │   └── logging.yaml            # Logging config
  ├── data/                       # Data directory
  │   └── app.db                  # SQLite database (auto-created)
  ├── logs/                       # Log files (auto-created)
  ├── tests/                      # Test files
  ├── pyproject.toml              # Project config and dependencies
  ├── .env.example                # Environment variables template
  ├── .gitignore                  # Git ignore file
  └── README.md                   # Project documentation
    """)

    # 使用说明
    print_title("Quick Start")
    print("  1. Install dependencies:")
    print(f"     cd {target_dir.name}")
    print()
    print("     # Stable (recommended):")
    print("     uv pip install -r requirements.txt")
    print()
    print("     # Or test version from TestPyPI:")
    print("     uv pip install --index-url https://test.pypi.org/simple/ \\")
    print("                    --extra-index-url https://pypi.org/simple/ \\")
    print("                    -r requirements.txt")
    print()
    print("  2. Configure environment (optional):")
    print("     cp .env.example .env")
    print("     # Edit .env for Redis, database, etc.")
    print()
    print("  3. Start the application:")
    print("     uvicorn app.main:app --reload")
    print("     # or")
    print("     python -m app.main")
    print()
    print("  4. Access the application:")
    print(f"     {Colors.OKBLUE}• API:          http://localhost:8000{Colors.ENDC}")
    print(f"     {Colors.OKBLUE}• API Docs:     http://localhost:8000/docs{Colors.ENDC}")
    print(f"     {Colors.OKBLUE}• Health Check: http://localhost:8000/health{Colors.ENDC}")

    print_title("Default Credentials")
    print("  Username: admin")
    print("  Password: admin123")
    print(f"  {Colors.WARNING}(Created automatically on first run){Colors.ENDC}")

    print_title("Features Demonstrated")
    features = [
        "✅ IOC Container - @component and @inject decorators",
        "✅ Lifecycle Management - ILifecycle with on_startup/on_shutdown",
        "✅ Configuration - YAML + Environment variables",
        "✅ Database Integration - SQLAlchemy async ORM",
        "✅ Repository Pattern - Clean data access layer",
        "✅ Caching - Redis integration with fallback",
        "✅ JWT Authentication - Login, register, token validation",
        "✅ RESTful API - FastAPI routes with dependency injection",
        "✅ Middleware - Request logging, timing, error handling",
        "✅ Structured Logging - Loguru with rotation"
    ]
    for feature in features:
        print(f"  {feature}")

    print_title("Important Notes")
    print(f"  {Colors.WARNING}• Redis is optional - falls back to memory cache if unavailable{Colors.ENDC}")
    print(f"  {Colors.WARNING}• SQLite is used by default (see .env to change database){Colors.ENDC}")
    print(f"  {Colors.WARNING}• Check README.md for detailed usage and learning guide{Colors.ENDC}")

    return True


def init_project(
        target_dir: Optional[str] = None,
        force: bool = False,
        minimal: bool = False,
        skip_env: bool = False,
        example: bool = False
):
    """
    Initialize PySpring Project Configuration
    
    Args:
        target_dir: Target directory (defaults to current directory)
        force: Whether to force overwrite existing files
        minimal: Whether to create minimal configuration only
        skip_env: Whether to skip .env file generation
        example: Whether to create complete example project
    """
    # 如果是创建示例项目，使用完全不同的逻辑
    if example:
        # Determine target directory
        if target_dir:
            target_path = Path(target_dir).resolve()
        else:
            target_path = Path.cwd()

        # 创建示例项目
        return create_example_project(target_path, force)

    # 原有的初始化逻辑
    print_header("PySpring Framework Initialization")

    # Determine target directory
    if target_dir:
        target_path = Path(target_dir).resolve()
    else:
        target_path = Path.cwd()

    print_info(f"Target Directory: {target_path}")

    # Create project directory structure
    if not minimal:
        create_project_structure(target_path)

    # Create config directory
    config_dir = target_path / "config"
    config_dir.mkdir(parents=True, exist_ok=True)
    print_success(f"Directory created: {config_dir}")

    # Configuration file list - automatic scan (validates required files)
    config_files = get_config_files_from_templates(minimal=minimal)

    print_info("\nCreating configuration files...")

    # Create configuration files
    created_count = 0
    for filename, description in config_files:
        print_info(f"→ {description}")
        if create_config_file(config_dir / filename, filename, force):
            created_count += 1

    # Create database scripts
    if not minimal:
        print_info("\nCreating database initialization scripts...")
        create_database_scripts(target_path)

    # Generate keys
    print_info("\nGenerating security keys...")
    jwt_secret = generate_jwt_secret()
    encryption_key = generate_encryption_key()

    print_success(f"JWT Signing Secret: {jwt_secret}")
    if encryption_key:
        print_success(f"JWT Encryption Key: {encryption_key[:20]}...")

    # Create .env file
    if not skip_env:
        print_info("\nCreating environment variable file...")
        create_env_file(target_path, jwt_secret, encryption_key, force)

    # Create other project files
    if not minimal:
        print_info("\nCreating project files...")
        create_main_file(target_path, force)
        create_pyproject_toml(target_path, force)

    # Create .gitignore
    print_info("\nCreating .gitignore...")
    create_gitignore(target_path, force)

    # Finish
    print_header("Initialization Complete")
    print_success(f"Created {created_count} configuration files")

    # Show project structure
    if not minimal:
        print_title("Project Structure")
        print(f"""
  {target_path.name}/
  ├── app/              # Application code
  │   ├── api/          # API routes
  │   ├── models/       # Data models
  │   ├── services/     # Business logic
  │   └── schemas/      # Pydantic schemas
  ├── config/           # Configuration files
  ├── scripts/          # Script files
  │   └── db/           # Database initialization scripts
  ├── tests/            # Test files
  ├── logs/             # Log files
  ├── data/             # Data files
  ├── main.py           # Application entry point
  ├── pyproject.toml    # Project configuration and dependencies
  ├── .env              # Environment variables
  └── .gitignore        # Git ignore file
        """)

    # Next steps hints
    print_title("Next Steps")
    print(f"  1. Setup Environment: pyspring uv setup --dev")
    print(f"  2. Check and modify configurations: {config_dir}")
    print(f"  3. Check and modify environment variables: {target_path / '.env'}")
    print(f"  4. Initialize database: Execute SQL scripts in scripts/db/")
    print(f"  5. Start application: uv run python main.py")

    print_title("Database Initialization")
    print(f"  PostgreSQL: psql -U user -d dbname -f scripts/db/init_postgresql.sql")
    print(f"  SQLite:     sqlite3 data/app.db < scripts/db/init_sqlite.sql")

    print_title("Important Notices")
    print(f"  {Colors.WARNING}• Do NOT commit .env file to version control{Colors.ENDC}")
    print(f"  {Colors.WARNING}• Change JWT keys in production environment{Colors.ENDC}")
    print(f"  {Colors.WARNING}• Enable JWT encryption in production{Colors.ENDC}")
    print(f"  {Colors.WARNING}• Create database before initializing schema{Colors.ENDC}")

    print_title("Documentation Reference")
    print(f"  • Quick Start: https://github.com/365tools/PySpring/docs/")
    print(f"  • Auth Config: https://github.com/365tools/PySpring/docs/SECURITY_CONFIG_GUIDE.md")
    print(f"  • JWT Encryption: https://github.com/365tools/PySpring/docs/JWT_ENCRYPTION_GUIDE.md")
    print(f"  • Database Config: https://github.com/365tools/PySpring/docs/REPOSITORIES_CONFIG_GUIDE.md")

    print()


def show_init_info():
    """Show initialization information and usage"""
    # Check templates
    checks = []
    try:
        tpl_dir = get_template_dir()
        if tpl_dir.exists():
            checks.append((f"Templates available at: {tpl_dir}", True))
        else:
            checks.append((f"Templates missing at: {tpl_dir}", False))
    except Exception as e:
        checks.append((f"Error checking templates: {e}", False))

    print_standard_command_help(
        title="PySpring Project Initialization",
        description="Initialize a new PySpring project structure with best practices.\nThis command helps you scaffold the necessary directories and configuration files.",
        checks=checks,
        usage=[
            ("pyspring init <directory>", "Initialize in specific directory"),
            ("pyspring init .", "Initialize in current directory"),
        ],
        options=[
            ("--minimal", "Create only essential configuration files"),
            ("--force", "Overwrite existing files"),
            ("--skip-env", "Skip .env file generation"),
        ],
        tips=[
            "Always specify a target directory to ensure safety.",
            "Use --minimal for a lightweight setup if you don't need all features."
        ]
    )

    print(f"\n{Colors.WARNING}⚠  No target directory specified.{Colors.ENDC}")
    print("Please specify a directory to start initialization.")


def run(args):
    """Run initialization command"""
    # Handle target_dir being None
    target_dir = getattr(args, 'target_dir', None)

    if target_dir is None:
        show_init_info()
        return

    try:
        init_project(
            target_dir=target_dir,
            force=args.force,
            minimal=args.minimal,
            skip_env=args.skip_env,
            example=getattr(args, 'example', False)
        )
    except KeyboardInterrupt:
        print_error("\nUpdate cancelled")
        sys.exit(1)
    except Exception as e:
        print_error(f"\nInitialization failed: {e}")
        traceback.print_exc()
        sys.exit(1)