# PySpring 配置文件说明

## 📁 配置文件结构

### 1. 框架级配置（Framework Level）
**位置：** `src/pyspring/config/`  
**维护者：** 框架开发者  
**用户权限：** 🚫 不可编辑（打包到框架内部）

```
src/pyspring/config/
├── framework.yaml          # 框架核心配置
└── defaults/               # 框架默认值（可被用户覆盖）
    ├── security.yaml       # 安全模块默认配置
    ├── repositories.yaml   # 数据仓储模块默认配置（数据库+缓存）
    └── logging.yaml        # 日志模块默认配置
```

### 2. 用户项目配置（User Project Level）
**位置：** `<your_project>/config/`  
**维护者：** 用户  
**用户权限：** ✅ 完全可编辑

```
your_project/config/
├── application.yaml        # 应用基本信息、服务器配置
├── security.yaml          # 安全配置（覆盖框架默认）
├── repositories.yaml      # 数据仓储配置（覆盖框架默认）
└── logging.yaml           # 日志配置（覆盖框架默认）
```

### 3. 配置模板（Templates）
**位置：** `src/pyspring/templates/example/config/`  
**用途：** 示例项目配置（生成新项目时复制）

```
src/pyspring/templates/example/config/
├── application.yaml.template
├── security.yaml.template
├── repositories.yaml.template
└── logging.yaml.template
```

## 🔄 配置加载顺序

```
1️⃣ 框架默认配置 (src/pyspring/config/defaults/)
   ↓ 加载
2️⃣ 用户项目配置 (<project>/config/)
   ↓ 深度合并（用户配置覆盖框架默认）
3️⃣ 环境变量 (JWT_SECRET_KEY, POSTGRES_PASSWORD 等)
   ↓ 覆盖
4️⃣ 最终配置
```

**示例：**
```yaml
# 框架默认值 (src/pyspring/config/defaults/security.yaml)
authentication:
  jwt:
    access_token_expire: 3600  # 1小时

# 用户配置 (config/security.yaml)
authentication:
  jwt:
    access_token_expire: 7200  # 覆盖为2小时

# 环境变量
JWT_SECRET_KEY=my_secret  # 最高优先级

# 最终结果
authentication:
  jwt:
    access_token_expire: 7200     # 来自用户配置
    secret_key: "my_secret"       # 来自环境变量
    algorithm: "HS256"            # 来自框架默认（未被覆盖）
```

## 🎯 配置管理器

### ConfigManager（统一配置管理）

```python
from pyspring.config_manager import ConfigManager

# 加载配置（自动合并框架默认值和用户配置）
config = ConfigManager.load_config("security")

# 便捷函数
from pyspring.config_manager import (
    load_security_config,
    load_repositories_config,
    load_logging_config
)

security_config = load_security_config()
repositories_config = load_repositories_config()
logging_config = load_logging_config()
```

### 各模块配置管理器

| 配置管理器                       | 配置文件              | 状态    | 说明               |
|-----------------------------|-------------------|-------|------------------|
| `SecurityConfigManager`     | security.yaml     | ✅ 已更新 | 使用 ConfigManager |
| `RepositoriesConfigManager` | repositories.yaml | ✅ 已更新 | 使用 ConfigManager |
| `LoggingConfigManager`      | logging.yaml      | ✅ 已更新 | 使用 ConfigManager |

## 🛠️ 用户使用指南

### 创建用户配置

用户只需在项目的 `config/` 目录下创建配置文件，**只配置要覆盖的值**：

```yaml
# config/security.yaml
# 只配置需要修改的值，其他使用框架默认

authentication:
  jwt:
    access_token_expire: 7200  # 覆盖为2小时

password:
  min_length: 10  # 覆盖为10位
```

未配置的项自动使用框架默认值。

### 环境变量覆盖

支持的环境变量：

**安全配置 (security.yaml):**
- `JWT_SECRET_KEY` - JWT 密钥
- `JWT_ENCRYPTION_KEY` - JWT 加密密钥
- `JWT_ALGORITHM` - JWT 算法
- `ACCESS_TOKEN_EXPIRE` - Token 过期时间
- `REFRESH_TOKEN_EXPIRE` - Refresh Token 过期时间

**数据仓储配置 (repositories.yaml):**
- `POSTGRES_PASSWORD` - PostgreSQL 密码
- `MYSQL_PASSWORD` - MySQL 密码
- `REDIS_PASSWORD` - Redis 密码

## 📝 配置结构

```
src/pyspring/config/
├── framework.yaml          # 框架核心
└── defaults/              # 框架默认值
    ├── security.yaml
    ├── database.yaml
    └── logging.yaml

<project>/config/          # 用户配置
├── security.yaml          # 只配置要覆盖的值
└── database.yaml
```

用户配置文件只需保留要覆盖的配置项，其余由 `ConfigManager` 自动合并框架默认值。

## ✅ 测试验证

运行配置架构测试：

```bash
python -m pytest tests/unit/config/test_config_architecture.py -v
```

测试覆盖：
- ✅ 框架默认配置加载
- ✅ 用户配置覆盖框架默认
- ✅ 深度合并嵌套配置
- ✅ 环境变量覆盖
- ✅ 配置缓存机制
- ✅ 边界情况处理

## 🎉 优势

### 对比旧架构

| 特性   | 旧架构       | 新架构            |
|------|-----------|----------------|
| 配置层次 | ❌ 混乱      | ✅ 清晰（框架/默认/用户） |
| 配置覆盖 | ❌ 无机制     | ✅ 深度合并 + 环境变量  |
| 用户体验 | ❌ 不知道哪些能改 | ✅ 只配置要覆盖的值     |
| 错误处理 | ⚠️  易出错   | ✅ 优雅降级         |
| 性能   | ⚠️  重复加载  | ✅ 配置缓存         |

### 核心优势

1. **清晰的配置层次** - 框架级/默认值/用户级分离
2. **灵活的配置覆盖** - 深度合并 + 环境变量支持
3. **优秀的用户体验** - 只需配置要修改的值
4. **健壮的错误处理** - 优雅降级，不影响系统运行
5. **高效的性能** - 配置缓存机制

## 📚 相关文档

- [配置架构分析](docs/CONFIG_ARCHITECTURE_ANALYSIS.md) - 详细的设计文档
- [测试报告](tests/unit/config/TEST_CONFIG_ARCHITECTURE_REPORT.md) - 测试结果
- [CHANGELOG](CHANGELOG.md) - 版本更新记录

---

**最后更新：** 2026-01-24  
**版本：** 1.1.0b21
