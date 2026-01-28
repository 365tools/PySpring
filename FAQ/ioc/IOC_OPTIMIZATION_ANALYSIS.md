# PySpring IoC 容器优化方案分析

## 一、当前机制分析

### 1.1 当前流程

```
扫描阶段：
ComponentScanner._generate_name() 
  → SecurityEntityConfiguration → 'security_entity_configuration'
  → CustomSecurityEntityConfiguration → 'custom_security_entity_configuration'
  ↓
注册阶段：
Container._register_component()
  → 检查 name 是否已存在
  → 如果存在且 existing.is_conditional=True，允许替换
  → 但前提是：name 必须相同！
```

### 1.2 核心问题

**问题**：依赖 Bean 名称匹配，不同类名生成不同的 Bean 名称

- `SecurityEntityConfiguration` → `security_entity_configuration`
- `CustomSecurityEntityConfiguration` → `custom_security_entity_configuration`
- **结果**：无法触发替换逻辑！

### 1.3 当前替换逻辑（registry.py:76-90）

```python
# 只在 name 相同时检查
if name in self._services:
    existing = self._services[name]
    # 👉 关键：如果旧的是 @ConditionalOnMissingBean，允许替换
    elif existing.is_conditional:
        logger.debug(f"🔄 用户组件替换条件组件: '{name}'")
        pass  # 继续注册，覆盖
```

**限制**：只有 name 相同才会检查 `is_conditional`！

---

## 二、Spring Boot 最佳实践

### 2.1 Spring Boot 的 @ConditionalOnMissingBean

Spring Boot 的实现：

```java
@ConditionalOnMissingBean(value = DataSource.class)
public DataSource dataSource() {
    return new HikariDataSource();
}
```

**关键特性**：

1. **基于类型匹配**，不是名称
2. 检查容器中是否已有 `DataSource` 类型的 Bean
3. 如果有，跳过注册；如果没有，注册

### 2.2 类型检查机制

Spring 的 `ConditionalOnMissingBean` 逻辑：

```java
// 简化版伪代码
boolean shouldRegister(Class<?> type) {
    // 1. 检查容器中是否有该类型
    if (beanFactory.containsBean(type)) {
        return false;
    }
    
    // 2. 检查是否有该类型的子类
    String[] beanNames = beanFactory.getBeanNamesForType(type);
    if (beanNames.length > 0) {
        return false;
    }
    
    return true;
}
```

**核心**：基于类型层次结构，不是名称！

### 2.3 PySpring 当前的类型检查

```python
# container.py:95
conditional_type = getattr(cls, "__pyspring_conditional_on_missing_bean__", None)
if conditional_type:
    if self.registry.has_type(conditional_type):  # ✅ 已有类型检查
        logger.debug(f"⏩ 跳过组件：{conditional_type.__name__} 已存在")
        return
```

**问题**：

- `has_type()` 只检查**精确类型**匹配
- 不检查继承关系！
- `SecurityEntityConfiguration` 标记为 `@ConditionalOnMissingBean`（无参数）
- 检查类型 = `SecurityEntityConfiguration` 本身
- `CustomSecurityEntityConfiguration` 注册时，容器中还没有 `CustomSecurityEntityConfiguration`
- **所以父类也会注册！**

---

## 三、优化方案设计

### 方案 A：类型映射表 + 继承检测（推荐）

#### 3.1 核心思路

```
扫描阶段：
  1. 扫描所有组件
  2. 建立类型映射表：
     - type_to_components: {SecurityEntityConfiguration: [metadata1, metadata2]}
     - conditional_types: {SecurityEntityConfiguration: metadata1}
     
注册阶段：
  1. 遍历每个组件
  2. 检查其所有基类
  3. 如果基类在 conditional_types 中
     → 标记：当前组件替换该基类
     → 跳过基类的注册
```

#### 3.2 数据结构设计

```python
# 在 ComponentScanner 中添加
class ComponentScanner:
    def __init__(self):
        self.scanned_components: Dict[type, ComponentMetadata] = {}
        
        # 新增：类型到组件的映射（支持多实现）
        self.type_to_components: Dict[type, List[ComponentMetadata]] = {}
        
        # 新增：条件组件映射
        self.conditional_components: Dict[type, ComponentMetadata] = {}
        
    def scan(self, base_packages: List[str]) -> Dict[type, ComponentMetadata]:
        # 第一步：扫描所有组件
        for package in base_packages:
            self._scan_package(package)
        
        # 第二步：构建类型映射表
        self._build_type_mappings()
        
        # 第三步：检测替换关系
        self._detect_replacements()
        
        return self.scanned_components
```

#### 3.3 替换检测逻辑

```python
def _detect_replacements(self):
    """检测组件替换关系"""
    for comp_type, metadata in self.scanned_components.items():
        # 检查所有基类
        for base_class in comp_type.__mro__[1:]:  # 跳过自己
            if base_class in self.conditional_components:
                conditional_meta = self.conditional_components[base_class]
                
                # 标记：当前组件替换条件组件
                metadata.replaces = conditional_meta.name
                
                # 标记：条件组件被替换
                conditional_meta.replaced_by = metadata.name
                
                logger.debug(f"🔄 检测到替换: {metadata.name} 替换 {conditional_meta.name}")
                break
```

#### 3.4 注册阶段优化

```python
def _register_component(self, metadata: ComponentMetadata):
    """注册普通组件"""

    # 检查是否被替换
    if hasattr(metadata, 'replaced_by') and metadata.replaced_by:
        logger.debug(f"⏩ 跳过条件组件 {metadata.name}：已被 {metadata.replaced_by} 替换")
        return

    # ... 原有注册逻辑
```

---

### 方案 B：延迟检查 + 类型层次查询

#### 3.1 核心思路

```
扫描阶段：
  - 正常扫描，不做特殊处理
  
注册阶段：
  1. 注册时不检查 ConditionalOnMissingBean
  2. 所有组件都先注册
  
实例化阶段：
  1. 首次 get_bean() 时
  2. 检查 registry 中是否有多个实现
  3. 如果有条件注册的，移除它
```

**缺点**：实例化阶段才检查，太晚了，可能已经创建了不该创建的实例。

---

### 方案 C：智能名称匹配（不推荐）

```python
def _generate_name(cls: type) -> str:
    """生成组件名称"""
    # 如果是子类，使用父类的名称
    for base in cls.__mro__[1:]:
        if hasattr(base, "__pyspring_conditional_on_missing_bean__"):
            return _generate_name(base)  # 递归使用父类名称

    # 默认逻辑
    return to_snake_case(cls.__name__)
```

**缺点**：改变了命名语义，可能导致其他问题。

---

## 四、推荐方案详细设计

### 方案 A（扩展版）：两阶段扫描 + 类型映射

#### 4.1 改动范围

**文件 1**: `src/pyspring/ioc/scanner/scanner.py`

- 新增：`_build_type_mappings()` - 构建类型映射表
- 新增：`_detect_replacements()` - 检测替换关系
- 修改：`scan()` - 添加两阶段处理

**文件 2**: `src/pyspring/ioc/scanner/scanner.py` (ComponentMetadata)

- 新增字段：`replaces: Optional[str] = None`
- 新增字段：`replaced_by: Optional[str] = None`

**文件 3**: `src/pyspring/ioc/container/container.py`

- 修改：`_register_component()` - 添加替换检查
- 可选：添加日志，显示替换关系

#### 4.2 伪代码实现

```python
# scanner.py
class ComponentScanner:
    def scan(self, base_packages: List[str]):
        # 阶段 1：扫描所有组件
        for package in base_packages:
            self._scan_package(package)

        # 阶段 2：构建映射表
        for comp_type, metadata in self.scanned_components.items():
            # 添加到类型映射
            for base_class in comp_type.__mro__:
                self.type_to_components.setdefault(base_class, []).append(metadata)

            # 记录条件组件
            if hasattr(comp_type, "__pyspring_conditional_on_missing_bean__"):
                conditional_type = getattr(comp_type, "__pyspring_conditional_on_missing_bean__")
                # 如果未指定类型，使用自身类型
                if conditional_type is None or conditional_type == object:
                    conditional_type = comp_type
                self.conditional_components[conditional_type] = metadata

        # 阶段 3：检测替换
        for comp_type, metadata in self.scanned_components.items():
            for base_class in comp_type.__mro__[1:]:  # 跳过自己
                if base_class in self.conditional_components:
                    conditional_meta = self.conditional_components[base_class]
                    metadata.replaces = conditional_meta.name
                    conditional_meta.replaced_by = metadata.name
                    break

        return self.scanned_components


# container.py
class Container:
    def _register_component(self, metadata: ComponentMetadata):
        # 新增：检查是否被替换
        if hasattr(metadata, 'replaced_by') and metadata.replaced_by:
            logger.info(f"⏩ 跳过条件组件 {metadata.name}: 已被 {metadata.replaced_by} 替换")
            return

        # 如果当前组件替换了其他组件，记录日志
        if hasattr(metadata, 'replaces') and metadata.replaces:
            logger.info(f"🔄 组件替换: {metadata.name} 替换 {metadata.replaces}")

        # ... 原有注册逻辑
```

#### 4.3 测试用例

```python
# 场景 1：父类有 @ConditionalOnMissingBean
@Component
@ConditionalOnMissingBean
class SecurityEntityConfiguration:
    pass


@Component
class CustomSecurityEntityConfiguration(SecurityEntityConfiguration):
    pass


# 预期：只注册 CustomSecurityEntityConfiguration


# 场景 2：父类指定了检查类型
@Component
@ConditionalOnMissingBean(IUserProvider)
class DefaultUserProvider(IUserProvider):
    pass


@Component
class CustomUserProvider(IUserProvider):
    pass


# 预期：只注册 CustomUserProvider（因为已有 IUserProvider 实现）


# 场景 3：多层继承
@ConditionalOnMissingBean
class BaseConfig:
    pass


class MiddleConfig(BaseConfig):
    pass


@Component
class FinalConfig(MiddleConfig):
    pass

# 预期：只注册 FinalConfig，BaseConfig 被替换
```

---

## 五、对比分析

| 特性            | 当前机制   | 方案 A（推荐）  | 方案 B  | 方案 C    |
|---------------|--------|-----------|-------|---------|
| 基于类型匹配        | ❌ 基于名称 | ✅ 基于继承    | ✅ 但太晚 | ❌ 改名    |
| Spring Boot兼容 | ❌      | ✅         | 部分    | ❌       |
| 实现复杂度         | 简单     | 中等        | 低     | 低       |
| 性能影响          | 无      | 扫描阶段+一次遍历 | 实例化阶段 | 无       |
| 向后兼容          | N/A    | ✅ 完全兼容    | ✅     | ⚠️ 可能破坏 |
| 解决当前问题        | ❌      | ✅         | ✅     | ✅       |

---

## 六、实施建议

### 6.1 优先级

1. **立即修复**（临时方案）：
    - 更新 example 模板，添加 `@Component(name='security_entity_configuration')`
    - 更新诊断脚本，检测这个问题

2. **v1.2.0 优化**（推荐方案 A）：
    - 实现两阶段扫描
    - 添加类型映射和替换检测
    - 完全解决继承替换问题

### 6.2 风险评估

**低风险**：

- 向后兼容：现有代码无需修改
- 只影响 `@ConditionalOnMissingBean` 的行为
- 可以通过配置开关控制新旧逻辑

**测试重点**：

- 单继承场景
- 多层继承场景
- 接口多实现场景
- 条件Bean与普通Bean混合场景

---

## 七、总结

### 当前问题根因

`_generate_name()` 基于类名生成不同的 Bean 名称，导致继承的子类无法触发父类的 `@ConditionalOnMissingBean` 替换逻辑。

### 推荐解决方案

**方案 A：两阶段扫描 + 类型映射**

- 扫描阶段：构建类型映射表
- 检测阶段：分析继承关系，标记替换
- 注册阶段：跳过被替换的组件
- **符合 Spring Boot 最佳实践**

### 实施路径

1. 短期：修改 template，手动指定 Bean 名称
2. 中期：实现方案 A，彻底解决问题
3. 长期：考虑更多条件装饰器（如 `@ConditionalOnProperty` 等）

---

**是否开始实施方案 A？** 请确认后我开始修改代码。
