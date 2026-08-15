# PySpring 文档

欢迎来到 PySpring 框架的官方文档！

PySpring 是一个基于 FastAPI 的、受 Spring Boot 启发的高级 Python Web 框架，采用 **Starter 化** 与 **PEP 420 命名空间包** 架构。

## 文档结构

PySpring 的文档按照"整体到局部"的原则进行组织：

### [00-架构设计](00-architecture/)
- 整体架构与模块化方案
- 模块清单与职责
- 开发规范（PEP 420 命名空间包、Starter 规范）
- 清理方案与 check 修复计划

### [01-入门指南](01-getting-started/)
- 快速开始
- 安装指南
- 项目初始化
- CLI 工具使用

### [02-核心概念](02-core-concepts/)
- IoC 容器详解
- AOP 切面编程
- 依赖注入机制
- 项目结构规范

### [03-配置管理](03-configuration/)
- 应用配置
- 安全配置
- 数据库配置
- 日志配置
- 配置架构指南

### [04-功能特性](04-features/)
- 认证与授权
- JWT 加密
- 数据库集成
- 控制器安全
- 标识符登录

### [05-高级主题](05-advanced/)
- 部署指南
- UV 环境配置

### [06-故障排除](06-troubleshooting/)
- 常见问题
- 诊断指南
- 解决方案

### [07-最佳实践](07-best-practices/)
- 示例修复指南
- 缓存清理指南
- 实用技巧

## 快速导航

- [开始使用](01-getting-started/README.md)
- [核心架构](00-architecture/00-ARCHITECTURE.md)
- [测试与 pytest-xdist 并行实践](00-architecture/03-TESTING.md)
- [IoC 容器](02-core-concepts/IOC_CONTAINER.md)
- [配置详解](03-configuration/CONFIG_ARCHITECTURE.md)
- [故障排除](06-troubleshooting/DIAGNOSE_GUIDE.md)
- [最佳实践](07-best-practices/)
- [文档汇总](SUMMARY.md)
- [快速入门](QUICK_START.md)

## 推荐阅读顺序

1. **架构概览**：从 [架构设计](00-architecture/00-ARCHITECTURE.md) 了解整体分层与 Starter 机制。
2. **快速上手**：通过 [快速入门](QUICK_START.md) 创建一个项目。
3. **核心概念**：深入 [IoC 容器](02-core-concepts/IOC_CONTAINER.md) 与 AOP。
4. **按需深入**：根据功能需求查阅 [功能特性](04-features/) 与 [配置管理](03-configuration/)。
5. **问题排查**：遇到问题时查阅 [故障排除](06-troubleshooting/)。
