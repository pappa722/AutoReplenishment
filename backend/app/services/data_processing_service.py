from typing import Dict, List, Any, Optional
import pandas as pd
import numpy as np
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from datetime import datetime, timedelta

from app.models.product import Product
from app.models.sale import Sale


class DataProcessingService:
    """
    数据处理服务：负责数据清洗、标准化和异常检测
    """
    
    @staticmethod
    def clean_sales_data(
        df: pd.DataFrame,
        required_columns: List[str] = ['date', 'product_id', 'quantity']
    ) -> pd.DataFrame:
        """
        清洗销售数据
        
        Args:
            df: 原始数据DataFrame
            required_columns: 必需的列名列表
            
        Returns:
            清洗后的DataFrame
        """
        # 检查必需的列
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            raise ValueError(f"缺少必需的列: {missing_columns}")
        
        # 复制数据以避免修改原始数据
        cleaned_df = df.copy()
        
        # 处理日期列
        cleaned_df['date'] = pd.to_datetime(cleaned_df['date'], errors='coerce')
        
        # 删除日期无效的行
        cleaned_df = cleaned_df.dropna(subset=['date'])
        
        # 确保数值列为数值类型
        cleaned_df['quantity'] = pd.to_numeric(cleaned_df['quantity'], errors='coerce')
        cleaned_df['product_id'] = pd.to_numeric(cleaned_df['product_id'], errors='coerce')
        
        # 删除数量为负或空的记录
        cleaned_df = cleaned_df[cleaned_df['quantity'] > 0]
        
        # 删除重复记录
        cleaned_df = cleaned_df.drop_duplicates()
        
        # 按日期排序
        cleaned_df = cleaned_df.sort_values('date')
        
        return cleaned_df
    
    @staticmethod
    def detect_outliers(
        df: pd.DataFrame,
        column: str,
        method: str = 'zscore',
        threshold: float = 3.0
    ) -> pd.DataFrame:
        """
        检测异常值
        
        Args:
            df: 数据DataFrame
            column: 要检查的列名
            method: 检测方法 ('zscore' 或 'iqr')
            threshold: 阈值
            
        Returns:
            带有异常值标记的DataFrame
        """
        result_df = df.copy()
        
        if method == 'zscore':
            # 使用Z-score方法
            z_scores = np.abs((df[column] - df[column].mean()) / df[column].std())
            result_df['is_outlier'] = z_scores > threshold
            result_df['outlier_score'] = z_scores
            
        elif method == 'iqr':
            # 使用IQR方法
            Q1 = df[column].quantile(0.25)
            Q3 = df[column].quantile(0.75)
            IQR = Q3 - Q1
            lower_bound = Q1 - threshold * IQR
            upper_bound = Q3 + threshold * IQR
            
            result_df['is_outlier'] = (df[column] < lower_bound) | (df[column] > upper_bound)
            # 计算离群程度
            result_df['outlier_score'] = np.maximum(
                np.abs(df[column] - lower_bound) / IQR,
                np.abs(df[column] - upper_bound) / IQR
            )
        
        else:
            raise ValueError(f"不支持的异常检测方法: {method}")
        
        return result_df
    
    @staticmethod
    def handle_missing_values(
        df: pd.DataFrame,
        methods: Dict[str, str]
    ) -> pd.DataFrame:
        """
        处理缺失值
        
        Args:
            df: 数据DataFrame
            methods: 每列的处理方法字典 {'column_name': 'method'}
                    支持的方法：'mean', 'median', 'mode', 'ffill', 'bfill', 'zero', 'drop'
            
        Returns:
            处理后的DataFrame
        """
        result_df = df.copy()
        
        for column, method in methods.items():
            if column not in result_df.columns:
                continue
                
            if method == 'mean':
                result_df[column] = result_df[column].fillna(result_df[column].mean())
            elif method == 'median':
                result_df[column] = result_df[column].fillna(result_df[column].median())
            elif method == 'mode':
                result_df[column] = result_df[column].fillna(result_df[column].mode()[0])
            elif method == 'ffill':
                result_df[column] = result_df[column].fillna(method='ffill')
            elif method == 'bfill':
                result_df[column] = result_df[column].fillna(method='bfill')
            elif method == 'zero':
                result_df[column] = result_df[column].fillna(0)
            elif method == 'drop':
                result_df = result_df.dropna(subset=[column])
            else:
                raise ValueError(f"不支持的缺失值处理方法: {method}")
        
        return result_df
    
    @staticmethod
    def analyze_sales_patterns(
        db: Session,
        product_id: int,
        days: int = 90
    ) -> Dict[str, Any]:
        """
        分析销售模式
        
        Args:
            db: 数据库会话
            product_id: 产品ID
            days: 分析的天数
            
        Returns:
            包含销售模式分析结果的字典
        """
        # 获取销售数据
        start_date = datetime.now() - timedelta(days=days)
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
        sales_df = pd.DataFrame([
            {
                'date': sale.sale_date,
                'quantity': sale.quantity
            }
            for sale in sales
        ])
        
        # 设置日期索引
        sales_df['date'] = pd.to_datetime(sales_df['date'])
        sales_df.set_index('date', inplace=True)
        
        # 按日期聚合
        daily_sales = sales_df.resample('D').sum().fillna(0)
        
        # 添加时间特征
        daily_sales['day_of_week'] = daily_sales.index.dayofweek
        daily_sales['month'] = daily_sales.index.month
        
        # 计算基本统计信息
        stats = {
            'total_sales': int(daily_sales['quantity'].sum()),
            'avg_daily_sales': round(daily_sales['quantity'].mean(), 2),
            'max_daily_sales': int(daily_sales['quantity'].max()),
            'days_with_sales': int((daily_sales['quantity'] > 0).sum()),
            'days_without_sales': int((daily_sales['quantity'] == 0).sum())
        }
        
        # 分析每周销售模式
        weekly_pattern = daily_sales.groupby('day_of_week')['quantity'].agg([
            ('mean', 'mean'),
            ('count', 'count'),
            ('sum', 'sum')
        ]).round(2)
        
        # 找出销售最好的日子
        best_day = weekly_pattern['mean'].idxmax()
        day_names = ['周一', '周二', '周三', '周四', '周五', '周六', '周日']
        
        # 分析月度销售模式
        monthly_pattern = daily_sales.groupby('month')['quantity'].agg([
            ('mean', 'mean'),
            ('count', 'count'),
            ('sum', 'sum')
        ]).round(2)
        
        # 检测销售趋势
        # 使用7天移动平均线
        daily_sales['MA7'] = daily_sales['quantity'].rolling(window=7).mean()
        
        # 计算整体趋势（简单线性回归）
        x = np.arange(len(daily_sales))
        y = daily_sales['quantity'].values
        z = np.polyfit(x, y, 1)
        trend = 'increasing' if z[0] > 0 else 'decreasing' if z[0] < 0 else 'stable'
        
        # 检测季节性（如果有足够的数据）
        has_seasonality = False
        if len(daily_sales) >= 14:
            # 计算自相关系数
            autocorr = daily_sales['quantity'].autocorr(lag=7)
            has_seasonality = abs(autocorr) > 0.3
        
        return {
            'product_id': product_id,
            'analysis_period_days': days,
            'basic_stats': stats,
            'weekly_pattern': {
                'best_selling_day': day_names[best_day],
                'daily_averages': weekly_pattern['mean'].to_dict()
            },
            'monthly_pattern': {
                'monthly_averages': monthly_pattern['mean'].to_dict()
            },
            'trends': {
                'overall_trend': trend,
                'has_weekly_seasonality': has_seasonality,
                'trend_strength': abs(z[0])  # 趋势强度
            },
            'recommendations': [
                f"最佳销售日是{day_names[best_day]}，建议该日增加库存",
                "检测到明显的周季节性" if has_seasonality else "未检测到明显的周季节性",
                f"销售趋势总体{trend}，建议相应调整库存策略"
            ]
        }