# PySpring 文档中心

欢迎查阅 PySpring 官方文档。本文档体系旨在帮助您从零开始掌握这个企业级 Python 框架。

## 📚 文档目录

### 1. 快速开始 (Getting Started)

- [新手入门指南](01-getting-started/README.md)
- [安装与环境配置](01-getting-started/INSTALLATION_GUIDE.md)
- [5分钟快速上手](01-getting-started/QUICK_REFERENCE.md)
- [项目初始化向导](01-getting-started/PROJECT_INIT_GUIDE.md)

### 2. 核心架构 (Core Concepts) ✨ *(重点更新 v1.0.1)*

- **[IoC 容器深度解析](02-core-concepts/IOC_CONTAINER.md)**: 了解依赖注入、启动加速与循环依赖防护。
- **[AOP 切面编程](02-core-concepts/AOP_GUIDE.md)**: 如何使用切面解耦业务逻辑。
- [单例与并发上下文](02-core-concepts/IOC_SINGLETON_GUIDE.md): 深入理解高并发下的状态管理。
- [标准项目结构](02-core-concepts/PROJECT_STRUCTURE.md): 目录结构的最佳实践。

### 3. 配置管理 (Configuration)

- [配置架构概览](03-configuration/CONFIG_ARCHITECTURE.md)
- [应用配置指南](03-configuration/APPLICATION_CONFIG_GUIDE.md)
- [安全配置指南](03-configuration/SECURITY_CONFIG_GUIDE.md)

### 4. 功能特性 (Features)

- [认证与安全](04-features/JWT_ENCRYPTION_GUIDE.md): JWT、加密与安全链。
- [数据库自动初始化](04-features/DATABASE_AUTO_INIT.md)
- [模板管理](04-features/TEMPLATE_MANAGEMENT.md)

### 5. 进阶指南 (Advanced)

- [UV 包管理器集成](05-advanced/SETUP_WITH_UV.md)
- [已有项目迁移指南](05-advanced/INSTALLATION_OTHER_PROJECT.md)
- [安全迁移指南](05-advanced/SECURITY_MIGRATION_GUIDE.md)

### 6. 故障排查 (Troubleshooting)

- [常见问题诊断](06-troubleshooting/DIAGNOSE_GUIDE.md)
- [依赖注入问题排查](06-troubleshooting/FIX_UNRESOLVED_REFERENCE.md)
- [数据库问题](06-troubleshooting/SQL_ISSUES.md)

- IoC 容器与依赖注入
- 单例服务管理
- 项目结构

### ⚙️ [03 - 配置指南](03-configuration/)

掌握 PySpring 的配置系统和各模块配置方法。

- 配置文件架构
- 应用配置
- 日志/存储/安全配置

### ✨ [04 - 功能模块](04-features/)

探索 PySpring 提供的核心功能。

- JWT 加密
- 数据库自动初始化
- 模板系统

### 🎓 [05 - 高级主题](05-advanced/)

深入学习框架集成、迁移和工具链。

- 框架迁移指南
- 项目集成
- uv 包管理器

### 🔧 [06 - 故障排除](06-troubleshooting/)

常见问题诊断和解决方案。

- 诊断工具
- IDE 配置问题
- SQL 问题修复

## 🎯 按场景查找

### 我想...

- **快速开始项目** → [项目初始化指南](PROJECT_INIT_GUIDE.md) → [快速参考](QUICK_REFERENCE.md)
- **创建新项目** → [Init 快速参考](INIT_QUICK_REF.md) → [项目初始化指南](PROJECT_INIT_GUIDE.md)

## 🎯 快速导航

### 常见任务

- **配置认证系统** → [03-configuration/SECURITY_CONFIG_GUIDE.md](03-configuration/SECURITY_CONFIG_GUIDE.md)
- **使用数据库** → [03-configuration/REPOSITORIES_CONFIG_GUIDE.md](03-configuration/REPOSITORIES_CONFIG_GUIDE.md)
- **配置日志** → [03-configuration/LOGGING_CONFIG_GUIDE.md](03-configuration/LOGGING_CONFIG_GUIDE.md)
- **使用单例服务** → [02-core-concepts/IOC_SINGLETON_GUIDE.md](02-core-concepts/IOC_SINGLETON_GUIDE.md)
- **配置 JWT 加密** → [04-features/JWT_ENCRYPTION_GUIDE.md](04-features/JWT_ENCRYPTION_GUIDE.md)

## 📖 推荐阅读路径

### 🌱 新用户路径

1. [01-getting-started/INSTALLATION_GUIDE.md](01-getting-started/INSTALLATION_GUIDE.md) - 安装框架
2. [01-getting-started/PROJECT_INIT_GUIDE.md](01-getting-started/PROJECT_INIT_GUIDE.md) - 初始化项目
3. [02-core-concepts/IOC_SINGLETON_GUIDE.md](02-core-concepts/IOC_SINGLETON_GUIDE.md) - 理解核心概念
4. [03-configuration/](03-configuration/) - 学习配置系统

### 🚀 进阶用户路径

1. [02-core-concepts/IOC_CONFIG_GUIDE.md](02-core-concepts/IOC_CONFIG_GUIDE.md) - 深入容器配置
2. [04-features/JWT_ENCRYPTION_IMPLEMENTATION.md](04-features/JWT_ENCRYPTION_IMPLEMENTATION.md) - 了解加密原理
3. [05-advanced/](05-advanced/) - 探索高级主题

### 🔄 迁移用户路径

1. [05-advanced/SECURITY_MIGRATION_GUIDE.md](05-advanced/SECURITY_MIGRATION_GUIDE.md) - 框架迁移
2. [05-advanced/INSTALLATION_OTHER_PROJECT.md](05-advanced/INSTALLATION_OTHER_PROJECT.md) - 项目集成

## 💡 获取帮助

### 遇到问题？

1. 查看 [06-troubleshooting/](06-troubleshooting/) 故障排除文档
2. 运行诊断工具：`pyspring diagnose`
3. 查看 [GitHub Issues](https://github.com/365tools/PySpring/issues)
4. 加入社区讨论

### 文档反馈

欢迎通过 Issue 或 PR 帮助改进文档！

---

**💡 提示**: 从 [01-getting-started/](01-getting-started/) 开始，循序渐进掌握 PySpring！
