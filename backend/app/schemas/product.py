from typing import Optional, List, Any, Dict
from pydantic import BaseModel, validator, Field
from datetime import date
from enum import Enum
from app.schemas.base import BaseSchema

class ProductBase(BaseModel):
    """产品基础Schema"""
    sku: str
    name: str
    category: str
    subcategory: Optional[str] = None
    price: float = Field(..., gt=0)
    cost: float = Field(..., gt=0)
    inventory_level: int = Field(default=0, ge=0)
    min_stock: int = Field(default=0, ge=0)
    max_stock: int = Field(default=0, ge=0)
    lead_time_days: int = Field(default=1, gt=0)

    @validator('max_stock')
    def max_stock_greater_than_min(cls, v, values):
        if 'min_stock' in values and v < values['min_stock']:
            raise ValueError('最大库存必须大于或等于最小库存')
        return v

class ProductCreate(ProductBase):
    """创建产品时的Schema"""
    pass

class ProductUpdate(BaseModel):
    """更新产品信息时的Schema"""
    sku: Optional[str] = None
    name: Optional[str] = None
    category: Optional[str] = None
    subcategory: Optional[str] = None
    price: Optional[float] = None
    cost: Optional[float] = None
    inventory_level: Optional[int] = None
    min_stock: Optional[int] = None
    max_stock: Optional[int] = None
    lead_time_days: Optional[int] = None

class Product(ProductBase, BaseSchema):
    """返回给API的产品Schema"""
    pass

class SaleBase(BaseModel):
    """销售记录基础Schema"""
    product_id: int
    quantity: int = Field(..., gt=0)
    sale_date: date

class SaleCreate(SaleBase):
    """创建销售记录时的Schema"""
    pass

class SaleUpdate(BaseModel):
    """更新销售记录时的Schema"""
    quantity: Optional[int] = None
    sale_date: Optional[date] = None

class Sale(SaleBase, BaseSchema):
    """返回给API的销售记录Schema"""
    product: Optional[Product] = None

class ReplenishmentBase(BaseModel):
    """补货记录基础Schema"""
    product_id: int
    quantity: int = Field(..., gt=0)
    order_date: date
    expected_arrival_date: Optional[date] = None
    status: str = "pending"

    @validator('status')
    def status_valid(cls, v):
        allowed_statuses = ["pending", "shipped", "received"]
        if v not in allowed_statuses:
            raise ValueError(f'状态必须是以下之一: {", ".join(allowed_statuses)}')
        return v

class ReplenishmentCreate(ReplenishmentBase):
    """创建补货记录时的Schema"""
    pass

class ReplenishmentUpdate(BaseModel):
    """更新补货记录时的Schema"""
    quantity: Optional[int] = None
    expected_arrival_date: Optional[date] = None
    status: Optional[str] = None

class Replenishment(ReplenishmentBase, BaseSchema):
    """返回给API的补货记录Schema"""
    product: Optional[Product] = None


class ProductWithStats(Product):
    """带有销售统计数据的产品Schema"""
    sales_count: int = 0
    sales_amount: float = 0
    average_daily_sales: float = 0
    days_to_stockout: Optional[float] = None
    turnover_rate: Optional[float] = None


class StockOperationType(str, Enum):
    """库存操作类型枚举"""
    ADD = "add"
    SUBTRACT = "subtract"
    SET = "set"


class ProductStockUpdate(BaseModel):
    """更新产品库存的Schema"""
    quantity: int
    operation_type: StockOperationType = StockOperationType.ADD