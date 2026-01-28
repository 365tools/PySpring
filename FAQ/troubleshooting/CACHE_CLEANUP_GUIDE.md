# 修复建议：清除 Python 缓存文件

## 问题分析

错误信息 `function() argument 'code' must be code, not str` 非常罕见，通常发生在：

1. **字节码缓存损坏**：`.pyc` 文件与源码不匹配
2. **动态导入问题**：某些导入钩子或元编程工具干扰
3. **第三方库bug**：decorator、wrapt等库的已知问题

## 解决步骤

### 步骤1：清除所有 Python 缓存文件

```powershell
# 在example项目目录下执行
Get-ChildItem -Recurse -Directory -Filter "__pycache__" | Remove-Item -Recurse -Force
Get-ChildItem -Recurse -File -Filter "*.pyc" | Remove-Item -Force
```

### 步骤2：检查是否有 @Component 装饰器

确认以下文件有正确的导入和装饰器：

**app/services/custom_login_provider.py**:

```python
from pyspring.ioc.annotations.component import Component


@Component
class CustomPasswordLoginProvider(DefaultPasswordLoginProvider):
    ...
```

**app/services/custom_register_service.py**:

```python
from pyspring.ioc.annotations.component import Component

@Component
class CustomRegisterService(DefaultRegisterService):
    ...
```

### 步骤3：重新安装框架

```powershell
# 回到框架目录
cd d:\Project\PycharmProjects\PySpring

# 清除框架缓存
Get-ChildItem -Recurse -Directory -Filter "__pycache__" | Remove-Item -Recurse -Force
Get-ChildItem -Recurse -File -Filter "*.pyc" | Remove-Item -Force

# 重新安装
pip install --upgrade --force-reinstall .
```

### 步骤4：重新启动项目

```powershell
cd example_project
pyspring run
```

## 如果问题仍然存在

请提供：

1. **完整的错误堆栈**（从头到尾）
2. **Python版本**：`python --version`
3. **已安装的包**：`pip list | findstr pyspring`
4. **custom_login_provider.py 的前50行**
5. **custom_register_service.py 的前50行**

这将帮助我精确定位问题。

## 最快的解决方案

**重新生成 example 项目**（推荐）：

```powershell
# 删除旧项目
Remove-Item -Recurse -Force example_project

# 重新生成
pyspring init example_project
cd example_project
pyspring db init
pyspring run
```

这确保使用最新的正确模板，避免旧文件的问题。
