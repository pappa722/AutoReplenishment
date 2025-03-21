from typing import Dict, List, Any, Optional
import pandas as pd
import numpy as np
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
import joblib
import os
from datetime import datetime, timedelta
from statsmodels.tsa.statespace.sarimax import SARIMAX
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

from app.models.product import Product
from app.models.sale import Sale

class ForecastService:
    """
    销量预测服务：负责销量预测模型的训练、评估和预测
    """
    
    MODELS_DIR = "app/models/ml"
    
    @staticmethod
    def _ensure_model_dir():
        """确保模型保存目录存在"""
        os.makedirs(ForecastService.MODELS_DIR, exist_ok=True)
    
    @staticmethod
    def _get_sales_data(db: Session, product_id: int, days: int = 90) -> pd.DataFrame:
        """
        获取指定产品的销售数据
        
        Args:
            db: 数据库会话
            product_id: 产品ID
            days: 获取最近多少天的数据
            
        Returns:
            包含销售数据的DataFrame
        """
        # 计算开始日期
        start_date = datetime.now() - timedelta(days=days)
        
        # 查询销售数据
        sales = db.query(Sale).filter(
            Sale.product_id == product_id,
            Sale.sale_date >= start_date
        ).order_by(Sale.sale_date).all()
        
        if not sales:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"没有找到产品ID {product_id} 的销售数据"
            )
        
        # 转换为DataFrame
        sales_data = pd.DataFrame([
            {
                'date': sale.sale_date,
                'quantity': sale.quantity
            }
            for sale in sales
        ])
        
        # 设置日期为索引
        sales_data['date'] = pd.to_datetime(sales_data['date'])
        sales_data.set_index('date', inplace=True)
        
        # 按日期聚合
        daily_sales = sales_data.resample('D').sum()
        
        # 填充缺失值为0
        daily_sales = daily_sales.fillna(0)
        
        return daily_sales
    
    @staticmethod
    def _extract_features(df: pd.DataFrame) -> pd.DataFrame:
        """
        从时间序列数据中提取特征
        
        Args:
            df: 销售数据DataFrame
            
        Returns:
            带有时间特征的DataFrame
        """
        df_features = df.copy()
        
        # 添加日期特征
        df_features['day_of_week'] = df_features.index.dayofweek
        df_features['day_of_month'] = df_features.index.day
        df_features['month'] = df_features.index.month
        df_features['quarter'] = df_features.index.quarter
        df_features['year'] = df_features.index.year
        df_features['is_weekend'] = df_features['day_of_week'].isin([5, 6]).astype(int)
        
        # 添加滞后特征
        for lag in [1, 7, 14, 30]:
            df_features[f'lag_{lag}'] = df_features['quantity'].shift(lag)
        
        # 添加滚动均值特征
        for window in [7, 14, 30]:
            df_features[f'rolling_mean_{window}'] = df_features['quantity'].rolling(window=window).mean()
        
        # 填充缺失值
        df_features = df_features.fillna(0)
        
        return df_features
    
    @staticmethod
    def train_sarima_model(db: Session, product_id: int) -> Dict[str, Any]:
        """
        训练SARIMA模型
        
        Args:
            db: 数据库会话
            product_id: 产品ID
            
        Returns:
            包含模型训练结果的字典
        """
        # 获取销售数据
        sales_data = ForecastService._get_sales_data(db, product_id)
        
        # 检查数据量是否足够
        if len(sales_data) < 30:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="销售数据不足，需要至少30天的数据来训练SARIMA模型"
            )
        
        try:
            # 使用SARIMA模型 (1,1,1)x(1,1,1,7) - 适用于有周期性的时间序列
            model = SARIMAX(
                sales_data['quantity'],
                order=(1, 1, 1),
                seasonal_order=(1, 1, 1, 7),
                enforce_stationarity=False,
                enforce_invertibility=False
            )
            
            # 训练模型
            model_fit = model.fit(disp=False)
            
            # 保存模型
            ForecastService._ensure_model_dir()
            model_path = f"{ForecastService.MODELS_DIR}/sarima_{product_id}.pkl"
            joblib.dump(model_fit, model_path)
            
            # 计算模型评估指标
            predictions = model_fit.predict(dynamic=False)
            mae = mean_absolute_error(sales_data['quantity'], predictions)
            rmse = np.sqrt(mean_squared_error(sales_data['quantity'], predictions))
            
            return {
                'product_id': product_id,
                'model_type': 'SARIMA',
                'model_path': model_path,
                'data_points': len(sales_data),
                'metrics': {
                    'mae': round(mae, 2),
                    'rmse': round(rmse, 2)
                },
                'training_success': True
            }
        
        except Exception as e:
            return {
                'product_id': product_id,
                'model_type': 'SARIMA',
                'training_success': False,
                'error': str(e)
            }
    
    @staticmethod
    def train_random_forest_model(db: Session, product_id: int) -> Dict[str, Any]:
        """
        训练RandomForest模型
        
        Args:
            db: 数据库会话
            product_id: 产品ID
            
        Returns:
            包含模型训练结果的字典
        """
        # 获取销售数据
        sales_data = ForecastService._get_sales_data(db, product_id)
        
        # 检查数据量是否足够
        if len(sales_data) < 30:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="销售数据不足，需要至少30天的数据来训练RandomForest模型"
            )
        
        try:
            # 提取特征
            features_df = ForecastService._extract_features(sales_data)
            
            # 准备训练数据
            X = features_df.drop('quantity', axis=1)
            y = features_df['quantity']
            
            # 划分训练集和测试集
            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=0.2, shuffle=False
            )
            
            # 标准化特征
            scaler = StandardScaler()
            X_train_scaled = scaler.fit_transform(X_train)
            X_test_scaled = scaler.transform(X_test)
            
            # 训练RandomForest模型
            model = RandomForestRegressor(
                n_estimators=100,
                max_depth=10,
                random_state=42
            )
            model.fit(X_train_scaled, y_train)
            
            # 保存模型和特征缩放器
            ForecastService._ensure_model_dir()
            model_path = f"{ForecastService.MODELS_DIR}/rf_{product_id}.pkl"
            scaler_path = f"{ForecastService.MODELS_DIR}/scaler_{product_id}.pkl"
            
            joblib.dump(model, model_path)
            joblib.dump(scaler, scaler_path)
            
            # 评估模型
            y_pred = model.predict(X_test_scaled)
            mae = mean_absolute_error(y_test, y_pred)
            rmse = np.sqrt(mean_squared_error(y_test, y_pred))
            r2 = r2_score(y_test, y_pred)
            
            # 特征重要性
            feature_importance = dict(zip(X.columns, model.feature_importances_))
            top_features = sorted(
                feature_importance.items(),
                key=lambda x: x[1],
                reverse=True
            )[:5]
            
            return {
                'product_id': product_id,
                'model_type': 'RandomForest',
                'model_path': model_path,
                'scaler_path': scaler_path,
                'data_points': len(sales_data),
                'metrics': {
                    'mae': round(mae, 2),
                    'rmse': round(rmse, 2),
                    'r2': round(r2, 2)
                },
                'top_features': top_features,
                'training_success': True
            }
        
        except Exception as e:
            return {
                'product_id': product_id,
                'model_type': 'RandomForest',
                'training_success': False,
                'error': str(e)
            }
    
    @staticmethod
    def predict_sales(
        db: Session,
        product_id: int,
        days: int = 30,
        model_type: str = 'RandomForest'
    ) -> Dict[str, Any]:
        """
        预测未来销量
        
        Args:
            db: 数据库会话
            product_id: 产品ID
            days: 预测天数
            model_type: 模型类型 ('SARIMA' 或 'RandomForest')
            
        Returns:
            包含预测结果的字典
        """
        # 获取产品信息
        product = db.query(Product).filter(Product.id == product_id).first()
        if not product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"未找到ID为 {product_id} 的产品"
            )
        
        # 检查模型文件是否存在
        if model_type == 'SARIMA':
            model_path = f"{ForecastService.MODELS_DIR}/sarima_{product_id}.pkl"
        else:
            model_path = f"{ForecastService.MODELS_DIR}/rf_{product_id}.pkl"
            scaler_path = f"{ForecastService.MODELS_DIR}/scaler_{product_id}.pkl"
        
        if not os.path.exists(model_path):
            # 如果模型不存在，尝试训练
            if model_type == 'SARIMA':
                training_result = ForecastService.train_sarima_model(db, product_id)
            else:
                training_result = ForecastService.train_random_forest_model(db, product_id)
            
            if not training_result['training_success']:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"模型训练失败: {training_result.get('error', '未知错误')}"
                )
        
        try:
            # 获取最近的销售数据
            sales_data = ForecastService._get_sales_data(db, product_id)
            
            # 生成预测日期范围
            last_date = sales_data.index[-1]
            future_dates = pd.date_range(
                start=last_date + timedelta(days=1),
                periods=days,
                freq='D'
            )
            
            # 根据模型类型进行预测
            if model_type == 'SARIMA':
                # 加载SARIMA模型
                model_fit = joblib.load(model_path)
                
                # 预测未来销量
                forecast = model_fit.forecast(steps=days)
                forecast_df = pd.DataFrame({
                    'date': future_dates,
                    'predicted_quantity': forecast
                })
                
            else:  # RandomForest
                # 加载RandomForest模型和缩放器
                model = joblib.load(model_path)
                scaler = joblib.load(scaler_path)
                
                # 准备预测数据
                future_df = pd.DataFrame(index=future_dates)
                future_df['quantity'] = np.nan  # 占位，后面会删除
                
                # 提取特征
                future_features = ForecastService._extract_features(future_df)
                future_features = future_features.drop('quantity', axis=1)
                
                # 标准化特征
                future_features_scaled = scaler.transform(future_features)
                
                # 预测
                predictions = model.predict(future_features_scaled)
                
                # 确保预测值非负
                predictions = np.maximum(predictions, 0)
                
                forecast_df = pd.DataFrame({
                    'date': future_dates,
                    'predicted_quantity': predictions
                })
            
            # 计算总预测销量
            total_predicted = forecast_df['predicted_quantity'].sum()
            
            # 计算预测置信区间 (简化版)
            forecast_df['lower_bound'] = forecast_df['predicted_quantity'] * 0.8
            forecast_df['upper_bound'] = forecast_df['predicted_quantity'] * 1.2
            
            # 格式化输出
            forecast_df['date'] = forecast_df['date'].dt.strftime('%Y-%m-%d')
            forecast_df['predicted_quantity'] = forecast_df['predicted_quantity'].round(2)
            forecast_df['lower_bound'] = forecast_df['lower_bound'].round(2)
            forecast_df['upper_bound'] = forecast_df['upper_bound'].round(2)
            
            return {
                'product_id': product_id,
                'product_name': product.name,
                'product_sku': product.sku,
                'model_type': model_type,
                'forecast_days': days,
                'total_predicted_quantity': round(total_predicted, 2),
                'average_daily_quantity': round(total_predicted / days, 2),
                'forecast_data': forecast_df.to_dict('records')
            }
            
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"预测失败: {str(e)}"
            )
    
    @staticmethod
    def calculate_replenishment_quantity(
        db: Session,
        product_id: int,
        forecast_days: int = 30,
        model_type: str = 'RandomForest'
    ) -> Dict[str, Any]:
        """
        计算补货数量
        
        Args:
            db: 数据库会话
            product_id: 产品ID
            forecast_days: 预测天数
            model_type: 模型类型
            
        Returns:
            包含补货建议的字典
        """
        # 获取产品信息
        product = db.query(Product).filter(Product.id == product_id).first()
        if not product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"未找到ID为 {product_id} 的产品"
            )
        
        # 获取销量预测
        forecast_result = ForecastService.predict_sales(
            db, product_id, forecast_days, model_type
        )
        
        # 计算补货数量
        # 补货数量 = 预测销量 + 安全库存 - 当前库存
        predicted_quantity = forecast_result['total_predicted_quantity']
        safety_stock = product.safety_stock
        current_stock = product.stock_quantity
        
        replenishment_quantity = max(0, predicted_quantity + safety_stock - current_stock)
        replenishment_quantity = round(replenishment_quantity)
        
        # 计算补货点 (ROP)
        # ROP = 提前期内平均需求 + 安全库存
        daily_avg_demand = forecast_result['average_daily_quantity']
        lead_time = product.lead_time_days
        reorder_point = (daily_avg_demand * lead_time) + safety_stock
        reorder_point = round(reorder_point)
        
        # 计算经济订货批量 (简化版EOQ)
        # EOQ = sqrt(2 * 年需求量 * 订货成本 / 库存持有成本率 * 单位成本)
        # 假设订货成本为100，库存持有成本率为20%
        annual_demand = daily_avg_demand * 365
        ordering_cost = 100  # 假设值
        holding_cost_rate = 0.2  # 假设值
        unit_cost = product.cost
        
        eoq = np.sqrt((2 * annual_demand * ordering_cost) / (holding_cost_rate * unit_cost))
        eoq = round(eoq)
        
        # 最终补货建议 (取EOQ和计算补货量的较大值)
        suggested_quantity = max(replenishment_quantity, eoq)
        
        return {
            'product_id': product_id,
            'product_name': product.name,
            'product_sku': product.sku,
            'current_stock': current_stock,
            'safety_stock': safety_stock,
            'lead_time_days': lead_time,
            'predicted_demand': round(predicted_quantity, 2),
            'replenishment_quantity': replenishment_quantity,
            'economic_order_quantity': eoq,
            'reorder_point': reorder_point,
            'suggested_quantity': suggested_quantity,
            'forecast_period_days': forecast_days,
            'model_type': model_type,
            'needs_replenishment': current_stock <= reorder_point
        }