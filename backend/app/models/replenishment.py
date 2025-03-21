from sqlalchemy import Column, Integer, String, Date, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from app.models.base import BaseModel


class Replenishment(BaseModel):
    """补货记录模型"""
    __tablename__ = "replenishments"
    
    product_id = Column(Integer, ForeignKey("products.id"))
    quantity = Column(Integer, nullable=False)
    order_date = Column(Date, nullable=False)
    expected_arrival_date = Column(Date)
    status = Column(String, default="pending")  # pending, shipped, received
    received_at = Column(DateTime, nullable=True)
    actual_quantity = Column(Integer, nullable=True)
    notes = Column(String, nullable=True)
    supplier_info = Column(String, nullable=True)
    created_by = Column(Integer, nullable=True)
    updated_by = Column(Integer, nullable=True)
    
    # 关联产品
    product = relationship("Product", back_populates="replenishments")