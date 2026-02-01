# 功能模块 (Features)

PySpring 提供的核心功能模块详细说明。

## 📚 文档列表

### 认证与授权

- **[AUTH_ARCHITECTURE.md](AUTH_ARCHITECTURE.md)** - 认证架构设计
    - 安全框架概述
    - 认证流程
    - 权限模型

- **[AUTH_AUTHORIZATION_INTEGRATION_GUIDE.md](AUTH_AUTHORIZATION_INTEGRATION_GUIDE.md)** - 认证授权集成指南
    - 完整集成示例
    - 依赖关系
    - 实现细节

- **[AUTH_LOGIN_IDENTIFIER_CONFIG.md](AUTH_LOGIN_IDENTIFIER_CONFIG.md)** - 标识符登录配置
    - 多字段登录支持
    - 配置方法
    - 使用示例

- **[identifier-login-guide.md](identifier-login-guide.md)** - 标识符登录使用指南
    - identifier字段详解
    - 登录实现方式
    - 配置选项

### JWT 加密

- **[JWT_ENCRYPTION_GUIDE.md](JWT_ENCRYPTION_GUIDE.md)** - JWT Token 加密使用指南
    - JWT 加密配置
    - 加密算法选择（Fernet/AES-GCM）
    - 密钥生成和管理
    - 使用示例

- **[JWT_ENCRYPTION_IMPLEMENTATION.md](JWT_ENCRYPTION_IMPLEMENTATION.md)** - JWT 加密底层实现原理
    - 加密流程详解
    - 性能优化
    - 安全考虑
    - 技术实现细节

### 数据库管理

- **[DATABASE_AUTO_INIT.md](DATABASE_AUTO_INIT.md)** - 数据库自动初始化
    - 应用启动时自动创建表
    - 增量模式 vs 完整模式
    - SQL 脚本管理
    - 初始化器配置

### 模板系统

- **[TEMPLATE_MANAGEMENT.md](TEMPLATE_MANAGEMENT.md)** - 项目模板系统
    - 模板文件管理
    - 自定义模板
    - 模板同步
    - 模板验证

## 🎯 功能特性

### 🛡️ 安全认证

- JWT Token 加密保护
- 责任链认证架构
- RBAC 权限模型
- 多字段登录支持

### 💾 数据存储

- 统一缓存层（Memory/Redis）
- 多数据库支持（PostgreSQL/SQLite）
- 连接池自动管理
- 服务降级机制

### 📝 日志系统

- Loguru 集成
- 结构化日志
- 自动轮转
- 彩色输出

### 🚀 启动管理

- 启动初始化器
- 数据库自动初始化
- 配置验证
- 健康检查

## 📖 相关文档

- 配置指南：[../03-configuration/](../03-configuration/)
- 核心概念：[../02-core-concepts/](../02-core-concepts/)
- 高级主题：[../05-advanced/](../05-advanced/)