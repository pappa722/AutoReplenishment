from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from sqlalchemy import func
import pandas as pd
import numpy as np
from sklearn.cluster import KMeans
from datetime import datetime, timedelta

from app.models.product import Product
from app.models.sale import Sale
from app.models.replenishment import Replenishment
from app.schemas.product import ProductCreate, ProductUpdate

class ProductService:
    """
    产品服务类：处理产品相关的业务逻辑
    """
    
    @staticmethod
    def get_product_by_id(db: Session, product_id: int) -> Optional[Product]:
        """
        通过ID获取产品
        
        Args:
            db: 数据库会话
            product_id: 产品ID
            
        Returns:
            产品对象，如果不存在则返回None
        """
        return db.query(Product).filter(Product.id == product_id).first()
    
    @staticmethod
    def get_product_by_sku(db: Session, sku: str) -> Optional[Product]:
        """
        通过SKU获取产品
        
        Args:
            db: 数据库会话
            sku: 产品SKU编码
            
        Returns:
            产品对象，如果不存在则返回None
        """
        return db.query(Product).filter(Product.sku == sku).first()
    
    @staticmethod
    def get_products(
        db: Session,
        skip: int = 0,
        limit: int = 100,
        category: Optional[str] = None,
        is_active: Optional[bool] = None,
        search: Optional[str] = None
    ) -> List[Product]:
        """
        获取产品列表
        
        Args:
            db: 数据库会话
            skip: 跳过的记录数
            limit: 返回的最大记录数
            category: 产品类别筛选
            is_active: 产品状态筛选
            search: 搜索关键词（匹配名称和SKU）
            
        Returns:
            产品对象列表
        """
        query = db.query(Product)
        
        if category:
            query = query.filter(Product.category == category)
        
        if is_active is not None:
            query = query.filter(Product.is_active == is_active)
        
        if search:
            search_pattern = f"%{search}%"
            query = query.filter(
                (Product.name.ilike(search_pattern)) |
                (Product.sku.ilike(search_pattern))
            )
        
        return query.offset(skip).limit(limit).all()
    
    @staticmethod
    def get_product_categories(db: Session) -> List[str]:
        """
        获取所有产品类别
        
        Args:
            db: 数据库会话
            
        Returns:
            产品类别列表
        """
        return [
            category[0] for category in 
            db.query(Product.category).distinct().all()
        ]
    
    @staticmethod
    def create_product(db: Session, product: ProductCreate) -> Product:
        """
        创建新产品
        
        Args:
            db: 数据库会话
            product: 产品创建模型
            
        Returns:
            新创建的产品对象
            
        Raises:
            HTTPException: 如果SKU已存在
        """
        # 检查SKU是否已存在
        if ProductService.get_product_by_sku(db, sku=product.sku):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="SKU已存在"
            )
        
        # 创建新产品对象
        db_product = Product(**product.dict())
        
        # 保存到数据库
        db.add(db_product)
        db.commit()
        db.refresh(db_product)
        
        return db_product
    
    @staticmethod
    def update_product(
        db: Session,
        product_id: int,
        product_update: ProductUpdate
    ) -> Product:
        """
        更新产品信息
        
        Args:
            db: 数据库会话
            product_id: 要更新的产品ID
            product_update: 产品更新模型
            
        Returns:
            更新后的产品对象
            
        Raises:
            HTTPException: 如果产品不存在
        """
        # 检查产品是否存在
        db_product = ProductService.get_product_by_id(db, product_id)
        if not db_product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="产品不存在"
            )
        
        # 如果要更新SKU，检查新SKU是否与其他产品冲突
        if product_update.sku and product_update.sku != db_product.sku:
            existing_product = ProductService.get_product_by_sku(
                db, 
                sku=product_update.sku
            )
            if existing_product:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="SKU已被其他产品使用"
                )
        
        # 更新产品信息
        update_data = product_update.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_product, field, value)
        
        db.commit()
        db.refresh(db_product)
        
        return db_product
    
    @staticmethod
    def delete_product(db: Session, product_id: int) -> Product:
        """
        删除产品（软删除）
        
        Args:
            db: 数据库会话
            product_id: 要删除的产品ID
            
        Returns:
            被删除的产品对象
            
        Raises:
            HTTPException: 如果产品不存在
        """
        # 检查产品是否存在
        db_product = ProductService.get_product_by_id(db, product_id)
        if not db_product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="产品不存在"
            )
        
        # 软删除产品（将is_active设置为False）
        db_product.is_active = False
        db.commit()
        db.refresh(db_product)
        
        return db_product
    
    @staticmethod
    def update_stock(
        db: Session,
        product_id: int,
        quantity_change: int,
        operation_type: str
    ) -> Product:
        """
        更新产品库存
        
        Args:
            db: 数据库会话
            product_id: 产品ID
            quantity_change: 库存变化量（正数表示增加，负数表示减少）
            operation_type: 操作类型（'sale'表示销售，'replenishment'表示补货）
            
        Returns:
            更新后的产品对象
            
        Raises:
            HTTPException: 如果产品不存在或库存不足
        """
        # 检查产品是否存在
        db_product = ProductService.get_product_by_id(db, product_id)
        if not db_product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="产品不存在"
            )
        
        # 如果是销售操作，检查库存是否充足
        if operation_type == 'sale' and db_product.stock_quantity < abs(quantity_change):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="库存不足"
            )
        
        # 更新库存
        db_product.stock_quantity += quantity_change
        
        # 如果是销售操作，更新销售相关信息
        if operation_type == 'sale':
            db_product.last_sale_date = datetime.now()
            # 假设销售价格是产品价格，更新销售总额
            sale_amount = abs(quantity_change) * db_product.price
            db_product.sales_amount += sale_amount
            db_product.sales_quantity += abs(quantity_change)
            # 更新利润率
            if db_product.sales_amount > 0:
                total_cost = db_product.sales_quantity * db_product.cost
                db_product.profit_margin = (db_product.sales_amount - total_cost) / db_product.sales_amount
        
        # 如果库存低于安全库存，标记需要补货
        if db_product.stock_quantity <= db_product.safety_stock:
            db_product.needs_replenishment = True
        else:
            db_product.needs_replenishment = False
        
        db.commit()
        db.refresh(db_product)
        
        return db_product
        
    @staticmethod
    def perform_abc_analysis(db: Session) -> Dict[str, Any]:
        """
        执行ABC分类分析
        基于销售额和利润率进行商品分类
        
        Args:
            db: 数据库会话
            
        Returns:
            包含分析结果的字典
        """
        # 获取所有产品数据
        products = db.query(Product).filter(Product.is_active == True).all()
        
        if not products:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="没有找到活跃的产品"
            )

        # 转换为DataFrame进行分析
        data = pd.DataFrame([{
            'id': p.id,
            'name': p.name,
            'sku': p.sku,
            'sales_amount': p.sales_amount,
            'profit_margin': p.profit_margin,
            'stock_quantity': p.stock_quantity
        } for p in products])

        # 确保有足够的数据进行聚类
        if len(data) < 3:
            # 如果数据少于3条，直接按销售额排序
            data['sales_rank'] = data['sales_amount'].rank(ascending=False)
            data.loc[data['sales_rank'] <= len(data) * 0.2, 'abc_class'] = 'A'
            data.loc[(data['sales_rank'] > len(data) * 0.2) & (data['sales_rank'] <= len(data) * 0.5), 'abc_class'] = 'B'
            data.loc[data['sales_rank'] > len(data) * 0.5, 'abc_class'] = 'C'
        else:
            # 使用K-means进行分类
            # 标准化特征
            features = data[['sales_amount', 'profit_margin']].copy()
            # 处理可能的NaN值
            features = features.fillna(0)
            
            # 使用K-means进行聚类
            kmeans = KMeans(n_clusters=3, random_state=42, n_init=10)
            data['cluster'] = kmeans.fit_predict(features)
            
            # 根据销售额均值对聚类进行排序
            cluster_means = data.groupby('cluster')['sales_amount'].mean().sort_values(ascending=False)
            cluster_ranks = {cluster: rank for rank, cluster in enumerate(['A', 'B', 'C'])}
            
            # 将聚类映射到ABC类别
            data['abc_class'] = data['cluster'].map({
                cluster_means.index[0]: 'A',
                cluster_means.index[1]: 'B',
                cluster_means.index[2]: 'C'
            })

        # 更新产品的ABC分类
        for _, row in data.iterrows():
            product = next((p for p in products if p.id == row['id']), None)
            if product:
                product.abc_class = row['abc_class']
        
        db.commit()

        return {
            'analysis_results': data[['id', 'name', 'sku', 'sales_amount', 'profit_margin', 'abc_class']].to_dict('records'),
            'summary': {
                'A_count': len(data[data['abc_class'] == 'A']),
                'B_count': len(data[data['abc_class'] == 'B']),
                'C_count': len(data[data['abc_class'] == 'C']),
                'total_products': len(data)
            }
        }

    @staticmethod
    def calculate_turnover_rate(db: Session, days: int = 30) -> Dict[str, Any]:
        """
        计算商品周转率
        
        Args:
            db: 数据库会话
            days: 计算周期（天数）
            
        Returns:
            包含周转率数据的字典
        """
        products = db.query(Product).filter(Product.is_active == True).all()
        
        if not products:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="没有找到活跃的产品"
            )

        turnover_data = []
        for product in products:
            # 计算周转率 = (销售数量 * 天数) / 平均库存
            avg_inventory = (product.current_stock + product.initial_stock) / 2 if product.initial_stock > 0 else product.current_stock
            if avg_inventory > 0:
                turnover_rate = (product.sales_quantity * days) / avg_inventory
            else:
                turnover_rate = 0

            turnover_data.append({
                'id': product.id,
                'name': product.name,
                'sku': product.sku,
                'turnover_rate': round(turnover_rate, 2),
                'sales_quantity': product.sales_quantity,
                'current_stock': product.stock_quantity,
                'avg_inventory': round(avg_inventory, 2)
            })

        # 转换为DataFrame进行分析
        df = pd.DataFrame(turnover_data)
        
        # 处理可能的NaN值
        df = df.fillna(0)
        
        return {
            'turnover_data': df.to_dict('records'),
            'summary': {
                'avg_turnover_rate': round(df['turnover_rate'].mean(), 2),
                'max_turnover_rate': round(df['turnover_rate'].max(), 2),
                'min_turnover_rate': round(df['turnover_rate'].min(), 2)
            }
        }

    @staticmethod
    def identify_slow_moving_items(db: Session, threshold_days: int = 30) -> Dict[str, Any]:
        """
        识别滞销商品
        
        Args:
            db: 数据库会话
            threshold_days: 判定为滞销的天数阈值
            
        Returns:
            包含滞销商品数据的字典
        """
        # 获取所有库存大于0的产品
        products = db.query(Product).filter(Product.is_active == True, Product.stock_quantity > 0).all()
        
        if not products:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="没有找到有库存的产品"
            )

        now = datetime.now()
        slow_moving_items = []
        
        for product in products:
            # 如果没有最后销售日期或者最后销售日期距今超过阈值天数
            if not product.last_sale_date or (now - product.last_sale_date).days > threshold_days:
                days_since_last_sale = (now - product.last_sale_date).days if product.last_sale_date else threshold_days
                
                slow_moving_items.append({
                    'id': product.id,
                    'name': product.name,
                    'sku': product.sku,
                    'days_since_last_sale': days_since_last_sale,
                    'current_stock': product.stock_quantity,
                    'stock_value': round(product.stock_quantity * product.price, 2),
                    'suggested_action': 'promote' if product.profit_margin > 0.2 else 'clearance'
                })

        # 计算滞销商品的总库存价值
        total_stock_value = sum(item['stock_value'] for item in slow_moving_items)
        
        return {
            'slow_moving_items': slow_moving_items,
            'total_count': len(slow_moving_items),
            'total_stock_value': round(total_stock_value, 2)
        }
        
    @staticmethod
    def calculate_dynamic_safety_stock(db: Session, service_level: float = 0.95) -> Dict[str, Any]:
        """
        计算动态安全库存
        
        Args:
            db: 数据库会话
            service_level: 服务水平（默认95%）
            
        Returns:
            包含安全库存计算结果的字典
        """
        from scipy import stats
        
        # 获取所有活跃产品
        products = db.query(Product).filter(Product.is_active == True).all()
        
        if not products:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="没有找到活跃的产品"
            )
            
        # 服务水平对应的z值
        z_score = stats.norm.ppf(service_level)
        
        safety_stock_data = []
        for product in products:
            # 假设我们有销售数据的标准差
            # 在实际应用中，应该从销售记录中计算
            # 这里使用一个简化的计算方式
            demand_std_dev = product.sales_quantity * 0.2  # 假设需求标准差为销售量的20%
            lead_time = product.lead_time_days
            
            # 计算安全库存 = Z * σ * √(提前期)
            safety_stock = z_score * demand_std_dev * np.sqrt(lead_time)
            safety_stock = max(round(safety_stock), 0)  # 确保安全库存非负
            
            # 更新产品的安全库存
            product.safety_stock = safety_stock
            
            safety_stock_data.append({
                'id': product.id,
                'name': product.name,
                'sku': product.sku,
                'safety_stock': safety_stock,
                'lead_time_days': lead_time,
                'current_stock': product.stock_quantity,
                'needs_replenishment': product.stock_quantity <= safety_stock
            })
        
        db.commit()
        
        return {
            'safety_stock_data': safety_stock_data,
            'service_level': service_level,
            'z_score': z_score,
            'total_products': len(safety_stock_data)
        }