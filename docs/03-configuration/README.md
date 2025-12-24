# 配置指南 (Configuration)

PySpring 的配置系统使用 YAML 文件，提供统一的配置管理。

## 📚 文档列表

### 配置架构

- **[CONFIG_ARCHITECTURE.md](CONFIG_ARCHITECTURE.md)** - 配置文件职责划分
    - 各配置文件的职责范围
    - 配置项分类说明
    - 配置文件之间的关系

### 应用配置

- **[APPLICATION_CONFIG_GUIDE.md](APPLICATION_CONFIG_GUIDE.md)** - 应用和服务器配置
    - 应用基本信息
    - 服务器配置
    - API 配置
    - 监控配置

### 功能模块配置

- **[LOGGING_CONFIG_GUIDE.md](LOGGING_CONFIG_GUIDE.md)** - 日志系统配置
    - 日志级别设置
    - 控制台输出配置
    - 文件日志配置
    - 日志过滤器

- **[REPOSITORIES_CONFIG_GUIDE.md](REPOSITORIES_CONFIG_GUIDE.md)** - 数据存储配置
    - 数据库配置（PostgreSQL/SQLite）
    - Redis 配置
    - 缓存策略配置
    - 连接池管理

- **[SECURITY_CONFIG_GUIDE.md](SECURITY_CONFIG_GUIDE.md)** - 安全配置
    - JWT 认证配置
    - RBAC 权限配置
    - CORS 跨域配置
    - 白名单配置
    - 限流配置

## 📁 配置文件概览

```
config/
├── application.yaml       # 应用和服务器基础配置
├── container.yaml         # IoC 容器和依赖注入
├── logging.yaml           # 日志系统配置
├── repositories.yaml      # 数据存储配置
└── security.yaml          # 安全和认证配置
```

## 🎯 配置原则

1. **职责单一** - 每个配置文件负责特定领域
2. **配置驱动** - 通过配置控制框架行为
3. **环境隔离** - 支持多环境配置
4. **合理默认** - 提供开箱即用的默认配置

## 📖 相关文档

- 核心概念：[../02-core-concepts/](../02-core-concepts/)
- 功能模块：[../04-features/](../04-features/)
- 故障排除：[../06-troubleshooting/](../06-troubleshooting/)
