from typing import Optional, Dict, Any, List
from datetime import date, datetime
from pydantic import BaseModel, Field

from app.schemas.base import BaseSchema


class ReplenishmentBase(BaseModel):
    """补货记录基础模型"""
    product_id: int
    quantity: int
    order_date: date
    expected_arrival_date: Optional[date] = None
    status: Optional[str] = "pending"  # pending, shipped, received, cancelled


class ReplenishmentCreate(ReplenishmentBase):
    """创建补货记录模型"""
    pass


class ReplenishmentUpdate(BaseModel):
    """更新补货记录模型"""
    quantity: Optional[int] = None
    expected_arrival_date: Optional[date] = None
    status: Optional[str] = None


class Replenishment(ReplenishmentBase, BaseSchema):
    """补货记录响应模型"""
    id: int
    
    class Config:
        orm_mode = True


class ReplenishmentWithDetails(Replenishment):
    """带有产品详情的补货记录响应模型"""
    product_name: str
    product_sku: str
    product_category: str
    
    class Config:
        orm_mode = True


class ReplenishmentSummary(BaseModel):
    """补货汇总数据模型"""
    total_count: int
    pending_count: int
    shipped_count: int
    received_count: int
    cancelled_count: int
    total_quantity: int
    total_value: float


class ReplenishmentRecommendation(BaseModel):
    """补货建议模型"""
    product_id: int
    product_name: str
    product_sku: str
    current_stock: int
    safety_stock: int
    recommended_quantity: int
    priority: float  # 优先级分数
    category: str
    lead_time_days: int