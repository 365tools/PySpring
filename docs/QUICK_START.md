# PySpring 快速入门指南

## 什么是PySpring？

PySpring是一个基于FastAPI构建的现代化Python Web框架，深受Spring Boot设计哲学启发。它通过控制反转(IoC)、依赖注入(DI)和约定优于配置的原则，帮助开发者构建可扩展、易维护的后端应用。

## 快速安装

### 临时使用（推荐新手）
```bash
# 使用 uvx 零安装快速创建项目
uvx --from pyspring pyspring init my-project --example
cd my-project
```

### 开发环境安装
```bash
# 使用 pipx（推荐，隔离安装）
pipx install pyspring

# 或使用 uv tool（现代化）
uv tool install pyspring
```

### 生产环境安装
```bash
# 标准安装
pip install pyspring
```

## 快速创建项目

```bash
# 初始化项目
pyspring init

# 项目结构
your-project/
├── app/                  # 业务代码
│   ├── api/              # 路由接口 (Controller)
│   ├── services/         # 业务逻辑 (Service)
│   ├── handlers/         # 生命周期处理器 (Handler)
│   └── models/           # 数据实体
├── config/               # 配置文件 (YAML)
│   ├── application.yaml  # 应用全局配置
│   ├── container.yaml    # IoC 容器扫描路径配置
│   ├── security.yaml     # 安全策略与白名单
│   └── repositories.yaml # 数据库源与缓存配置
├── logs/                 # 运行日志
├── scripts/              # 维护脚本
├── main.py               # 应用入口
└── .env                  # 敏感变量
```

## 核心功能示例

### 1. IoC 容器和依赖注入

定义服务：
```python
from pyspring.core.ioc import Component


@Component  # 自动注册到 IoC 容器，默认单例
class UserService:
    # 类型提示触发自动注入
    def __init__(self, db_manager: "DBManagerService"):
        self.db = db_manager

    def get_users(self):
        return self.db.query("SELECT * FROM users")
```

使用服务：
```python
from pyspring.core.ioc import ApplicationContext
from app.services.user_service import UserService

# 需先初始化应用上下文
app_context = ApplicationContext.initialize(base_packages=["app"])

user_service = app_context.get_by_type(UserService)

users = user_service.get_users()
```

### 2. 认证和授权

使用内置的认证装饰器：
```python
from pyspring.security.authentication.web.middleware.dependencies import (
    require_authentication_from_token,
    permission_dependency,
    role_dependency,
)
from fastapi import Depends
from typing import Annotated

# 需要认证
AuthenticatedUser = Annotated[Any, Depends(require_authentication_from_token)]

# 需要特定权限
UserReadPermission = Annotated[Any, Depends(permission_dependency("user:read"))]

# 需要特定角色
AdminOnly = Annotated[Any, Depends(role_dependency("admin"))]


@app.get("/api/users")
async def list_users(user: UserReadPermission):
    # 只有拥有 user:read 权限的用户才能访问
    pass
```

### 3. 多字段登录

支持使用多种标识符登录：
```python
# 配置支持的登录字段
# config/security.yaml
authentication:
  identifier_fields:
    - "user_id"    # 用户ID
    - "username"   # 用户名
    - "email"      # 邮箱
    - "phone"      # 手机号
```

API请求示例：
```bash
# 使用邮箱登录
curl -X POST /api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"identifier": "admin@example.com", "password": "admin123"}'

# 使用用户名登录
curl -X POST /api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"identifier": "admin", "password": "admin123"}'
```

## 常用配置

### 安全配置示例
```yaml
# config/security.yaml
authentication:
  jwt:
    secret_key: ${JWT_SECRET_KEY:your-secret-key-here}
    access_token_expire: 3600
    refresh_token_expire: 2592000
  identifier_fields:
    - "user_id"
    - "username"
    - "email"
    - "phone"
  providers:
    password:
      enabled: true
      encoder: bcrypt
      strength: 12
```

### 容器配置示例
```yaml
# config/container.yaml
container:
  scan_cache: true        # 开启启动缓存
  lazy_loading: true      # 懒加载模式

scan:
  packages:
    - app.services
    - app.controllers
    - app.repositories
```

## 故障排除

### 常用诊断命令
```bash
# 检查项目健康（循环依赖、导入、编码、版本一致性）
pyspring check

# 查看版本信息
pyspring --version
```

### 常见问题
1. **循环依赖**: 使用 `@Lazy` 或重构代码解耦
2. **IDE引用错误**: 检查虚拟环境和Python解释器配置
3. **配置加载失败**: 验证YAML语法和路径

## 进一步学习

- [入门指南](01-getting-started/) - 详细安装和配置说明
- [核心概念](02-core-concepts/) - IoC容器、AOP等核心功能
- [配置管理](03-configuration/) - 配置文件详解
- [功能特性](04-features/) - 认证、授权等高级功能
- [故障排除](06-troubleshooting/) - 问题诊断和解决方案
- [最佳实践](07-best-practices/) - 项目优化建议

## CLI命令速查

- `pyspring init` - 初始化新项目
- `pyspring check` - 检查项目健康（循环依赖、导入、编码）
- `pyspring dev` - 开发工作流辅助
- `pyspring clean` - 清理缓存与构建产物
- `pyspring security` - 安全相关检查
- `pyspring uv` - 封装 uv 环境管理
- `pyspring --help` - 查看帮助信息

## 核心优势

- **企业级特性**: 完整的IoC容器、AOP、安全体系
- **高性能**: 优化的启动时间和内存使用
- **易用性**: 约定优于配置，快速上手
- **可扩展性**: 模块化设计，易于扩展
- **生产就绪**: 包含日志、健康检查、错误处理等生产特性

开始使用PySpring，构建您的下一代Python Web应用！