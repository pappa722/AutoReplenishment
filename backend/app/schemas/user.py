from typing import Optional
from pydantic import BaseModel, EmailStr, validator
from app.schemas.base import BaseSchema

class TokenData(BaseModel):
    """用于解析JWT令牌的Schema"""
    username: Optional[str] = None

class UserBase(BaseModel):
    """用户基础Schema"""
    username: str
    email: EmailStr
    full_name: Optional[str] = None
    is_active: Optional[bool] = True
    is_superuser: Optional[bool] = False

class UserCreate(UserBase):
    """创建用户时的Schema"""
    password: str

    @validator('password')
    def password_min_length(cls, v):
        if len(v) < 8:
            raise ValueError('密码长度至少为8个字符')
        return v

class UserUpdate(UserBase):
    """更新用户信息时的Schema"""
    password: Optional[str] = None

class UserInDB(UserBase, BaseSchema):
    """数据库中的用户Schema"""
    hashed_password: str

class User(UserBase, BaseSchema):
    """返回给API的用户Schema"""
    pass