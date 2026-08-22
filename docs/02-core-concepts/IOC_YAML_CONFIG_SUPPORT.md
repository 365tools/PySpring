# 改进 YAML 配置支持方案

## 📊 当前状态

### ✅ 已有的 YAML 支持

框架**已经支持 YAML**，但实现分散在各个模块：

```python
# 1. ConfigLoader (core)
loader = ConfigLoader()
yaml_data = loader.load_yaml(Path("config/app.yaml"))

# 2. RepositoriesConfigManager (repositories)
config_mgr = RepositoriesConfigManager()  # 自动加载 repositories.yaml

# 3. LoggingConfigManager (log)
log_mgr = LoggingConfigManager()  # 自动加载 logging.yaml
```

### ❌ 当前问题

1. **配置类不自动加载 YAML**
   ```python
   # ❌ Pydantic 原生不支持 YAML
   @Component
   @Singleton
   class CacheConfig(ConfigSection):
       type: str = Field(default="memory")
       # 无法自动从 YAML 加载！
   ```

2. **手动加载代码重复**
   ```python
   # 每个模块都有类似代码
   with open("config/xxx.yaml") as f:
       config = yaml.safe_load(f)
   ```

3. **配置加载时机不统一**
    - 有些在 `__init__` 中加载
    - 有些通过 ConfigManager
    - 有些通过 Initializer

---

## 🎯 改进方案

### 方案 A：扩展 ConfigSection 支持 YAML（推荐）

**目标**: 让配置类自动从 YAML 文件加载

#### 实现步骤

##### 1. 增强 ConfigSection 基类

```python
# core/abstracts/config.py

from pathlib import Path
from typing import Any, Dict, Optional, TypeVar
import yaml
from pydantic_settings import BaseSettings, SettingsConfigDict

TConfig = TypeVar("TConfig", bound=BaseSettings)


class ConfigSection(BaseSettings):
    """
    配置节基类

    支持多源配置加载（优先级从高到低）：
    1. 环境变量（如 CACHE__TYPE=redis）
    2. .env 文件
    3. YAML 文件（通过 yaml_config_file 指定）
    4. Field 默认值

    使用示例：
        @Component
        @Singleton
        class CacheConfig(ConfigSection):
            model_config = SettingsConfigDict(
                yaml_config_file="config/repositories.yaml",  # YAML 文件路径
                yaml_config_key="cache",  # YAML 中的键路径
            )

            type: str = Field(default="memory")
    """

    model_config = SettingsConfigDict(env_nested_delimiter="__", case_sensitive=False, extra="ignore")

    def __init__(self, **kwargs):
        """
        初始化配置，自动加载 YAML

        加载顺序：
        1. 尝试加载 YAML 配置
        2. 合并传入的 kwargs
        3. 环境变量自动覆盖（Pydantic 原生支持）
        """
        # 1. 加载 YAML 配置
        yaml_data = self._load_yaml_config()

        # 2. 合并 YAML 数据和传入的 kwargs
        merged_data = {**yaml_data, **kwargs}

        # 3. 调用 Pydantic 的初始化（环境变量自动覆盖）
        super().__init__(**merged_data)

    def _load_yaml_config(self) -> Dict[str, Any]:
        """
        从 YAML 文件加载配置

        Returns:
            配置字典
        """
        config = self.model_config

        # 获取 YAML 文件路径
        yaml_file = config.get("yaml_config_file")
        if not yaml_file:
            return {}

        # 获取 YAML 键路径（如 "cache.redis"）
        yaml_key = config.get("yaml_config_key", "")

        # 加载 YAML
        yaml_path = self._find_yaml_file(yaml_file)
        if not yaml_path or not yaml_path.exists():
            return {}

        try:
            with open(yaml_path, "r", encoding="utf-8") as f:
                yaml_data = yaml.safe_load(f) or {}

            # 提取指定键的数据
            if yaml_key:
                for key in yaml_key.split("."):
                    yaml_data = yaml_data.get(key, {})

            return yaml_data if isinstance(yaml_data, dict) else {}

        except Exception:
            return {}

    @staticmethod
    def _find_yaml_file(filename: str) -> Optional[Path]:
        """
        查找 YAML 文件

        搜索路径（优先级从高到低）：
        1. 当前工作目录
        2. config/ 目录
        3. 项目根目录/config
        """
        search_paths = [
            Path.cwd() / filename,
            Path.cwd() / "config" / Path(filename).name,
            Path(__file__).parent.parent.parent / "config" / Path(filename).name,
        ]

        for path in search_paths:
            if path.exists():
                return path

        return None

    def validate(self) -> bool:
        """验证配置"""
        try:
            self.model_validate(self.model_dump())
            return True
        except Exception:
            return False

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return self.model_dump()
```

##### 2. 更新配置类使用

```python
# repositories/cache/config.py

from pyspring.core.abstracts.config import ConfigSection
from pyspring.core.ioc.annotations.component import Component
from pyspring.core.ioc.annotations.scope import Singleton
from pydantic import Field
from pydantic_settings import SettingsConfigDict


@Component
@Singleton
class CacheConfig(ConfigSection):
    """
    缓存配置（由IOC管理）

    配置加载优先级（从高到低）：
    1. 环境变量：CACHE__TYPE=redis
    2. .env 文件：CACHE__TYPE=redis
    3. YAML 文件：config/repositories.yaml 中的 cache 节点
    4. 默认值：Field(default="memory")
    """

    model_config = SettingsConfigDict(
        # 指定 YAML 文件路径
        yaml_config_file="config/repositories.yaml",
        # 指定在 YAML 中的键路径
        yaml_config_key="cache",
        # Pydantic 原生配置
        env_prefix="CACHE__",
        env_nested_delimiter="__",
        env_file=".env",
    )

    type: str = Field(default="memory", description="缓存类型：redis、memory")
    redis: RedisConfig = Field(default_factory=RedisConfig)
    memory: MemoryConfig = Field(default_factory=MemoryConfig)
```

##### 3. 配置文件结构

```yaml
# config/repositories.yaml
cache:
  type: memory
  redis:
    host: localhost
    port: 6379
    db: 0
    pool:
      max_connections: 50
  memory:
    max_size: 1000
    ttl: 3600

database:
  type: sqlite
  postgres:
    host: localhost
    port: 5432
```

##### 4. 使用示例

```python
# 业务代码
@Component
class CacheConnectionInitializer:
    def __init__(self, cache_config: CacheConfig):
        # IOC 自动注入配置（已自动加载 YAML）
        self.config = cache_config
        
        # 配置已完整加载，优先级：
        # 环境变量 > YAML > 默认值
        print(self.config.type)  # 从 YAML 加载
        print(self.config.redis.host)  # 从 YAML 加载
```

---

### 方案 B：使用 ConfigFactory（备选）

如果不想修改 `ConfigSection`，可以用工厂模式：

```python
# core/configuration/factory.py

from pathlib import Path
from typing import Type, TypeVar, Dict, Any
import yaml
from pydantic_settings import BaseSettings

T = TypeVar("T", bound=BaseSettings)


class ConfigFactory:
    """
    配置工厂

    负责从 YAML + 环境变量创建配置对象
    """

    @staticmethod
    def create(config_cls: Type[T], yaml_file: str, yaml_key: str = "") -> T:
        """
        创建配置对象

        Args:
            config_cls: 配置类
            yaml_file: YAML 文件路径
            yaml_key: YAML 中的键路径（如 "cache.redis"）

        Returns:
            配置实例
        """
        # 1. 加载 YAML
        yaml_data = ConfigFactory._load_yaml(yaml_file, yaml_key)

        # 2. 创建配置对象（环境变量自动覆盖）
        return config_cls(**yaml_data)

    @staticmethod
    def _load_yaml(filename: str, key_path: str) -> Dict[str, Any]:
        """加载 YAML 配置"""
        yaml_path = ConfigFactory._find_file(filename)
        if not yaml_path or not yaml_path.exists():
            return {}

        try:
            with open(yaml_path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f) or {}

            # 提取指定键
            if key_path:
                for key in key_path.split("."):
                    data = data.get(key, {})

            return data if isinstance(data, dict) else {}
        except Exception:
            return {}

    @staticmethod
    def _find_file(filename: str) -> Optional[Path]:
        """查找配置文件"""
        search_paths = [
            Path.cwd() / filename,
            Path.cwd() / "config" / Path(filename).name,
        ]
        for path in search_paths:
            if path.exists():
                return path
        return None
```

**使用**:

```python
# repositories/cache/__init__.py

from pyspring.core.configuration.factory import ConfigFactory
from pyspring.core.ioc.annotations.bean import Bean
from pyspring.core.ioc.annotations.configuration import Configuration
from .config import CacheConfig


@Configuration
class CacheConfigProvider:
    """配置提供者"""

    @Bean
    def cache_config(self) -> CacheConfig:
        """
        创建 CacheConfig Bean

        自动从 YAML + 环境变量加载
        """
        return ConfigFactory.create(CacheConfig, yaml_file="config/repositories.yaml", yaml_key="cache")
```

---

## 📊 方案对比

| 特性         | 方案 A（扩展 ConfigSection） | 方案 B（ConfigFactory） |
|------------|------------------------|---------------------|
| **实现难度**   | 中等                     | 简单                  |
| **侵入性**    | 修改基类                   | 无侵入                 |
| **使用便捷性**  | ⭐⭐⭐⭐⭐（最方便）             | ⭐⭐⭐（需要工厂）           |
| **配置集中度**  | ⭐⭐⭐⭐⭐（配置类内）            | ⭐⭐⭐（分散在Provider）    |
| **IOC 集成** | ⭐⭐⭐⭐⭐（完美）              | ⭐⭐⭐⭐（需要 @Bean）      |
| **API 稳定性** | ⭐⭐⭐⭐（可选功能）             | ⭐⭐⭐⭐⭐（完全稳定）         |

---

## 🎯 推荐实现：方案 A

### 优势

1. ✅ **自动化最高**：配置类自己处理 YAML 加载
2. ✅ **使用最简单**：只需在 `model_config` 中指定 YAML 文件
3. ✅ **IOC 友好**：配置类直接加 `@Component` 即可
4. ✅ **统一优先级**：环境变量 > YAML > 默认值

### 实施步骤

1. **修改 `ConfigSection` 基类** (1个文件)
    - 添加 `__init__` 方法
    - 实现 `_load_yaml_config` 方法
    - 实现 `_find_yaml_file` 方法

2. **更新配置类** (3-5个文件)
    - `CacheConfig`
    - `DatabaseConfig`
    - 其他需要 YAML 的配置类

3. **删除旧的 ConfigManager** (可选)
    - `RepositoriesConfigManager` 可以删除
    - `LoggingConfigManager` 可以简化

---

## 🔧 完整示例

### 配置定义

```python
# repositories/cache/config.py


@Component
@Singleton
class CacheConfig(ConfigSection):
    model_config = SettingsConfigDict(
        yaml_config_file="config/repositories.yaml",
        yaml_config_key="cache",
        env_prefix="CACHE__",
    )

    type: str = Field(default="memory")
    redis: RedisConfig = Field(default_factory=RedisConfig)
```

### YAML 文件

```yaml
# config/repositories.yaml
cache:
  type: redis
  redis:
    host: localhost
    port: 6379
```

### 环境变量覆盖

```bash
# .env
CACHE__TYPE=redis
CACHE__REDIS__HOST=redis-server
CACHE__REDIS__PASSWORD=secret123
```

### 业务代码

```python
@Component
class CacheConnectionInitializer:
    def __init__(self, cache_config: CacheConfig):
        # IOC 注入配置（YAML 已自动加载）
        self.config = cache_config
        
        # 配置优先级：
        # CACHE__TYPE 环境变量 > YAML cache.type > Field default
        print(self.config.type)
```

---

## 🎉 总结

- ✅ **YAML 配置**：通过 ConfigLoader 自动加载
- ✅ **统一优先级**：环境变量 > YAML > 默认值
- ✅ **IOC 友好**：配置对象通过 IOC 注入
- ✅ **零侵入使用**：业务代码只需声明依赖

实现 **Pydantic + YAML + 环境变量** 的完美融合。 🚀
