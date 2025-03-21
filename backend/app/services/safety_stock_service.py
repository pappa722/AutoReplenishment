from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import numpy as np
from scipy import stats
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from fastapi import HTTPException, status

from app.models.product import Product
from app.models.sale import Sale
from app.services.forecast_service import ForecastService


class SafetyStockService:
    """
    安全库存服务：计算和管理商品安全库存水平
    """
    
    @staticmethod
    def calculate_safety_stock(
        db: Session,
        product_id: int,
        service_level: float = 0.95,
        history_months: int = 6,
        lead_time_days: int = 7,
        consider_seasonality: bool = True
    ) -> Dict[str, Any]:
        """
        计算商品的安全库存水平
        
        Args:
            db: 数据库会话
            product_id: 产品ID
            service_level: 服务水平（默认0.95，即95%）
            history_months: 历史数据月数（默认6个月）
            lead_time_days: 补货提前期（天数）
            consider_seasonality: 是否考虑季节性因素
            
        Returns:
            包含安全库存计算结果的字典
            
        Raises:
            HTTPException: 如果产品不存在或数据不足
        """
        # 检查产品是否存在
        product = db.query(Product).filter(Product.id == product_id).first()
        if not product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="产品不存在"
            )
        
        # 获取历史销售数据
        start_date = datetime.now() - timedelta(days=history_months * 30)
        sales_data = db.query(
            func.date(Sale.sale_date).label("date"),
            func.sum(Sale.quantity).label("quantity")
        ).filter(
            Sale.product_id == product_id,
            Sale.sale_date >= start_date
        ).group_by(
            func.date(Sale.sale_date)
        ).order_by(
            func.date(Sale.sale_date)
        ).all()
        
        # 检查是否有足够的销售数据
        if len(sales_data) < 30:  # 至少需要30天的数据
            return {
                "product_id": product_id,
                "current_safety_stock": product.safety_stock,
                "suggested_safety_stock": product.safety_stock,  # 数据不足时保持原值
                "change_percentage": 0,
                "confidence_level": 0.5,
                "reason": "历史销售数据不足，无法计算可靠的安全库存水平"
            }
        
        # 提取销售数量数据
        daily_sales = [sale.quantity for sale in sales_data]
        
        # 计算需求标准差
        demand_std = np.std(daily_sales)
        
        # 根据服务水平获取Z值（标准正态分布的分位数）
        z_score = stats.norm.ppf(service_level)
        
        # 计算安全库存
        # 基本公式: 安全库存 = Z * 需求标准差 * sqrt(补货提前期)
        safety_stock_base = z_score * demand_std * np.sqrt(lead_time_days)
        
        # 考虑季节性因素（如果需要）
        seasonality_factor = 1.0
        if consider_seasonality:
            # 使用预测服务检测季节性
            try:
                seasonality_info = ForecastService.detect_seasonality(
                    db, product_id, history_months
                )
                
                if seasonality_info["has_seasonality"]:
                    # 根据季节性强度调整因子
                    seasonality_strength = seasonality_info["seasonality_strength"]
                    # 季节性越强，因子越大
                    seasonality_factor = 1.0 + min(seasonality_strength * 0.5, 0.5)
                    
                    # 考虑当前是否处于高峰期
                    if seasonality_info["is_peak_season"]:
                        seasonality_factor *= 1.2
            except Exception:
                # 如果季节性检测失败，使用默认因子
                seasonality_factor = 1.0
        
        # 应用季节性因子
        suggested_safety_stock = int(safety_stock_base * seasonality_factor)
        
        # 确保安全库存至少为1
        suggested_safety_stock = max(1, suggested_safety_stock)
        
        # 计算变化百分比
        current_safety_stock = product.safety_stock or 1  # 避免除以零
        change_percentage = (suggested_safety_stock - current_safety_stock) / current_safety_stock
        
        # 计算置信度（基于数据量和变异系数）
        cv = demand_std / np.mean(daily_sales) if np.mean(daily_sales) > 0 else 1
        data_points_factor = min(len(sales_data) / 180, 1)  # 数据越多越好，最高1
        cv_factor = max(1 - cv, 0.3)  # 变异系数越小越好，最低0.3
        confidence_level = data_points_factor * cv_factor
        
        # 生成调整建议原因
        reason = SafetyStockService._generate_adjustment_reason(
            current_safety_stock,
            suggested_safety_stock,
            change_percentage,
            service_level,
            seasonality_factor,
            cv
        )
        
        return {
            "product_id": product_id,
            "current_safety_stock": current_safety_stock,
            "suggested_safety_stock": suggested_safety_stock,
            "change_percentage": change_percentage,
            "confidence_level": confidence_level,
            "reason": reason
        }
    
    @staticmethod
    def _generate_adjustment_reason(
        current: int,
        suggested: int,
        change_percentage: float,
        service_level: float,
        seasonality_factor: float,
        cv: float
    ) -> str:
        """
        生成安全库存调整建议的原因说明
        
        Args:
            current: 当前安全库存
            suggested: 建议安全库存
            change_percentage: 变化百分比
            service_level: 服务水平
            seasonality_factor: 季节性因子
            cv: 变异系数
            
        Returns:
            调整建议原因说明
        """
        reasons = []
        
        # 根据变化方向生成基本原因
        if change_percentage > 0.2:
            reasons.append(f"建议增加安全库存以满足{service_level*100:.0f}%的服务水平")
            if cv > 0.5:
                reasons.append("需求波动较大")
            if seasonality_factor > 1.1:
                reasons.append("考虑了季节性因素")
        elif change_percentage < -0.2:
            reasons.append(f"当前库存过高，可以降低以维持{service_level*100:.0f}%的服务水平")
            if cv < 0.3:
                reasons.append("需求相对稳定")
        else:
            reasons.append("当前安全库存水平基本合理")
        
        # 根据变异系数添加建议
        if cv > 0.8:
            reasons.append("建议关注需求预测以减少不确定性")
        
        return "；".join(reasons) + "。"
    
    @staticmethod
    def batch_calculate_safety_stock(
        db: Session,
        params: Dict[str, Any],
        skip: int = 0,
        limit: int = 100,
        category: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        批量计算安全库存
        
        Args:
            db: 数据库会话
            params: 计算参数
            skip: 跳过的记录数
            limit: 返回的最大记录数
            category: 产品类别筛选
            
        Returns:
            包含计算结果列表和总数的字典
        """
        # 提取参数
        service_level = float(params.get("serviceLevel", 0.95))
        history_months = int(params.get("historyPeriod", 6))
        lead_time_days = int(params.get("leadTime", 7))
        consider_seasonality = params.get("considerSeasonality", True)
        
        # 查询活跃产品
        query = db.query(Product).filter(Product.is_active == True)
        
        # 应用类别筛选
        if category:
            query = query.filter(Product.category == category)
        
        # 获取总数
        total = query.count()
        
        # 获取分页产品
        products = query.offset(skip).limit(limit).all()
        
        # 计算每个产品的安全库存
        results = []
        for product in products:
            calculation = SafetyStockService.calculate_safety_stock(
                db,
                product.id,
                service_level,
                history_months,
                lead_time_days,
                consider_seasonality
            )
            
            # 添加产品信息
            results.append({
                "productId": product.id,
                "productCode": product.sku,
                "productName": product.name,
                "currentSafetyStock": calculation["current_safety_stock"],
                "suggestedSafetyStock": calculation["suggested_safety_stock"],
                "changePercentage": calculation["change_percentage"],
                "confidenceLevel": calculation["confidence_level"],
                "reason": calculation["reason"]
            })
        
        return {
            "total": total,
            "items": results
        }
    
    @staticmethod
    def update_safety_stock(
        db: Session,
        product_id: int,
        safety_stock: int
    ) -> Product:
        """
        更新产品的安全库存
        
        Args:
            db: 数据库会话
            product_id: 产品ID
            safety_stock: 新的安全库存值
            
        Returns:
            更新后的产品对象
            
        Raises:
            HTTPException: 如果产品不存在
        """
        # 检查产品是否存在
        product = db.query(Product).filter(Product.id == product_id).first()
        if not product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="产品不存在"
            )
        
        # 更新安全库存
        product.safety_stock = safety_stock
        
        # 检查是否需要更新补货需求状态
        if product.stock_quantity < safety_stock:
            product.needs_replenishment = True
        
        # 保存更新
        db.add(product)
        db.commit()
        db.refresh(product)
        
        return product
    
    @staticmethod
    def auto_update_all_safety_stocks(
        db: Session,
        service_level: float = 0.95,
        history_months: int = 6,
        lead_time_days: int = 7,
        consider_seasonality: bool = True,
        confidence_threshold: float = 0.7
    ) -> Dict[str, Any]:
        """
        自动更新所有产品的安全库存
        
        Args:
            db: 数据库会话
            service_level: 服务水平
            history_months: 历史数据月数
            lead_time_days: 补货提前期（天数）
            consider_seasonality: 是否考虑季节性因素
            confidence_threshold: 置信度阈值，只更新高于此阈值的计算结果
            
        Returns:
            更新结果统计
        """
        # 查询所有活跃产品
        products = db.query(Product).filter(Product.is_active == True).all()
        
        total_count = len(products)
        updated_count = 0
        skipped_count = 0
        
        for product in products:
            # 计算安全库存
            calculation = SafetyStockService.calculate_safety_stock(
                db,
                product.id,
                service_level,
                history_months,
                lead_time_days,
                consider_seasonality
            )
            
            # 只更新高置信度的结果
            if calculation["confidence_level"] >= confidence_threshold:
                product.safety_stock = calculation["suggested_safety_stock"]
                
                # 检查是否需要更新补货需求状态
                if product.stock_quantity < product.safety_stock:
                    product.needs_replenishment = True
                
                db.add(product)
                updated_count += 1
            else:
                skipped_count += 1
        
        # 提交所有更改
        db.commit()
        
        return {
            "total_products": total_count,
            "updated_count": updated_count,
            "skipped_count": skipped_count
        }