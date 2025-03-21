from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from sqlalchemy import func, desc

from app.models.sale import Sale
from app.models.product import Product
from app.schemas.sale import SaleCreate, SaleUpdate
from app.services.product_service import ProductService

class SaleService:
    """
    销售服务类：处理销售记录相关的业务逻辑
    """
    
    @staticmethod
    def get_sale_by_id(db: Session, sale_id: int) -> Optional[Sale]:
        """
        通过ID获取销售记录
        
        Args:
            db: 数据库会话
            sale_id: 销售记录ID
            
        Returns:
            销售记录对象，如果不存在则返回None
        """
        return db.query(Sale).filter(Sale.id == sale_id).first()
    
    @staticmethod
    def get_sales(
        db: Session,
        skip: int = 0,
        limit: int = 100,
        product_id: Optional[int] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> List[Sale]:
        """
        获取销售记录列表
        
        Args:
            db: 数据库会话
            skip: 跳过的记录数
            limit: 返回的最大记录数
            product_id: 产品ID筛选
            start_date: 开始日期筛选
            end_date: 结束日期筛选
            
        Returns:
            销售记录对象列表
        """
        query = db.query(Sale)
        
        if product_id:
            query = query.filter(Sale.product_id == product_id)
        
        if start_date:
            query = query.filter(Sale.sale_date >= start_date)
        
        if end_date:
            query = query.filter(Sale.sale_date <= end_date)
        
        return query.order_by(desc(Sale.sale_date)).offset(skip).limit(limit).all()
    
    @staticmethod
    def create_sale(db: Session, sale: SaleCreate) -> Sale:
        """
        创建新销售记录
        
        Args:
            db: 数据库会话
            sale: 销售记录创建模型
            
        Returns:
            新创建的销售记录对象
            
        Raises:
            HTTPException: 如果产品不存在或库存不足
        """
        # 检查产品是否存在
        db_product = ProductService.get_product_by_id(db, sale.product_id)
        if not db_product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="产品不存在"
            )
        
        # 检查库存是否充足
        if db_product.stock_quantity < sale.quantity:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="库存不足"
            )
        
        # 计算销售总额
        sale_amount = sale.quantity * db_product.selling_price
        
        # 创建销售记录
        db_sale = Sale(
            product_id=sale.product_id,
            quantity=sale.quantity,
            sale_date=sale.sale_date or datetime.now(),
            sale_amount=sale_amount,
            customer_info=sale.customer_info
        )
        
        # 更新产品库存
        ProductService.update_stock(
            db,
            sale.product_id,
            -sale.quantity,  # 减少库存
            'sale'
        )
        
        # 保存销售记录
        db.add(db_sale)
        db.commit()
        db.refresh(db_sale)
        
        return db_sale
    
    @staticmethod
    def update_sale(
        db: Session,
        sale_id: int,
        sale_update: SaleUpdate
    ) -> Sale:
        """
        更新销售记录
        
        Args:
            db: 数据库会话
            sale_id: 销售记录ID
            sale_update: 销售记录更新模型
            
        Returns:
            更新后的销售记录对象
            
        Raises:
            HTTPException: 如果销售记录不存在或库存不足
        """
        # 检查销售记录是否存在
        db_sale = SaleService.get_sale_by_id(db, sale_id)
        if not db_sale:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="销售记录不存在"
            )
        
        # 如果要更新产品或数量，需要处理库存变化
        if sale_update.product_id or sale_update.quantity:
            # 获取当前产品
            current_product_id = db_sale.product_id
            current_quantity = db_sale.quantity
            
            # 确定新的产品ID和数量
            new_product_id = sale_update.product_id or current_product_id
            new_quantity = sale_update.quantity or current_quantity
            
            # 如果产品ID变化，需要处理两个产品的库存
            if new_product_id != current_product_id:
                # 恢复原产品库存
                ProductService.update_stock(
                    db,
                    current_product_id,
                    current_quantity,  # 增加库存
                    'sale_update'
                )
                
                # 检查新产品是否存在并减少其库存
                db_new_product = ProductService.get_product_by_id(db, new_product_id)
                if not db_new_product:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail="新产品不存在"
                    )
                
                if db_new_product.stock_quantity < new_quantity:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="新产品库存不足"
                    )
                
                ProductService.update_stock(
                    db,
                    new_product_id,
                    -new_quantity,  # 减少库存
                    'sale_update'
                )
                
                # 更新销售金额
                sale_amount = new_quantity * db_new_product.selling_price
                sale_update.sale_amount = sale_amount
                
            # 如果只是数量变化，需要调整当前产品库存
            elif new_quantity != current_quantity:
                # 计算库存变化量
                stock_change = current_quantity - new_quantity
                
                # 如果新数量大于原数量，需要检查库存是否充足
                if stock_change < 0:
                    db_product = ProductService.get_product_by_id(db, current_product_id)
                    if db_product.stock_quantity < abs(stock_change):
                        raise HTTPException(
                            status_code=status.HTTP_400_BAD_REQUEST,
                            detail="库存不足"
                        )
                
                # 更新库存
                ProductService.update_stock(
                    db,
                    current_product_id,
                    stock_change,
                    'sale_update'
                )
                
                # 更新销售金额
                db_product = ProductService.get_product_by_id(db, current_product_id)
                sale_amount = new_quantity * db_product.selling_price
                sale_update.sale_amount = sale_amount
        
        # 更新销售记录
        update_data = sale_update.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_sale, field, value)
        
        db.commit()
        db.refresh(db_sale)
        
        return db_sale
    
    @staticmethod
    def delete_sale(db: Session, sale_id: int) -> Sale:
        """
        删除销售记录
        
        Args:
            db: 数据库会话
            sale_id: 销售记录ID
            
        Returns:
            被删除的销售记录对象
            
        Raises:
            HTTPException: 如果销售记录不存在
        """
        # 检查销售记录是否存在
        db_sale = SaleService.get_sale_by_id(db, sale_id)
        if not db_sale:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="销售记录不存在"
            )
        
        # 恢复产品库存
        ProductService.update_stock(
            db,
            db_sale.product_id,
            db_sale.quantity,  # 增加库存
            'sale_delete'
        )
        
        # 删除销售记录
        db.delete(db_sale)
        db.commit()
        
        return db_sale
    
    @staticmethod
    def get_sales_analytics(
        db: Session,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        group_by: str = "day"
    ) -> List[Dict[str, Any]]:
        """
        获取销售分析数据
        
        Args:
            db: 数据库会话
            start_date: 开始日期
            end_date: 结束日期
            group_by: 分组方式（day, week, month）
            
        Returns:
            销售分析数据列表
        """
        # 默认时间范围为过去30天
        if not start_date:
            start_date = datetime.now() - timedelta(days=30)
        if not end_date:
            end_date = datetime.now()
        
        # 根据分组方式设置日期格式
        date_format = {
            "day": func.date_trunc('day', Sale.sale_date),
            "week": func.date_trunc('week', Sale.sale_date),
            "month": func.date_trunc('month', Sale.sale_date)
        }.get(group_by, func.date_trunc('day', Sale.sale_date))
        
        # 查询销售数据
        sales_data = db.query(
            date_format.label("date"),
            func.sum(Sale.sale_amount).label("total_amount"),
            func.sum(Sale.quantity).label("total_quantity"),
            func.count(Sale.id).label("transaction_count")
        ).filter(
            Sale.sale_date >= start_date,
            Sale.sale_date <= end_date
        ).group_by(
            "date"
        ).order_by(
            "date"
        ).all()
        
        # 格式化结果
        result = []
        for data in sales_data:
            result.append({
                "date": data.date.strftime("%Y-%m-%d"),
                "total_amount": float(data.total_amount),
                "total_quantity": int(data.total_quantity),
                "transaction_count": int(data.transaction_count)
            })
        
        return result
    
    @staticmethod
    def get_top_selling_products(
        db: Session,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        获取热销产品排行
        
        Args:
            db: 数据库会话
            start_date: 开始日期
            end_date: 结束日期
            limit: 返回的记录数
            
        Returns:
            热销产品数据列表
        """
        # 默认时间范围为过去30天
        if not start_date:
            start_date = datetime.now() - timedelta(days=30)
        if not end_date:
            end_date = datetime.now()
        
        # 查询热销产品数据
        top_products = db.query(
            Sale.product_id,
            Product.name,
            Product.sku,
            Product.category,
            func.sum(Sale.quantity).label("total_quantity"),
            func.sum(Sale.sale_amount).label("total_amount"),
            func.count(Sale.id).label("sale_count")
        ).join(
            Product, Sale.product_id == Product.id
        ).filter(
            Sale.sale_date >= start_date,
            Sale.sale_date <= end_date
        ).group_by(
            Sale.product_id,
            Product.name,
            Product.sku,
            Product.category
        ).order_by(
            desc("total_quantity")
        ).limit(limit).all()
        
        # 格式化结果
        result = []
        for product in top_products:
            result.append({
                "product_id": product.product_id,
                "name": product.name,
                "sku": product.sku,
                "category": product.category,
                "total_quantity": int(product.total_quantity),
                "total_amount": float(product.total_amount),
                "sale_count": int(product.sale_count)
            })
        
        return result