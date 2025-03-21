from sqlalchemy import Column, String, Boolean
from app.models.base import BaseModel

class User(BaseModel):
    """用户模型"""
    __tablename__ = "users"
    
    username = Column(String, unique=True, index=True, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    full_name = Column(String)
    is_active = Column(Boolean, default=True)
    is_superuser = Column(Boolean, default=False)