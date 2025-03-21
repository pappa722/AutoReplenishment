from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from sqlalchemy import func, desc

from app.models.replenishment import Replenishment
from app.models.product import Product
from app.schemas.replenishment import ReplenishmentCreate, ReplenishmentUpdate
from app.services.product_service import ProductService

class ReplenishmentService:
    """
    补货服务类：处理补货记录相关的业务逻辑
    """
    
    @staticmethod
    def get_replenishment_by_id(db: Session, replenishment_id: int) -> Optional[Replenishment]:
        """
        通过ID获取补货记录
        
        Args:
            db: 数据库会话
            replenishment_id: 补货记录ID
            
        Returns:
            补货记录对象，如果不存在则返回None
        """
        return db.query(Replenishment).filter(Replenishment.id == replenishment_id).first()
    
    @staticmethod
    def get_replenishments(
        db: Session,
        skip: int = 0,
        limit: int = 100,
        product_id: Optional[int] = None,
        status: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> List[Replenishment]:
        """
        获取补货记录列表
        
        Args:
            db: 数据库会话
            skip: 跳过的记录数
            limit: 返回的最大记录数
            product_id: 产品ID筛选
            status: 状态筛选（pending, received, cancelled）
            start_date: 开始日期筛选
            end_date: 结束日期筛选
            
        Returns:
            补货记录对象列表
        """
        query = db.query(Replenishment)
        
        if product_id:
            query = query.filter(Replenishment.product_id == product_id)
        
        if status:
            query = query.filter(Replenishment.status == status)
        
        if start_date:
            query = query.filter(Replenishment.created_at >= start_date)
        
        if end_date:
            query = query.filter(Replenishment.created_at <= end_date)
        
        return query.order_by(desc(Replenishment.created_at)).offset(skip).limit(limit).all()
    
    @staticmethod
    def create_replenishment(db: Session, replenishment: ReplenishmentCreate) -> Replenishment:
        """
        创建新补货记录
        
        Args:
            db: 数据库会话
            replenishment: 补货记录创建模型
            
        Returns:
            新创建的补货记录对象
            
        Raises:
            HTTPException: 如果产品不存在
        """
        # 检查产品是否存在
        db_product = ProductService.get_product_by_id(db, replenishment.product_id)
        if not db_product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="产品不存在"
            )
        
        # 创建补货记录
        db_replenishment = Replenishment(
            product_id=replenishment.product_id,
            quantity=replenishment.quantity,
            status="pending",  # 初始状态为待处理
            expected_arrival=replenishment.expected_arrival,
            supplier_info=replenishment.supplier_info,
            notes=replenishment.notes
        )
        
        # 保存补货记录
        db.add(db_replenishment)
        db.commit()
        db.refresh(db_replenishment)
        
        return db_replenishment
    
    @staticmethod
    def update_replenishment(
        db: Session,
        replenishment_id: int,
        replenishment_update: ReplenishmentUpdate
    ) -> Replenishment:
        """
        更新补货记录
        
        Args:
            db: 数据库会话
            replenishment_id: 补货记录ID
            replenishment_update: 补货记录更新模型
            
        Returns:
            更新后的补货记录对象
            
        Raises:
            HTTPException: 如果补货记录不存在或产品不存在
        """
        # 检查补货记录是否存在
        db_replenishment = ReplenishmentService.get_replenishment_by_id(db, replenishment_id)
        if not db_replenishment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="补货记录不存在"
            )
        
        # 如果要更新产品，检查新产品是否存在
        if replenishment_update.product_id:
            db_product = ProductService.get_product_by_id(db, replenishment_update.product_id)
            if not db_product:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="产品不存在"
                )
        
        # 更新补货记录
        update_data = replenishment_update.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_replenishment, field, value)
        
        db.commit()
        db.refresh(db_replenishment)
        
        return db_replenishment
    
    @staticmethod
    def confirm_replenishment(
        db: Session,
        replenishment_id: int,
        actual_quantity: Optional[int] = None
    ) -> Replenishment:
        """
        确认补货到货
        
        Args:
            db: 数据库会话
            replenishment_id: 补货记录ID
            actual_quantity: 实际到货数量，如果不提供则使用原计划数量
            
        Returns:
            更新后的补货记录对象
            
        Raises:
            HTTPException: 如果补货记录不存在或状态不是待处理
        """
        # 检查补货记录是否存在
        db_replenishment = ReplenishmentService.get_replenishment_by_id(db, replenishment_id)
        if not db_replenishment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="补货记录不存在"
            )
        
        # 检查补货记录状态
        if db_replenishment.status != "pending":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"补货记录状态为{db_replenishment.status}，无法确认到货"
            )
        
        # 确定实际到货数量
        final_quantity = actual_quantity if actual_quantity is not None else db_replenishment.quantity
        
        # 更新补货记录状态
        db_replenishment.status = "received"
        db_replenishment.received_at = datetime.now()
        db_replenishment.actual_quantity = final_quantity
        
        # 更新产品库存
        ProductService.update_stock(
            db,
            db_replenishment.product_id,
            final_quantity,  # 增加库存
            'replenishment'
        )
        
        # 更新产品的补货需求状态
        db_product = ProductService.get_product_by_id(db, db_replenishment.product_id)
        if db_product.stock_quantity > db_product.safety_stock:
            db_product.needs_replenishment = False
            db.add(db_product)
        
        db.commit()
        db.refresh(db_replenishment)
        
        return db_replenishment
    
    @staticmethod
    def cancel_replenishment(
        db: Session,
        replenishment_id: int,
        cancel_reason: Optional[str] = None
    ) -> Replenishment:
        """
        取消补货记录
        
        Args:
            db: 数据库会话
            replenishment_id: 补货记录ID
            cancel_reason: 取消原因
            
        Returns:
            更新后的补货记录对象
            
        Raises:
            HTTPException: 如果补货记录不存在或状态不是待处理
        """
        # 检查补货记录是否存在
        db_replenishment = ReplenishmentService.get_replenishment_by_id(db, replenishment_id)
        if not db_replenishment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="补货记录不存在"
            )
        
        # 检查补货记录状态
        if db_replenishment.status != "pending":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"补货记录状态为{db_replenishment.status}，无法取消"
            )
        
        # 更新补货记录状态
        db_replenishment.status = "cancelled"
        db_replenishment.notes = cancel_reason or db_replenishment.notes
        
        db.commit()
        db.refresh(db_replenishment)
        
        return db_replenishment
    
    @staticmethod
    def get_replenishment_analytics(
        db: Session,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        获取补货分析数据
        
        Args:
            db: 数据库会话
            start_date: 开始日期
            end_date: 结束日期
            
        Returns:
            补货分析数据
        """
        # 默认时间范围为过去30天
        if not start_date:
            start_date = datetime.now() - timedelta(days=30)
        if not end_date:
            end_date = datetime.now()
        
        # 查询各状态的补货记录数量
        status_counts = db.query(
            Replenishment.status,
            func.count(Replenishment.id).label("count")
        ).filter(
            Replenishment.created_at >= start_date,
            Replenishment.created_at <= end_date
        ).group_by(
            Replenishment.status
        ).all()
        
        # 查询补货总量和平均到货时间
        replenishment_stats = db.query(
            func.sum(Replenishment.quantity).label("total_quantity"),
            func.avg(
                func.extract('epoch', Replenishment.received_at) - 
                func.extract('epoch', Replenishment.created_at)
            ).label("avg_lead_time")
        ).filter(
            Replenishment.created_at >= start_date,
            Replenishment.created_at <= end_date,
            Replenishment.status == "received"
        ).first()
        
        # 格式化结果
        status_data = {status: 0 for status in ["pending", "received", "cancelled"]}
        for status, count in status_counts:
            status_data[status] = count
        
        return {
            "status_counts": status_data,
            "total_quantity": int(replenishment_stats.total_quantity or 0),
            "avg_lead_time_hours": float(replenishment_stats.avg_lead_time or 0) / 3600 if replenishment_stats.avg_lead_time else 0
        }
    
    @staticmethod
    def get_products_needing_replenishment(
        db: Session,
        skip: int = 0,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        获取需要补货的产品列表
        
        Args:
            db: 数据库会话
            skip: 跳过的记录数
            limit: 返回的最大记录数
            
        Returns:
            需要补货的产品列表
        """
        # 查询需要补货的产品
        products = db.query(
            Product
        ).filter(
            Product.is_active == True,
            Product.needs_replenishment == True
        ).order_by(
            # 优先级：库存量/安全库存比例升序
            (Product.stock_quantity / Product.safety_stock).asc()
        ).offset(skip).limit(limit).all()
        
        # 格式化结果
        result = []
        for product in products:
            # 计算建议补货数量：目标库存 - 当前库存
            suggested_quantity = max(
                0, 
                product.target_stock - product.stock_quantity
            )
            
            # 检查是否有未完成的补货
            pending_replenishments = db.query(
                func.sum(Replenishment.quantity).label("total")
            ).filter(
                Replenishment.product_id == product.id,
                Replenishment.status == "pending"
            ).first()
            
            pending_quantity = pending_replenishments.total or 0
            
            result.append({
                "product_id": product.id,
                "name": product.name,
                "sku": product.sku,
                "category": product.category,
                "current_stock": product.stock_quantity,
                "safety_stock": product.safety_stock,
                "target_stock": product.target_stock,
                "suggested_quantity": int(suggested_quantity),
                "pending_quantity": int(pending_quantity),
                "stock_ratio": round(product.stock_quantity / product.safety_stock, 2) if product.safety_stock > 0 else 0
            })
        
        return result