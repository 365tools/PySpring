# PySpring 系统重构执行方案

## 重构策略

考虑到模块数量多、依赖关系复杂，采用以下策略：

### 阶段划分

#### 第一阶段：基础设施（已完成）

- ✅ IOC框架重构
- ✅ Log模块基础重构

#### 第二阶段：核心抽象清理（当前）

- ⏳ 移除废弃接口
- ⏳ 迁移生命周期接口
- ⏳ 保留必要的配置和异常

#### 第三阶段：模块逐个重构

按依赖关系顺序重构：

1. aop - AOP框架
2. repositories - 数据访问层
3. security - 安全框架
4. templates - 模板系统
5. web - Web框架

## 当前任务：Core模块清理

### 需要删除的文件

```
core/abstracts/interfaces/ISingleton.py
core/abstracts/interfaces/IService.py
core/abstracts/interfaces/IComponent.py
core/abstracts/interfaces/ISystemService.py
```

### 需要移动的文件

```
core/abstracts/interfaces/handler/* → 已在ioc/lifecycle/shutdown.py
core/abstracts/interfaces/initializer/* → 已在ioc/lifecycle/initializer.py
```

### 保留并优化的文件

```
core/abstracts/config.py - 配置基类
core/abstracts/exceptions.py - 异常定义
```

## 执行计划

由于文件数量众多（security模块约40+文件），建议：

1. **先完成Core清理**（快速，影响最大）
2. **创建迁移脚本**（批量更新import语句）
3. **逐模块测试**（确保功能正常）

## 风险控制

- 每个模块重构后立即测试
- 保留Git提交点以便回滚
- 先处理小模块（aop, templates）
- 最后处理大模块（security, web）

## 建议

考虑到工作量，建议分批进行：

- **今天**: 完成Core清理 + aop重构
- **后续**: 逐个重构其他模块

是否继续完成Core模块清理？
