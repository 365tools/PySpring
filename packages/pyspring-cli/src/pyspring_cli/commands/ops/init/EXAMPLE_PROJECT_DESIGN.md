# PySpring Init 完整项目示例功能设计

## 🎯 目标

创建一个 `pyspring init --example` 命令，生成一个**开箱即用**的完整示例项目，包含：

1. ✅ 完整的项目结构
2. ✅ 所有功能的示例代码
3. ✅ 可以直接运行的 FastAPI 应用
4. ✅ 覆盖框架所有可自定义功能

## 📁 生成的项目结构

```
my-pyspring-app/
├── app/                                    # 应用代码
│   ├── __init__.py
│   ├── main.py                            # FastAPI 应用入口
│   ├── config/                            # 配置类
│   │   ├── __init__.py
│   │   ├── settings.py                    # Pydantic 配置模型
│   │   └── beans.py                       # @Configuration + @Bean 示例
│   ├── api/                               # API 路由
│   │   ├── __init__.py
│   │   ├── deps.py                        # 依赖注入辅助函数
│   │   ├── health.py                      # 健康检查
│   │   ├── auth.py                        # 认证相关 API
│   │   └── users.py                       # 用户管理 API
│   ├── models/                            # 数据库模型
│   │   ├── __init__.py
│   │   ├── base.py                        # Base Model
│   │   └── user.py                        # User Model 示例
│   ├── schemas/                           # Pydantic Schemas
│   │   ├── __init__.py
│   │   ├── common.py                      # 通用 Schema
│   │   ├── auth.py                        # 认证 Schema
│   │   └── user.py                        # 用户 Schema
│   ├── services/                          # 业务逻辑层
│   │   ├── __init__.py
│   │   ├── user.py                        # UserService（带生命周期）
│   │   ├── email.py                       # EmailService 示例
│   │   └── cache.py                       # CacheService 示例
│   ├── repositories/                      # 数据访问层
│   │   ├── __init__.py
│   │   ├── base.py                        # BaseRepository
│   │   └── user.py                        # UserRepository
│   ├── middleware/                        # 中间件
│   │   ├── __init__.py
│   │   ├── request_logger.py             # 请求日志中间件
│   │   ├── timing.py                      # 计时中间件
│   │   └── error_handler.py              # 错误处理中间件
│   ├── initializers/                      # 启动初始化器
│   │   ├── __init__.py
│   │   ├── database.py                    # DatabaseInitializer
│   │   ├── cache.py                       # CacheInitializer
│   │   └── data_seeder.py                 # DataSeederInitializer
│   ├── shutdown/                          # 关闭处理器
│   │   ├── __init__.py
│   │   ├── database.py                    # DatabaseShutdownHandler
│   │   └── metrics.py                     # MetricsExportHandler
│   ├── aop/                               # AOP 切面示例
│   │   ├── __init__.py
│   │   ├── logging_aspect.py             # 日志切面
│   │   └── performance_aspect.py         # 性能监控切面
│   └── utils/                             # 工具类
│       ├── __init__.py
│       └── helpers.py
├── config/                                 # 配置文件
│   ├── application.yaml                   # 应用配置
│   ├── logging.yaml                       # 日志配置
│   ├── database.yaml                      # 数据库配置
│   ├── security.yaml                      # 安全配置
│   └── container.yaml                     # IOC 容器配置
├── scripts/                               # 脚本
│   ├── db/                                # 数据库脚本
│   │   ├── init_postgresql.sql
│   │   └── init_sqlite.sql
│   └── dev/                               # 开发脚本
│       ├── run_dev.sh
│       └── run_dev.bat
├── tests/                                 # 测试
│   ├── __init__.py
│   ├── conftest.py                       # Pytest 配置
│   ├── test_api/
│   ├── test_services/
│   └── test_repositories/
├── logs/                                  # 日志目录（.gitignore）
├── data/                                  # 数据目录
│   └── .gitkeep
├── docs/                                  # 文档
│   ├── README.md
│   ├── API.md                            # API 文档
│   └── DEPLOYMENT.md                     # 部署指南
├── .env                                   # 环境变量
├── .env.example                          # 环境变量示例
├── .gitignore                            # Git 忽略文件
├── pyproject.toml                        # 项目配置
├── requirements.txt                      # 依赖列表
├── README.md                             # 项目说明
└── Dockerfile                            # Docker 配置（可选）
```

## 🎨 示例代码涵盖的功能

### 1. IOC 容器功能

- ✅ `@Component` 组件注册
- ✅ `@Configuration` + `@Bean` 工厂方法
- ✅ `@Singleton` / `@Prototype` 作用域
- ✅ 构造函数依赖注入
- ✅ 接口到实现的自动映射

### 2. 生命周期管理

- ✅ `ILifecycle` 接口（on_init / on_destroy）
- ✅ `IStartupInitializer` 启动初始化器
- ✅ `IShutdownHandler` 关闭处理器
- ✅ 依赖顺序自动管理

### 3. AOP 切面编程

- ✅ `@Before` / `@After` / `@Around` 切面
- ✅ 日志切面示例
- ✅ 性能监控切面示例
- ✅ 异常处理切面示例

### 4. 配置管理

- ✅ YAML 配置文件
- ✅ 环境变量注入
- ✅ Pydantic Settings 类型安全
- ✅ 多环境配置支持

### 5. 数据库集成

- ✅ SQLAlchemy ORM 集成
- ✅ Repository 模式
- ✅ 事务管理
- ✅ 数据库初始化脚本

### 6. 缓存集成

- ✅ Redis 缓存服务
- ✅ 缓存装饰器
- ✅ 缓存预热

### 7. 认证授权

- ✅ JWT Token 认证
- ✅ 登录/登出 API
- ✅ 权限验证
- ✅ 用户管理

### 8. FastAPI 集成

- ✅ 应用生命周期管理
- ✅ 依赖注入集成
- ✅ 中间件示例
- ✅ 异常处理

### 9. 日志系统

- ✅ Loguru 日志配置
- ✅ 结构化日志
- ✅ 日志过滤
- ✅ 文件轮转

### 10. 测试

- ✅ Pytest 配置
- ✅ 单元测试示例
- ✅ 集成测试示例
- ✅ API 测试示例

## 🚀 使用方式

### 创建完整示例项目

```bash
# 在当前目录创建
pyspring init . --example

# 在指定目录创建
pyspring init my-project --example

# 创建最小化示例
pyspring init my-project --example --minimal
```

### 生成后立即运行

```bash
cd my-project

# 1. 安装依赖
pip install -r requirements.txt

# 2. 配置环境变量（编辑 .env）
# 3. 初始化数据库
python -m app.scripts.init_db

# 4. 运行应用
uvicorn app.main:app --reload

# 访问 http://localhost:8000
# API 文档: http://localhost:8000/docs
```

## 📋 命令选项

```bash
pyspring init [target_dir] [options]

Options:
  --example          创建完整的示例项目（可直接运行）
  --minimal          最小化配置（只包含核心功能）
  --force, -f        强制覆盖已存在的文件
  --skip-env         跳过 .env 文件生成
  --with-docker      包含 Docker 配置
  --with-tests       包含完整测试示例
  --db-type TYPE     数据库类型 (postgresql/mysql/sqlite)
```

## 🎯 实现计划

### Phase 1: 模板文件准备（当前任务）

1. 创建完整的示例代码模板
2. 在 `src/pyspring/templates/` 下组织文件
3. 确保所有代码可运行

### Phase 2: CLI 命令增强

1. 在 `init.py` 添加 `--example` 选项
2. 修改 `core.py` 支持示例项目生成
3. 添加项目名称替换逻辑

### Phase 3: 文档完善

1. 更新 README.md
2. 添加快速开始指南
3. 添加功能说明文档

### Phase 4: 测试验证

1. 测试生成的项目
2. 确保可以直接运行
3. 验证所有功能正常

## 💡 特性亮点

1. **开箱即用**：生成的项目可以直接运行，无需额外配置
2. **最佳实践**：展示 PySpring 的推荐用法和项目结构
3. **功能完整**：覆盖框架所有核心功能
4. **易于定制**：代码清晰，便于根据需求修改
5. **生产就绪**：包含错误处理、日志、监控等生产环境必备功能

## 🔗 相关文档

- [PySpring IOC 容器指南](../docs/IOC_CONTAINER.md)
- [生命周期管理](../docs/LIFECYCLE_GUIDE.md)
- [配置管理最佳实践](../docs/CONFIG_BEST_PRACTICES.md)
- [AOP 切面编程](../docs/AOP_GUIDE.md)
