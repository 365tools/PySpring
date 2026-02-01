# 核心概念 (Core Concepts)

理解 PySpring 的核心设计理念和架构。

## 📚 文档列表

### IoC 容器与依赖注入

- **[IOC_CONTAINER.md](IOC_CONTAINER.md)** ✨ *(Recommended)*
    - IoC 容器深度解析
    - 自动扫描与注册机制
    - **启动加速 (Cache)** 与 **循环依赖防护** (v1.0.1)

- **[AOP_GUIDE.md](AOP_GUIDE.md)** ✨ *(New)*
    - AOP 切面编程指南
    - Before/After/Around 通知的使用

- **[IOC_SINGLETON_GUIDE.md](IOC_SINGLETON_GUIDE.md)**
    - 单例模式的设计思考
    - 结合 `ContextVars` 的并发安全实现
    - 为什么你不需要 Prototype Scope？

### 旧版文档 (Reference)

- [IOC_CONFIG_GUIDE.md](IOC_CONFIG_GUIDE.md) (Container Config Ref)

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
- **工厂模式** - ApplicationContext 服务容器
- **责任链模式** - 认证链、初始化链
- **策略模式** - 缓存策略、认证策略

## 📖 相关文档

- 配置管理：[../03-configuration/](../03-configuration/)
- 功能模块：[../04-features/](../04-features/)
- 入门指南：[../01-getting-started/](../01-getting-started/)
