# PySpring Core模块重构计划

## 当前问题分析

### 1. 废弃的接口

- `ISingletonService` - 已被 `@Singleton` 装饰器替代
- `IService` - 基础服务接口，功能被 `IManaged` 替代
- `IComponent` - 组件接口，功能被 `@Component` 替代
- `ISystemService` - 系统服务接口，可能冗余

### 2. 生命周期接口

- `IStartupInitializer` - 已在新IOC中重新实现（兼容层）
- `IShutdownHandler` - 已在新IOC中重新实现（兼容层）

## 重构方案

### 保留的内容

1. **abstracts/config.py** - 配置抽象，可能有用
2. **abstracts/exceptions.py** - 异常定义，保留

### 移除的内容

1. **abstracts/interfaces/ISingleton.py** - 删除
2. **abstracts/interfaces/IService.py** - 删除
3. **abstracts/interfaces/IComponent.py** - 删除
4. **abstracts/interfaces/ISystemService.py** - 删除
5. **abstracts/interfaces/handler/** - 移动到 ioc/lifecycle
6. **abstracts/interfaces/initializer/** - 移动到 ioc/lifecycle

### 新增内容

1. 创建统一的异常体系
2. 创建配置管理基类

## 实施步骤

1. ✅ 分析当前结构
2. ⏳ 移除废弃接口
3. ⏳ 移动生命周期接口到IOC
4. ⏳ 整理异常和配置
5. ⏳ 更新所有引用
