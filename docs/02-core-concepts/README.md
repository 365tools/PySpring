# 核心概念 (Core Concepts)

理解 PySpring 的核心设计理念和架构。

## 📚 文档列表

### IoC 容器与依赖注入

- **[IOC_SINGLETON_GUIDE.md](IOC_SINGLETON_GUIDE.md)** - IoC 容器使用与单例服务管理
    - IoC 容器基础
    - 单例服务生命周期
    - 自动依赖注入
    - 服务发现机制

- **[IOC_CONFIG_GUIDE.md](IOC_CONFIG_GUIDE.md)** - IoC 容器配置详解
    - container.yaml 配置
    - 自动扫描配置
    - 服务注册规则

### 项目架构

- **[PROJECT_STRUCTURE.md](PROJECT_STRUCTURE.md)** - 项目结构说明
    - 框架目录结构
    - 模块职责划分
    - 代码组织原则

## 🎯 核心特性

### IoC 容器

类似 Spring Framework 的 ApplicationContext，PySpring 提供：

- 自动扫描和注册（Service、Handler、Initializer）
- 类型注解依赖注入
- 接口映射和服务发现
- 单例生命周期管理

### 设计模式

- **单例模式** - ISingletonService 接口
- **工厂模式** - AppContainerManager 服务容器
- **责任链模式** - 认证链、初始化链
- **策略模式** - 缓存策略、认证策略

## 📖 相关文档

- 配置管理：[../03-configuration/](../03-configuration/)
- 功能模块：[../04-features/](../04-features/)
- 入门指南：[../01-getting-started/](../01-getting-started/)
