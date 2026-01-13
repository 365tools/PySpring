# IoC 容器配置说明

## 概述

PySpring 的 IoC 容器现在支持通过 YAML 配置文件管理服务扫描路径和容器行为，不再需要在代码中硬编码配置。

## 配置文件位置

容器管理器会按以下顺序查找配置文件：

1. `{项目根目录}/config/container.yaml`
2. `{当前工作目录}/config/container.yaml`
3. `{当前工作目录}/container.yaml`

如果找不到配置文件，将使用默认配置。

## 配置文件结构

```yaml
# 服务扫描配置
scan:
  # 需要扫描的包路径列表
  # 注意：框架会自动包含 'pyspring.*' 核心包，此处只需添加你自己的业务包
  packages:
    - app.services        # 用户服务
    - app.repositories    # 用户数据层
    - app.aspects         # 用户切面
  
  # 是否启用递归扫描（扫描子包）
  recursive: true
  
# 容器行为配置
container:
  # 启用启动缓存 (v1.0.1+) - 显著提升二次启动速度
  scan_cache: true
  
  # 启用懒加载 - 服务仅在首次注入或获取时实例化
  lazy_loading: true
  
  # 自动接口映射 - IService -> ServiceImpl
  auto_interface_mapping: true
  
  # 调试模式 - 打印更多 DI 细节
  debug: false
```

## 配置项说明

### scan 配置

- **packages**: 需要扫描的 Python 包路径列表
    - 支持任意有效的 Python 模块路径
    - 容器会扫描这些包下所有以 `service_suffix` 结尾的类

- **recursive**: 是否递归扫描子包（默认：`true`）

- **service_suffix**: 服务类名后缀（默认：`"Service"`）
    - 所有以此后缀结尾的类都会被识别为服务类

### container 配置

- **lazy_loading**: 是否启用懒加载（默认：`true`）
    - `true`: 服务在首次使用时才实例化
    - `false`: 容器初始化时实例化所有服务

- **auto_interface_mapping**: 是否自动映射接口到实现（默认：`true`）
    - 自动建立抽象类/接口到具体实现类的映射关系

- **debug**: 是否记录详细日志（默认：`false`）
    - 开启后会记录服务注册、依赖解析等详细信息

## 使用方式

### 1. 使用默认配置

如果不创建配置文件，容器会使用内置的默认配置：

```python
from pyspring.ioc.manager import AppContainerManager

manager = AppContainerManager()
manager.register_all_services()
```

### 2. 使用自定义配置

创建 `config/container.yaml` 文件：

```yaml
scan:
  packages:
    - your.custom.services
    - your.custom.repositories
    - src.pyspring.system
```

然后正常初始化容器：

```python
from pyspring.ioc.manager import AppContainerManager

manager = AppContainerManager()
manager.register_all_services()  # 会自动加载 YAML 配置
```

### 3. 获取配置信息

```python
# 获取扫描包列表
packages = manager.get_scan_packages()
print(f"将扫描以下包: {packages}")
```

## 示例

### 添加自定义服务包

假设您有自定义的服务在 `myapp.services` 包下：

**config/container.yaml**:

```yaml
scan:
  packages:
    - myapp.services      # 添加您的自定义包
    - myapp.repositories
    # 注意：pyspring.* 核心包会自动被框架注册，无需在此列出
```

### 开发环境配置

开发时可以开启调试日志：

**config/container.yaml**:

```yaml
scan:
  packages:
    - myapp.services

container:
  debug: true  # 开启调试日志
```

### 最小化配置

只扫描必要的包以提高启动速度：

**config/container.yaml**:

```yaml
scan:
  packages:
    - src.pyspring.repositories.db
    - myapp.core
```

## 注意事项

1. **包路径必须有效**: 确保配置的包路径是有效的 Python 模块路径
2. **服务命名约定**: 所有服务类必须以 `Service` 结尾（或配置的后缀）
3. **单例模式**: 实现 `ISingletonService` 接口的服务会被注册为单例
4. **依赖注入**: 容器会自动解析构造函数的依赖并注入
5. **配置优先级**: YAML 配置 > 默认配置

## 迁移指南

### 从硬编码配置迁移

**之前（硬编码）**:

```python
path = [
    'src.ref.core.repositories',
    'src.ref.core.security',
    'src.ref.services',
]

for path in path:
    self.scan_and_register_services(path)
```

**现在（YAML 配置）**:

1. 创建 `config/container.yaml`:

```yaml
scan:
  packages:
    - src.ref.core.repositories
    - src.ref.core.security
    - src.ref.services
```

2. 代码简化为:

```python
manager = AppContainerManager()
manager.register_all_services()  # 自动从 YAML 加载
```

## 故障排查

### 配置文件未加载

如果看到日志 "⚠️ 未找到配置文件，使用默认配置"：

1. 检查配置文件路径是否正确
2. 确认文件名为 `container.yaml` 而不是 `container.yml`
3. 查看日志中的搜索路径

### 服务未被扫描

如果某些服务未被注册：

1. 确认包路径在 `scan.packages` 中
2. 检查类名是否以 `Service` 结尾
3. 开启 `container.debug: true` 查看详细日志

### 依赖注入失败

如果服务依赖无法解析：

1. 确保被依赖的服务也在扫描路径中
2. 检查接口到实现的映射是否正确
3. 查看日志中的依赖解析信息
