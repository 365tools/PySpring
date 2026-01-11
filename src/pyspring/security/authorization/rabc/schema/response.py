from typing import Optional, Any, List

from pydantic import BaseModel, Field


class Token(BaseModel):
    """Token模型"""
    access_token: str = Field(..., description="访问令牌")
    refresh_token: str = Field(..., description="刷新令牌")
    expires_in: int = Field(..., description="令牌有效期（秒）")
    token_type: str = Field(..., description="令牌类型")
    scope: Optional[List[Any]] = Field(default=None, description="令牌范围")
