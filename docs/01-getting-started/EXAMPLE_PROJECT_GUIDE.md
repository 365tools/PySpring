# PySpring Init --example 功能使用指南

## 功能说明

`pyspring init --example` 命令可以创建一个**完整、可运行**的 PySpring 示例项目，展示框架的所有核心功能。

## 🔧 前置要求：如何运行命令？

### 首次使用 PySpring？

你可能会疑惑："要运行 `pyspring init` 命令，不是得先安装 PySpring 吗？但我还没项目呢！"

**解决方案**：

**方式 1：使用 `uvx` 临时运行（推荐，无需安装）✨**

```bash
# 安装 uv（如果还没有）
pip install uv

# 直接创建项目（自动使用最新版 PySpring，无需预先安装）
uvx --from pyspring pyspring init my-project --example
```

**方式 2：使用 `pipx` 安装 CLI 工具**

```bash
# 安装 pipx
pip install pipx

# 安装 PySpring CLI（仅安装命令行工具，不影响项目）
pipx install pyspring

# 现在可以在任何目录使用
pyspring init my-project --example
```

📖 **更多安装方式**: [安装指南](./INSTALLATION_GUIDE.md)

---

## 快速开始

### 1. 创建示例项目

```bash
# 在当前目录创建示例项目
pyspring init --example

# 或指定项目目录
pyspring init my-project --example
```

### 2. 安装依赖

```bash
cd my-project

# 使用 uv（推荐）
uv sync

# 或使用 pip
pip install -e .
```

### 3. 启动应用

```bash
# 方式 1：使用 uvicorn
uvicorn app.main:app --reload

# 方式 2：直接运行
python -m app.main
```

### 4. 访问应用

- **API 地址**: http://localhost:8000
- **API 文档**: http://localhost:8000/docs
- **健康检查**: http://localhost:8000/health

## 项目特性

创建的示例项目包含以下功能：

### ✅ IOC 容器和依赖注入

- `@component` 装饰器自动注册组件
- `@inject` 装饰器自动依赖注入
- 查看: `app/services/user_service.py`

### ✅ 生命周期管理

- `ILifecycle` 接口
- `on_startup()` 启动初始化器
- `on_shutdown()` 关闭处理器
- 查看: `app/services/user_service.py`

### ✅ 配置管理

- YAML 配置文件
- 环境变量支持
- 多环境配置
- 查看: `config/` 目录

### ✅ 数据库集成

- SQLAlchemy 异步 ORM
- Repository 模式
- 自动初始化
- 查看: `app/database/` 和 `app/repositories/`

### ✅ 缓存服务

- Redis 集成（可选）
- 内存缓存降级
- TTL 支持
- 查看: `app/services/cache_service.py`

### ✅ JWT 认证

- 用户注册/登录
- JWT 令牌生成和验证
- 密码哈希
- 查看: `app/services/auth_service.py`

### ✅ RESTful API

- FastAPI 路由
- 请求验证
- 响应模型
- 查看: `app/api/` 目录

### ✅ 中间件

- 请求日志
- 性能监控
- 全局异常处理
- 查看: `app/middleware/` 目录

### ✅ 结构化日志

- Loguru 日志系统
- 日志轮转
- 多级别输出
- 查看: `config/logging.yaml`

## 默认账户

应用首次启动时会自动创建管理员账户：

- **用户名**: admin
- **密码**: admin123
- **邮箱**: admin@example.com

## API 使用示例

### 健康检查

```bash
curl http://localhost:8000/health
```

### 用户注册

```bash
curl -X POST http://localhost:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "username": "newuser",
    "email": "newuser@example.com",
    "password": "password123"
  }'
```

### 用户登录

```bash
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "username": "admin",
    "password": "admin123"
  }'
```

### 获取当前用户信息

```bash
curl http://localhost:8000/api/users/me \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

## 项目结构

```
my-project/
├── app/                         # 应用代码
│   ├── main.py                  # FastAPI 入口点
│   ├── api/                     # API 路由
│   │   ├── health.py           # 健康检查
│   │   ├── auth.py             # 认证
│   │   └── users.py            # 用户管理
│   ├── services/               # 业务逻辑层
│   │   ├── user_service.py     # 用户服务（带缓存）
│   │   ├── auth_service.py     # 认证服务
│   │   └── cache_service.py    # 缓存服务
│   ├── repositories/           # 数据访问层
│   │   └── user_repository.py  # 用户仓储
│   ├── models/                 # 数据模型
│   │   └── user.py             # 用户模型
│   ├── database/               # 数据库配置
│   │   ├── session.py          # 会话管理
│   │   └── initializer.py      # 初始化器
│   ├── middleware/             # 中间件
│   ├── dependencies/           # FastAPI 依赖
│   └── aspects/                # AOP 切面（可选）
├── config/                     # 配置文件
│   ├── application.yaml        # 应用配置
│   ├── container.yaml          # IOC 容器配置
│   └── logging.yaml            # 日志配置
├── data/                       # 数据目录
├── logs/                       # 日志目录
├── tests/                      # 测试代码
├── pyproject.toml              # 项目配置和依赖
├── .env.example                # 环境变量模板
├── .gitignore                  # Git 忽略文件
└── README.md                   # 项目文档
```

## 学习路径

1. **入门**: 先运行项目，访问 API 文档了解可用接口
2. **IOC 容器**: 阅读 `app/services/user_service.py` 了解依赖注入
3. **生命周期**: 查看 `app/main.py` 了解应用启动/关闭流程
4. **数据访问**: 学习 `app/repositories/user_repository.py` 的 Repository 模式
5. **认证**: 研究 `app/services/auth_service.py` 的 JWT 实现
6. **缓存**: 了解 `app/services/cache_service.py` 的缓存策略
7. **中间件**: 查看 `app/middleware/` 了解请求处理流程

## 重要提示

- ✅ **Redis 可选**: 如果没有 Redis，自动降级为内存缓存
- ✅ **SQLite 默认**: 开箱即用，无需额外配置
- ✅ **完整日志**: 查看 `logs/` 目录的详细日志
- ✅ **可扩展**: 所有组件都可以根据需求修改和扩展

## 常见问题

### 1. 如何更换数据库？

修改 `.env` 文件中的 `DATABASE_URL`:

```bash
# PostgreSQL
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/dbname

# MySQL
DATABASE_URL=mysql+aiomysql://user:password@localhost:3306/dbname
```

### 2. Redis 连接失败怎么办？

不用担心！应用会自动降级为内存缓存，不影响运行。

### 3. 如何添加新的 API 端点？

1. 在 `app/api/` 创建新的路由文件
2. 在 `app/main.py` 中注册路由
3. 参考 `app/api/users.py` 的写法

### 4. 如何添加新的服务？

1. 在 `app/services/` 创建服务类
2. 使用 `@component` 装饰器
3. 使用 `@inject` 进行依赖注入
4. 可选：实现 `ILifecycle` 接口

## 相关文档

- [PySpring 文档](../../docs/)
- [配置最佳实践](../../docs/03-configuration/PYTHON_PROJECT_CONFIG_BEST_PRACTICES.md)
- [IOC 容器指南](../../docs/02-core-concepts/IOC_CONTAINER.md)
- [生命周期管理](../../docs/02-core-concepts/LIFECYCLE_GUIDE.md)

## 反馈和贡献

如果您有任何问题或建议，欢迎：

- 提交 Issue
- 贡献代码
- 完善文档

---

**享受使用 PySpring 构建应用的乐趣！** 🚀
