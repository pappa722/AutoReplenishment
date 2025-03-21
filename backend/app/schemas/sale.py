from typing import Optional
from datetime import date
from pydantic import BaseModel


class SaleBase(BaseModel):
    """销售记录基础模型"""
    product_id: int
    quantity: int
    sale_date: Optional[date] = None
    sale_amount: Optional[float] = None
    customer_info: Optional[dict] = None


class SaleCreate(SaleBase):
    """创建销售记录模型"""
    pass


class SaleUpdate(BaseModel):
    """更新销售记录模型"""
    product_id: Optional[int] = None
    quantity: Optional[int] = None
    sale_date: Optional[date] = None
    sale_amount: Optional[float] = None
    customer_info: Optional[dict] = None


class Sale(SaleBase):
    """销售记录返回模型"""
    id: int
    
    class Config:
        orm_mode = True


class SaleWithDetails(Sale):
    """带有详细信息的销售记录返回模型"""
    product_name: Optional[str] = None
    product_sku: Optional[str] = None
    product_category: Optional[str] = None


class SaleSummary(BaseModel):
    """销售汇总数据模型"""
    total_sales: float
    total_quantity: int
    average_order_value: float
    total_orders: int