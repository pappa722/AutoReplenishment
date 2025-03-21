from sqlalchemy import Column, Integer, ForeignKey, Date, Float, JSON
from sqlalchemy.orm import relationship
from app.models.base import BaseModel


class Sale(BaseModel):
    """销售记录模型"""
    __tablename__ = "sales"
    
    product_id = Column(Integer, ForeignKey("products.id"))
    quantity = Column(Integer, nullable=False)
    sale_date = Column(Date, nullable=False)
    sale_amount = Column(Float)
    customer_info = Column(JSON)
    
    # 关联产品
    product = relationship("Product", back_populates="sales")