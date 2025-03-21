from sqlalchemy import Column, String, Float, Integer, Boolean, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.models.base import BaseModel

class Product(BaseModel):
    """产品模型"""
    __tablename__ = "products"
    
    sku = Column(String, unique=True, index=True, nullable=False)
    name = Column(String, nullable=False)
    category = Column(String, nullable=False)
    subcategory = Column(String)
    price = Column(Float, nullable=False)
    cost = Column(Float, nullable=False)
    inventory_level = Column(Integer, default=0)
    min_stock = Column(Integer, default=0)
    max_stock = Column(Integer, default=0)
    lead_time_days = Column(Integer, default=1)  # 补货提前期（天）
    safety_stock = Column(Integer, default=0)  # 安全库存
    is_active = Column(Boolean, default=True)  # 产品状态
    needs_replenishment = Column(Boolean, default=False)  # 是否需要补货
    last_sale_date = Column(DateTime)  # 最后一次销售日期
    sales_amount = Column(Float, default=0)  # 销售总额
    sales_quantity = Column(Integer, default=0)  # 销售数量
    profit_margin = Column(Float, default=0)  # 利润率
    stock_quantity = Column(Integer, default=0)  # 当前库存
    initial_stock = Column(Integer, default=0)  # 期初库存
    current_stock = Column(Integer, default=0)  # 当前库存
    created_at = Column(DateTime, server_default=func.now())  # 创建时间
    updated_at = Column(DateTime, onupdate=func.now())  # 更新时间
    
    # 关联销售记录
    sales = relationship("Sale", back_populates="product")
    
    # 关联补货记录
    replenishments = relationship("Replenishment", back_populates="product")
