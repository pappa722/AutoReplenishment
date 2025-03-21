from pydantic import BaseModel
from typing import Any, Dict, List, Optional

class BaseSchema(BaseModel):
    """
    基础模式类，所有其他模式类可以继承此类
    提供通用的方法和属性
    """
    
    class Config:
        # 允许通过属性访问
        orm_mode = True
        # 允许额外属性
        extra = "allow"