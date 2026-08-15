# IOC 配置注入机制详解

## ❓ 你的问题

### 问题 1：这两种方式哪个好？还是一样的？

```python
# 方式 1: 配置类
@Component
@Singleton
class CacheConfig(ConfigSection):
    type: str = Field(default="memory")

# 方式 2: 初始化器类
@Component
class CacheConnectionInitializer:
    def __init__(self, cache_config: CacheConfig, cache_manager: CacheManagerService):
        ...
```

**答案**: **这两个不是二选一，而是配合使用的！**

---

## 📚 完整解释

### 1. 它们是不同的东西

| 对比项      | CacheConfig             | CacheConnectionInitializer |
|----------|-------------------------|----------------------------|
| **类型**   | **配置类**                 | **业务类（初始化器）**              |
| **职责**   | 存储配置数据                  | 使用配置初始化缓存                  |
| **注解**   | `@Component @Singleton` | `@Component`               |
| **生命周期** | 单例（全局唯一）                | 单例/原型（根据需要）                |
| **依赖方向** | 无依赖（只存数据）               | 依赖 `CacheConfig`           |

### 2. 它们是如何配合工作的

```python
# 步骤 1: 定义配置类（数据容器）
@Component
@Singleton
class CacheConfig(ConfigSection):
    """配置类 - 只负责存储配置数据"""
    type: str = Field(default="memory")
    redis: RedisConfig = Field(default_factory=RedisConfig)

# 步骤 2: 定义业务类（使用配置）
@Component
class CacheConnectionInitializer:
    """初始化器 - 使用配置来初始化缓存"""
    def __init__(self, cache_config: CacheConfig, cache_manager: CacheManagerService):
        # IOC 自动注入 CacheConfig 实例
        self.config = cache_config
        self.manager = cache_manager
    
    async def startup(self):
        # 使用配置
        if self.config.type == "redis":
            # 根据配置初始化 Redis
            provider = RedisService(host=self.config.redis.host, ...)
```

### 3. IOC 容器的工作流程

```
┌─────────────────────────────────────────────────────────────┐
│ 1. IOC 容器启动                                              │
└─────────────────────────────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────────┐
│ 2. 扫描发现 @Component 类                                    │
│    - 找到 CacheConfig                                        │
│    - 找到 CacheConnectionInitializer                         │
└─────────────────────────────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────────┐
│ 3. 实例化 CacheConfig                                        │
│    - Pydantic 自动从环境变量/默认值加载                       │
│    - 注册为 Singleton                                        │
└─────────────────────────────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────────┐
│ 4. 实例化 CacheConnectionInitializer                         │
│    - 分析构造函数参数类型                                     │
│    - 参数 1: cache_config: CacheConfig                       │
│    - 参数 2: cache_manager: CacheManagerService              │
│    - 从容器获取这两个依赖                                     │
│    - 自动注入到构造函数                                       │
└─────────────────────────────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────────┐
│ 5. 初始化器使用注入的配置对象工作                              │
└─────────────────────────────────────────────────────────────┘
```

---

## 🔑 核心概念

### @Component vs @Component @Singleton

```python
# ❌ 配置类不加 @Singleton
@Component  # 每次获取都创建新实例
class CacheConfig(ConfigSection):
    type: str = Field(default="memory")

# ✅ 配置类必须加 @Singleton
@Component
@Singleton  # 全局唯一实例，所有服务共享
class CacheConfig(ConfigSection):
    type: str = Field(default="memory")
```

**为什么配置类必须是 Singleton？**

- 配置在应用运行期间不应该改变
- 避免重复加载配置（性能优化）
- 所有服务应该使用同一份配置

---

## 📝 问题 2：Pydantic 自动从环境变量/YAML 加载？

### 答案：部分自动，部分需要配置

#### ✅ Pydantic 原生支持（自动）

```python
@Component
@Singleton
class CacheConfig(ConfigSection):  # ConfigSection 继承 BaseSettings
    """Pydantic 自动支持以下来源"""
    type: str = Field(default="memory")
```

**自动加载优先级**（从高到低）：

1. ✅ **环境变量**: `CACHE__TYPE=redis`
2. ✅ **.env 文件**: 如果配置了 `env_file=".env"`
3. ✅ **默认值**: `Field(default="memory")`

#### ❌ YAML 需要手动加载（不是自动的）

Pydantic **不原生支持** YAML 文件，需要额外处理：

```python
# 当前框架的实现方式
from pyspring.core.configuration.loader import ConfigLoader

# 1. 手动加载 YAML
loader = ConfigLoader()
yaml_data = loader.load_yaml(Path("config/repositories.yaml"))

# 2. 传递给 Pydantic
cache_config = CacheConfig(**yaml_data.get('cache', {}))
```

---

## 🎯 推荐方案

### 方案 A：纯 Pydantic（环境变量）

**适用场景**: 12-Factor App，容器化部署

```python
@Component
@Singleton
class CacheConfig(ConfigSection):
    """配置完全通过环境变量"""
    model_config = SettingsConfigDict(
        env_prefix="CACHE__",  # 环境变量前缀
        env_nested_delimiter="__",  # 嵌套分隔符
    )
    
    type: str = Field(default="memory")
    redis: RedisConfig = Field(default_factory=RedisConfig)
```

**使用**:

```bash
# .env 文件
CACHE__TYPE=redis
CACHE__REDIS__HOST=localhost
CACHE__REDIS__PORT=6379
```

**优点**:

- ✅ 完全自动，无需手动加载
- ✅ 容器友好（Docker/K8s）
- ✅ 安全（敏感信息不存 YAML）

---

### 方案 B：YAML + 环境变量混合（当前方案）

**适用场景**: 传统部署，复杂配置

```python
@Component
@Singleton
class CacheConfig(ConfigSection):
    """YAML 提供默认值，环境变量覆盖"""
    model_config = SettingsConfigDict(
        env_prefix="CACHE__",
        env_nested_delimiter="__",
    )
    
    type: str = Field(default="memory")
```

**YAML 文件**:

```yaml
# config/repositories.yaml
cache:
  type: memory
  redis:
    host: localhost
    port: 6379
```

**环境变量覆盖**:

```bash
CACHE__TYPE=redis  # 覆盖 YAML 中的 type
CACHE__REDIS__PASSWORD=secret123  # 添加密码（YAML 中没有）
```

**加载流程**:

```python
# 框架启动时
# 1. ConfigLoader 加载 YAML
yaml_data = ConfigLoader().load_yaml("config/repositories.yaml")

# 2. 实例化配置类（Pydantic 自动合并 YAML + 环境变量）
cache_config = CacheConfig(**yaml_data.get('cache', {}))

# 3. IOC 注册为 Singleton
container.register_singleton(CacheConfig, cache_config)
```

**优点**:

- ✅ YAML 提供结构化默认值（易读）
- ✅ 环境变量覆盖敏感信息（安全）
- ✅ 灵活性高

**缺点**:

- ❌ YAML 加载需要额外代码
- ❌ 不是完全"自动"

---

## 🔧 当前框架的实现

### 实际工作方式

```python
# 1. CacheConfig 定义
@Component
@Singleton
class CacheConfig(ConfigSection):
    type: str = Field(default="memory")
    redis: RedisConfig = Field(default_factory=RedisConfig)

# 2. IOC 容器扫描时
# IOC 容器发现 @Component(CacheConfig)，自动调用：
config = CacheConfig()  # Pydantic 自动从环境变量加载

# 3. 业务类注入
@Component
class CacheConnectionInitializer:
    def __init__(self, cache_config: CacheConfig):
        # IOC 注入步骤 2 创建的实例
        self.config = cache_config
```

### 配置加载优先级（完整）

```
最高优先级
    ↓
1. 环境变量 (CACHE__TYPE=redis)
    ↓
2. .env 文件 (如果配置了 env_file)
    ↓
3. 构造函数传参 (CacheConfig(type="redis"))
    ↓
4. Field 默认值 (Field(default="memory"))
    ↓
最低优先级
```

---

## 💡 最佳实践

### 1. 配置类设计

```python
# ✅ 推荐：小而专注的配置类
@Component
@Singleton
class CacheConfig(ConfigSection):
    """只负责缓存配置"""
    type: str = Field(default="memory")
    redis: RedisConfig = Field(default_factory=RedisConfig)

# ❌ 不推荐：大而全的配置类
@Component
@Singleton
class AllConfig(ConfigSection):
    """包含所有配置（难维护）"""
    cache: CacheConfig
    database: DatabaseConfig
    security: SecurityConfig
    # ...
```

### 2. 环境变量命名

```bash
# ✅ 推荐：使用前缀和分隔符
CACHE__TYPE=redis
CACHE__REDIS__HOST=localhost
DATABASE__POSTGRES__HOST=localhost

# ❌ 不推荐：扁平命名（容易冲突）
CACHE_TYPE=redis
REDIS_HOST=localhost  # 不知道是哪个模块的
```

### 3. 敏感信息处理

```yaml
# config/repositories.yaml (提交到 Git)
cache:
  type: redis
  redis:
    host: localhost
    port: 6379
    # password 不在 YAML 中！
```

```bash
# .env (不提交到 Git)
CACHE__REDIS__PASSWORD=super_secret_password
```

---

## 📋 总结

### 回答你的问题

1. **这两种方式哪个好？**
    - 它们**不是二选一**，是**配合使用**
    - `CacheConfig` 是**数据容器**（配置类）
    - `CacheConnectionInitializer` 是**使用者**（业务类）

2. **Pydantic 是否自动加载？**
    - ✅ **环境变量**：完全自动
    - ✅ **.env 文件**：配置后自动
    - ❌ **YAML 文件**：需要手动加载（Pydantic 不原生支持）

3. **推荐方式**：
    - **云原生部署**：纯环境变量（完全自动）
    - **传统部署**：YAML + 环境变量混合（半自动）
    - **当前框架**：使用混合方式，YAML 提供默认值，环境变量覆盖

### 关键点

- `@Component @Singleton` 让配置类由 IOC 管理
- Pydantic 自动从环境变量加载（**这是自动的**）
- YAML 加载需要额外代码（**这不是自动的**）
- 环境变量优先级最高，可以覆盖任何配置源

---

**简单记忆**:

- **配置类** = 数据存储 = `@Component @Singleton`
- **业务类** = 使用配置 = `@Component` + 构造函数注入
- **自动加载** = 环境变量 ✅ / YAML ❌
