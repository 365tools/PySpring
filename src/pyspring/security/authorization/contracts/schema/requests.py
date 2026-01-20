from typing import Optional

from pydantic import BaseModel, Field, EmailStr, model_validator, ConfigDict


class User(BaseModel):
    """用户模型"""
    id: Optional[int] = Field(default=None, description="数据库主键ID")
    user_id: Optional[str] = Field(default=None, description="用户唯一标识")
    first_name: Optional[str] = Field(default=None, description="用户名")
    last_name: Optional[str] = Field(default=None, description="用户姓")
    email: Optional[EmailStr] = Field(default=None, description="用户邮箱")
    password: Optional[str] = Field(default=None, min_length=6, description="用户密码")
    active: bool = Field(default=True, description="用户是否激活")
    deleted: bool = Field(default=False, description="用户是否删除")

    @model_validator(mode='after')
    def check_user_id_or_email(self):
        """验证 user_id 和 email 至少提供一个"""
        if not self.user_id and not self.email:
            raise ValueError("必须提供 user_id 或 email 其中之一")
        return self

    model_config = ConfigDict(from_attributes=True)


class Role(BaseModel):
    """角色模型"""
    id: Optional[int] = Field(None, description="数据库主键ID")
    code: str = Field(..., description="角色代码")
    name: str = Field(..., description="角色名称")
    description: str = Field(..., description="角色描述")
    status: bool = Field(default=True, description="角色状态")

    model_config = ConfigDict(from_attributes=True)


class Permission(BaseModel):
    """权限模型"""
    id: Optional[int] = Field(None, description="数据库主键ID")
    code: str = Field(..., description="权限代码")
    name: str = Field(..., description="权限名称")
    description: str = Field(..., description="权限描述")
    status: bool = Field(default=True, description="权限状态")

    model_config = ConfigDict(from_attributes=True)


class UserRole(BaseModel):
    """用户角色模型"""
    id: Optional[int] = Field(None, description="数据库主键ID")
    user_id: int = Field(..., description="用户ID")
    role_id: int = Field(..., description="角色ID")

    model_config = ConfigDict(from_attributes=True)


class RolePermission(BaseModel):
    """角色权限模型"""
    id: Optional[int] = Field(None, description="数据库主键ID")
    role_code: str = Field(..., description="角色代码")
    permission_code: str = Field(..., description="权限代码")

    model_config = ConfigDict(from_attributes=True)


class UserInfo(BaseModel):
    """注册用户模型"""
    user: User = Field(..., description="用户基本信息")
    roles: Optional[list[Role]] = Field(None, description="用户角色列表")
    permissions: Optional[list[Permission]] = Field(None, description="用户权限列表")

    model_config = ConfigDict(from_attributes=True)


class LoginRequest(BaseModel):
    """登录请求模型 - user_id 和 email 二选一"""
    user_id: Optional[str] = Field(default=None, description="用户唯一标识")
    email: Optional[EmailStr] = Field(default=None, description="用户邮箱")
    password: str = Field(..., min_length=6, description="用户密码")

    @model_validator(mode='after')
    def check_user_id_or_email(self):
        """验证 user_id 和 email 至少提供一个"""
        if not self.user_id and not self.email:
            raise ValueError("必须提供 user_id 或 email 其中之一")
        return self
