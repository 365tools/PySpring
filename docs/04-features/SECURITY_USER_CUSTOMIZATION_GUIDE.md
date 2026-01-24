# PySpring 安全模块 - 用户自定义扩展指南

## 核心理念：@ConditionalOnMissingBean

PySpring 框架采用 **Spring Boot 的"约定优于配置"设计模式**：

```
框架提供默认实现 + @ConditionalOnMissingBean
           ↓
用户提供自定义实现 + @Bean()
           ↓
框架自动检测并选择：有用户实现 → 用用户的；没有 → 用默认的
```

**这就是真正的"用户自定义扩展最佳实践"！**

## @ConditionalOnMissingBean 机制详解

### 框架侧（提供默认实现）

```python
# pyspring/security/authentication/config/auto_config.py
@Configuration
class AuthenticationConfiguration:

    @Bean()
    @ConditionalOnMissingBean(IRegisterService)  # 关键！
    def default_register_service(...) -> IRegisterService:
        """
        只有当用户没有提供 IRegisterService 实现时，才创建此默认实现
        """
        return DefaultRegisterService(...)
```

### 用户侧（提供自定义实现）

```python
# app/services/custom_register_service.py
@Configuration
class CustomRegisterServiceConfiguration:

    @Bean()  # 通过 @Bean() 注册到容器
    def custom_register_service(...) -> IRegisterService:
        """
        框架检测到用户提供了 IRegisterService 实现
        自动跳过 DefaultRegisterService 的创建
        全局使用此自定义实现
        """
        return CustomRegisterService(...)
```

### 检测流程

```
1. IoC 容器启动
    ↓
2. 扫描所有 @Configuration 和 @Bean
    ↓
3. 收集用户提供的 Bean（CustomRegisterService）
    ↓
4. 处理框架的 @ConditionalOnMissingBean
    ↓
5. 检查容器中是否已有 IRegisterService 实例
    ↓
6a. 有 → 跳过 DefaultRegisterService 创建
6b. 没有 → 创建 DefaultRegisterService
    ↓
7. 全局使用选定的实现
```

## 可自定义的组件列表

框架通过 `@ConditionalOnMissingBean` 标记了以下组件，**用户可以自由替换**：

| 接口                            | 默认实现                         | 用途       | 自定义场景                  |
|-------------------------------|------------------------------|----------|------------------------|
| `IRegisterService`            | DefaultRegisterService       | 用户注册     | ✅ 自定义字段、验证规则、后置操作      |
| `ILoginService`               | DefaultLoginService          | 用户登录     | ✅ 自定义认证逻辑、Token 生成     |
| `IPasswordEncoder`            | BCryptPasswordEncoder        | 密码加密     | ✅ 使用 Argon2、Scrypt 等算法 |
| `ILoginProvider`              | DefaultPasswordLoginProvider | 认证方式     | ✅ OAuth2、LDAP、短信验证码    |
| `IUserProvider`               | DefaultUserProvider          | 用户查询     | ✅ 自定义用户数据源             |
| `ITokenService`               | TokenService                 | Token 管理 | ✅ 自定义 Token 格式、存储      |
| `SecurityEntityConfiguration` | 默认配置                         | 实体映射     | ✅ 自定义用户表映射             |

## 完整的自定义示例

### 1. 自定义用户注册服务

```python
# app/services/custom_register_service.py
from pyspring.ioc.annotations.component import Configuration, Bean
from pyspring.security.authentication.contracts.flow import IRegisterService
from pyspring.security.authentication.contracts.response import UserInfo, User, Role
from pyspring.repositories.db.manager import DBManagerService


class CustomRegisterService(IRegisterService):
    """
    用户自定义的注册服务
    
    扩展点：
    - 自定义字段处理（username, phone）
    - 自定义验证规则（密码强度、黑名单检查）
    - 注册后操作（发送欢迎邮件、短信通知）
    - 集成第三方服务
    """

    def __init__(self, db: DBManagerService, component: SecurityEntityConfiguration,
                 password_encoder: IPasswordEncoder):
        self.db = db
        self.component = component
        self.password_encoder = password_encoder
        logger.info("📦 创建自定义 CustomRegisterService 实例")

    async def register(self, request: UserInfo) -> UserInfo:
        """自定义注册逻辑"""
        logger.info(f"🔐 自定义注册服务：注册用户 {request.user.email}")

        # 使用框架的数据库会话管理
        async with await self.db.session() as session:
            # 1. 自定义验证
            await self._validate_user(session, request.user)

            # 2. 创建用户（处理自定义字段）
            db_user = await self._create_user(session, request.user)

            # 3. 分配角色
            if request.roles:
                await self._assign_roles(session, db_user.id, request.roles)

            # 4. 提交事务
            await session.commit()
            await session.refresh(db_user)

            # 5. 自定义后置操作
            await self._after_register(db_user)

            return await self._build_user_info(session, db_user)

    async def _validate_user(self, session, user: User):
        """自定义验证逻辑"""
        # 检查邮箱是否已存在
        result = await session.execute(
            select(CustomUser).where(CustomUser.email == user.email)
        )
        if result.scalar_one_or_none():
            raise ValueError(f"邮箱已被注册: {user.email}")

        # 自定义验证：密码强度
        if len(user.password) < 6:
            raise ValueError("密码长度至少6位")

    async def _create_user(self, session, user: User):
        """创建用户记录，映射自定义字段"""
        hashed_password = self.password_encoder.encode(user.password)

        db_user = CustomUser(
            user_id=user.user_id or user.email,
            email=user.email,
            password=hashed_password,
            username=getattr(user, 'username', user.user_id),  # 自定义字段
            phone=getattr(user, 'phone', None),  # 自定义字段
            active=True,
            creator="system"
        )
        session.add(db_user)
        await session.flush()
        return db_user

    async def _after_register(self, user: CustomUser):
        """注册后置操作"""
        logger.info(f"📧 发送欢迎邮件到: {user.email}")
        # TODO: 集成邮件服务
        # await email_service.send_welcome(user.email)


@Configuration
class CustomRegisterServiceConfiguration:
    """注册自定义服务到 IoC 容器"""

    @Bean()  # 关键：通过 @Bean() 注册
    def custom_register_service(
            self, db: DBManagerService, component: SecurityEntityConfiguration,
            password_encoder: IPasswordEncoder
    ) -> IRegisterService:
        """
        框架会自动检测到用户提供了 IRegisterService 实现
        跳过 DefaultRegisterService 的创建（@ConditionalOnMissingBean）
        全局使用此实现
        """
        logger.info("🔧 注册自定义 IRegisterService 实现")
        return CustomRegisterService(db, component, password_encoder)
```

### 2. API 层使用（面向接口编程）

```python
# app/api/auth.py
from pyspring.security.authentication.contracts.flow import IRegisterService


@router.post("/register")
async def register(
        request: RegisterRequest,
        register_service: IRegisterService = Depends(lambda: Inject(IRegisterService))
        # ↑ 注入接口，框架自动提供用户的 CustomRegisterService 实现
):
    """
    用户注册
    
    关键点：
    - 注入的是 IRegisterService 接口（面向接口编程）
    - 实际实例是 CustomRegisterService（用户自定义）
    - 框架通过 @ConditionalOnMissingBean 自动选择
    """
    user_request = UserInfo(
        user=User(
            user_id=request.username,
            email=request.email,
            password=request.password,  # 明文，服务自动加密
            username=request.username  # 自定义字段
        ),
        roles=[Role(code="USER", name="普通用户", status=True)]
    )

    # 调用的是用户自定义的 CustomRegisterService.register()
    result = await register_service.register(user_request)
    return Response.success(result, message="注册成功")
```

**工作流程：**

```
用户请求 POST /register
    ↓
FastAPI 依赖注入 IRegisterService
    ↓
IoC 容器查找 IRegisterService 实现
    ↓
发现用户提供了 CustomRegisterService（@Bean）
    ↓
框架跳过 DefaultRegisterService（@ConditionalOnMissingBean）
    ↓
注入 CustomRegisterService 实例
    ↓
执行用户自定义的注册逻辑（包括发送邮件等后置操作）
```

### 3. 数据库初始化

```python
# app/database/initializer.py
@Component()
class DatabaseInitializer(IStartupInitializer):

    def __init__(self, register_service: IRegisterService):
        """
        注入的是用户的 CustomRegisterService
        （框架通过 @ConditionalOnMissingBean 自动选择）
        """
        super().__init__(enabled=True)
        self.register_service = register_service

    async def _seed_initial_data(self):
        """使用自定义注册服务创建管理员"""
        user_request = UserInfo(
            user=User(
                user_id="admin",
                email="admin@example.com",
                password="admin123",
                username="admin"  # 自定义字段
            ),
            roles=[Role(code="ADMIN", name="管理员", status=True)]
        )

        # 调用用户自定义的 CustomRegisterService
        # - 自动会话管理
        # - 自动密码加密
        # - 自动角色分配
        # - 执行自定义后置操作（发送邮件等）
        result = await self.register_service.register(user_request)
        logger.info(f"✅ 管理员创建完成: {result.user.user_id}")
```

## 更多自定义示例

### 自定义密码加密器

```python
# app/config/security_config.py
from pyspring.security.authentication.contracts.password import IPasswordEncoder


class CustomPasswordEncoder(IPasswordEncoder):
    """自定义密码加密器（使用 Argon2）"""

    def __init__(self):
        self.pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")

    def encode(self, raw_password: str) -> str:
        return self.pwd_context.hash(raw_password)

    def verify(self, raw_password: str, hashed_password: str) -> bool:
        return self.pwd_context.verify(raw_password, hashed_password)


@Configuration
class CustomPasswordConfiguration:
    @Bean()  # 框架检测到后，跳过 BCryptPasswordEncoder
    def custom_password_encoder(self) -> IPasswordEncoder:
        return CustomPasswordEncoder()
```

### 自定义登录方式（短信验证码）

```python
# app/services/sms_login_provider.py
class SmsLoginProvider(ILoginProvider):
    """短信验证码登录提供者"""

    def support_type(self) -> str:
        return "sms"  # 登录类型标识

    async def authenticate(self, request: LoginRequest) -> Optional[int]:
        """验证短信验证码，返回用户ID"""
        phone = request.username
        code = request.password

        # 1. 从缓存获取验证码
        # 2. 验证验证码
        # 3. 查询用户
        # 4. 返回用户ID

        return user_id


@Configuration
class SmsLoginConfiguration:
    @Bean()  # 框架会收集所有 ILoginProvider 实现
    def sms_login_provider(self) -> ILoginProvider:
        return SmsLoginProvider()
```

**使用：**

```bash
curl -X POST http://localhost:8000/auth/login \
  -d '{"type": "sms", "username": "13800138000", "password": "123456"}'
```

## 框架 vs 用户自定义对比

### 使用框架默认实现

```python
# 不提供任何自定义实现
# 框架自动使用 DefaultRegisterService, DefaultLoginService
```

**特点：**

- ✅ 开箱即用
- ✅ 标准功能完整
- ❌ 无法扩展自定义字段
- ❌ 无法添加业务逻辑（发送邮件等）

### 使用用户自定义实现（推荐）

```python
# 提供 CustomRegisterService + @Bean()
@Configuration
class CustomRegisterServiceConfiguration:
    @Bean()
    def custom_register_service(...) -> IRegisterService:
        return CustomRegisterService(...)
```

**特点：**

- ✅ 完全控制业务逻辑
- ✅ 支持自定义字段
- ✅ 可添加后置操作
- ✅ 保持框架标准（会话管理、事务安全）
- ✅ 符合开闭原则（对扩展开放，对修改关闭）

## 最佳实践

### ✅ 推荐做法

1. **实现接口，注册 Bean**
   ```python
   class CustomService(IRegisterService):
       # 实现接口所有方法
   
   @Configuration
   class Config:
       @Bean()
       def custom_service(...) -> IRegisterService:
           return CustomService(...)
   ```

2. **面向接口编程**
   ```python
   def __init__(self, service: IRegisterService):  # 注入接口，不是具体类
       self.service = service
   ```

3. **参考框架实现**
    - 查看 `DefaultRegisterService` 源码
    - 复用框架的会话管理、事务处理
    - 在关键点插入自定义逻辑

4. **利用框架依赖注入**
   ```python
   def __init__(self, db: DBManagerService,  # 框架自动注入
                password_encoder: IPasswordEncoder):  # 自动注入（可被用户覆盖）
       pass
   ```

### ❌ 避免的做法

1. **不要直接依赖具体实现**
   ```python
   # ❌ 错误
   def __init__(self, service: DefaultRegisterService):
       pass
   
   # ✅ 正确
   def __init__(self, service: IRegisterService):
       pass
   ```

2. **不要绕过接口直接操作数据库**
   ```python
   # ❌ 错误：手动管理会话
   async with AsyncSessionLocal() as session:
       user = User(...)
       session.add(user)
       await session.commit()
   
   # ✅ 正确：使用服务
   await register_service.register(user_request)
   ```

3. **不要注册多个同接口实现（除非命名不同）**
   ```python
   # ❌ 错误：容器会混乱
   @Bean()
   def service1() -> IRegisterService: ...
   
   @Bean()
   def service2() -> IRegisterService: ...
   
   # ✅ 正确：使用命名
   @Bean(name="custom")
   def custom_service() -> IRegisterService: ...
   ```

## 常见问题

### Q1: 如何验证我的自定义实现生效了？

A: 查看日志，构造函数应输出：

```
🔧 注册自定义 IRegisterService 实现
📦 创建自定义 CustomRegisterService 实例
```

### Q2: 可以同时使用多个实现吗？

A: 可以，通过命名 Bean：

```python
@Bean(name="custom")
def custom_register() -> IRegisterService: ...


@Bean(name="default")
def default_register() -> IRegisterService: ...


# 使用时指定名称
@Inject(name="custom")


register_service: IRegisterService
```

### Q3: @ConditionalOnMissingBean 如何检测？

A: 按类型检测，不考虑名称：

```python
# 只要容器中有任何 IRegisterService 实例
# 就会跳过 @ConditionalOnMissingBean 的创建
```

### Q4: 用户实现必须实现所有方法吗？

A: 是的，必须实现接口的所有抽象方法。参考：

```python
# src/pyspring/security/authentication/services/register.py
class DefaultRegisterService(IRegisterService):
    async def register(self, request: UserInfo) -> UserInfo:
        ...
```

### Q5: Bean 是单例还是多例？

A: 默认单例（Singleton），全局共享一个实例。

## 总结

PySpring 的 `@ConditionalOnMissingBean` 机制实现了真正的"用户自定义扩展"：

1. **框架提供默认实现** - 开箱即用
2. **用户提供自定义实现** - 通过 `@Bean()` 注册
3. **框架自动选择** - 有用户实现用用户的，没有用默认的
4. **面向接口编程** - 解耦，易扩展
5. **符合开闭原则** - 对扩展开放，对修改关闭

**这就是 Spring Boot 的核心设计哲学！**
