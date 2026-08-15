# 🚀 PySpring 示例项目快速参考

## ⚡ 零配置快速开始（推荐）

**使用 `uvx`（无需预安装 PySpring）**：

```bash
# 1. 安装 uv（如果还没有）
pip install uv

# 2. 创建项目（自动使用最新版 PySpring）
uvx --from pyspring pyspring init my-project --example

# 3. 进入项目并运行
cd my-project
uv sync
uv run uvicorn app.main:app --reload
```

## 📦 传统方式（已安装 PySpring）

```bash
pyspring init my-project --example
cd my-project
uv sync
uv run uvicorn app.main:app --reload
```

💡 **首次使用？** 查看 [安装指南](./INSTALLATION_GUIDE.md)

## 访问地址

| 服务   | URL                          |
|------|------------------------------|
| API  | http://localhost:8000        |
| 文档   | http://localhost:8000/docs   |
| 健康检查 | http://localhost:8000/health |

## 默认账户

```
用户名: admin
密码: admin123
```

## API 快速测试

### 1. 健康检查

```bash
curl http://localhost:8000/health
```

### 2. 用户登录

```bash
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123"}'
```

### 3. 获取用户信息

```bash
# 先登录获取 token，然后：
curl http://localhost:8000/api/users/me \
  -H "Authorization: Bearer YOUR_TOKEN"
```

## 核心功能位置

| 功能     | 文件                                    |
|--------|---------------------------------------|
| 应用入口   | `app/main.py`                         |
| IOC 示例 | `app/services/user_service.py`        |
| 生命周期   | `app/database/initializer.py`         |
| 认证     | `app/services/auth_service.py`        |
| 数据库    | `app/repositories/user_repository.py` |
| 缓存     | `app/services/cache_service.py`       |
| 中间件    | `app/middleware/`                     |
| API 路由 | `app/api/`                            |

## 10 个展示的功能

1. ✅ IOC 容器 - `@component` + `@inject`
2. ✅ 生命周期 - `ILifecycle`
3. ✅ 配置管理 - YAML + 环境变量
4. ✅ 数据库 - SQLAlchemy async
5. ✅ Repository - 数据访问层
6. ✅ 缓存 - Redis + 降级
7. ✅ JWT 认证 - 登录/注册
8. ✅ RESTful API - FastAPI
9. ✅ 中间件 - 日志/监控
10. ✅ 结构化日志 - Loguru

## 常用命令

```bash
# 启动应用
uv run uvicorn app.main:app --reload

# 运行测试
uv run pytest tests/

# 查看日志
tail -f logs/app_*.log

# 数据库迁移（如需）
# alembic init alembic
# alembic revision --autogenerate -m "init"
# alembic upgrade head
```

## 配置文件

| 文件                        | 用途         |
|---------------------------|------------|
| `.env`                    | 环境变量（敏感信息） |
| `config/application.yaml` | 应用配置       |
| `config/container.yaml`   | IOC 容器配置   |
| `config/logging.yaml`     | 日志配置       |

## 依赖包

使用 `uv` 管理依赖，所有依赖在 `pyproject.toml` 中定义：

```toml
pyspring       # 核心框架
fastapi        # Web 框架
sqlalchemy     # ORM
aiosqlite      # SQLite 异步驱动
redis          # Redis 客户端（可选）
pyjwt          # JWT 令牌
passlib        # 密码哈希
loguru         # 日志
```

## 项目结构速览

```
my-project/
├── app/              # 应用代码
│   ├── main.py      # 入口点
│   ├── api/         # API 路由
│   ├── services/    # 业务逻辑
│   ├── repositories/# 数据访问
│   └── models/      # 数据模型
├── config/          # 配置文件
├── tests/           # 测试代码
└── pyproject.toml   # 项目配置
```

## 学习顺序

1. 🏁 运行项目 → 访问 /docs
2. 📖 阅读 `app/main.py`
3. 🔧 学习 `app/services/user_service.py`
4. 💾 研究 `app/repositories/user_repository.py`
5. 🔐 了解 `app/services/auth_service.py`
6. 🎯 实践：添加新功能

## 帮助资源

- 📚 [完整指南](../../docs/01-getting-started/EXAMPLE_PROJECT_GUIDE.md)
- 📘 [配置最佳实践](../../docs/03-configuration/PYTHON_PROJECT_CONFIG_BEST_PRACTICES.md)
- 📙 [IOC 容器](../../docs/02-core-concepts/IOC_CONTAINER.md)

---

💡 **提示**: 所有代码都有详细注释，直接阅读源码是最好的学习方式！
