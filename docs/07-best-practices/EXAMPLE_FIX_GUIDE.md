# Example 项目修复指南

## 问题说明

扫描器报错：`function() argument 'code' must be code, not str`

**根本原因**：您的 example 项目文件是从旧模板生成的，缺少必要的 `@Component` 装饰器。

## 解决方案

### 方案1：重新生成 example 项目（推荐）

如果您的 example 项目中没有重要的自定义代码，最简单的方法是重新生成：

```powershell
# 1. 删除旧的 example 项目
Remove-Item -Recurse -Force example_project

# 2. 重新安装最新版本的 PySpring
pip install --upgrade .

# 3. 重新生成 example 项目
pyspring init example_project
cd example_project
pyspring db init
pyspring run
```

### 方案2：手动修复现有文件

如果您想保留现有的 example 项目，需要手动添加装饰器：

#### 1. 修复 `app/services/custom_login_provider.py`

在文件顶部添加导入：

```python
from pyspring.core.ioc.annotations.component import Component
```

在类定义前添加装饰器：

```python
@Component
class CustomPasswordLoginProvider(DefaultPasswordLoginProvider): ...
```

#### 2. 修复 `app/services/custom_register_service.py`

确认文件顶部有导入（应该已经有了）：

```python
from pyspring.core.ioc.annotations.component import Component
```

确认类定义前有装饰器：

```python
@Component
class CustomRegisterService(DefaultRegisterService): ...
```

#### 3. 如果您自定义了 `app/config/security_config.py`

如果您定义了自定义的 `CustomSecurityEntityConfiguration`，需要添加：

```python
from pyspring.core.ioc.annotations.component import Component


@Component
class CustomSecurityEntityConfiguration(SecurityEntityConfiguration): ...
```

## 验证修复

修复后，重新运行：

```powershell
pyspring run
```

应该不再出现扫描错误，并且能看到：

```
📦 发现组件: CustomPasswordLoginProvider (app.services.custom_login_provider)
📦 发现组件: CustomRegisterService (app.services.custom_register_service)
```

## 为什么需要 @Component 装饰器？

框架的组件扫描器需要明确的标记来识别哪些类应该被管理：

1. **@Component 装饰器**：告诉扫描器"这是一个组件，请注册我"
2. **继承 + @Component**：子类会替换父类（如果父类有 @ConditionalOnMissingBean）

**错误的理解**（旧模板）：

- ❌ "继承就能自动替换父类，无需装饰器"

**正确的理解**（新模板）：

- ✅ "继承 + @Component = 替换父类"
- ✅ "扫描器必须看到 @Component 才能识别组件"
- ✅ "父类有 @ConditionalOnMissingBean，子类有 @Component，实现替换"

## 更新日志

- 修复模板，所有自定义组件必须使用 @Component 装饰器
- 改进扫描器错误处理，提供更清晰的错误信息
