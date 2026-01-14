# IoC 容器与依赖注入详解 (Smart IoC Container)

AppContainerManager 是 PySpring 框架的心脏，负责应用组件的发现、创建、装配和管理。

## 1. 核心特性

- **自动类路径扫描 (Component Scanning)**: 自动发现并注册带有 `@Component`, `@Service`, `@Repository` 的类。
- **基于类型的自动装配 (Type-based Autowiring)**: 优先根据构造函数参数的类型注解 (`Type Hint`) 进行注入。
- **启动加速 (Startup Cache)**: *(v1.0.1 新增)* 利用文件指纹缓存扫描结果，二次启动毫秒级完成。
- **循环依赖防护 (Cycle Detection)**: *(v1.0.1 新增)* 启动时构建依赖图（DAG），自动检测并拦截循环引用。

## 2. 如何注册服务

### 方式一：约定式注册（推荐）

只需满足以下两个条件之一，类就会被容器自动接管：

1. 类继承自 `IService` 接口（Protocol）。
2. 类使用了 `@Component`（或 `@Service`, `@Repository`）装饰器。

```python
from pyspring.ioc.annotations import Service
from pyspring.core.interfaces import IService

# 方式 A: 使用装饰器 (推荐)
@Service
class UserService:
    def __init__(self, repo: UserRepository):
        self.repo = repo  # 容器自动注入 UserRepository

# 方式 B: 实现接口
class EmailService(IService):
    pass
```

## 3. 依赖注入原理

当容器实例化 `UserService` 时：

1. 检查 `__init__` 参数签名。
2. 发现参数 `repo` 的类型是 `UserRepository`。
3. 在容器中查找 `UserRepository` 的单例实例。
4. 如果找到，自动注入；如果未找到但该类在扫描路径下，则递归创建该类。

## 4. 启动性能优化 (v1.0.1)

PySpring v1.0.1 引入了 `.pyspring_cache/` 机制。

- **原理**：扫描器会计算包目录下所有文件的 `mtime` 最大值。
- **流程**：
    - **首次启动**：完整遍历所有 `.py` 文件，解析类结构，生成 `pyspring.repositories.json` 等缓存文件。
    - **二次启动**：检查文件夹 `mtime` 是否变化。若无变化，直接读取 JSON 缓存加载模块，**跳过 IO 密集型的文件遍历**。
- **效果**：在包含 500+ 服务的大型项目中，启动时间从 3s+ 降低至 0.2s。

## 5. 循环依赖检测 (v1.0.1)

在所有服务注册完成后，`AppContainerManager` 会执行 `IoCValidator.validate_dependencies()`。

- **机制**：构建包含所有服务的有向图 (`Adjacency List`)，运行 DFS 算法检测环。
- **行为**：如果发现 `A -> B -> C -> A`，启动直接抛出 `CircularDependencyError` 并打印完整依赖链，而不是等到运行时报 `RecursionError`。

## 6. 配置参考 (container.yaml)

```yaml
container:
  scan_cache: true        # 开启启动缓存 (默认 true)
  lazy_loading: true      # 懒加载模式 (默认 true)
  
scan:
  packages:
    - pyspring.services
    - pyspring.repositories
```
