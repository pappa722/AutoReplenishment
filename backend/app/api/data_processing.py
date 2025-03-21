from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status, UploadFile, File
from sqlalchemy.orm import Session
import pandas as pd
import io

from app.db.session import get_db
from app.services.data_processing_service import DataProcessingService
from app.api.deps import get_current_user

router = APIRouter()


@router.post("/clean-data", response_model=Dict[str, Any])
async def clean_data(
    file: UploadFile = File(...),
    required_columns: List[str] = Query(["date", "product_id", "quantity"]),
    db: Session = Depends(get_db),
    current_user: Dict = Depends(get_current_user)
):
    """
    清洗上传的销售数据
    """
    try:
        # 读取上传的文件
        content = await file.read()
        
        # 根据文件类型读取数据
        if file.filename.endswith('.csv'):
            df = pd.read_csv(io.StringIO(content.decode('utf-8')))
        elif file.filename.endswith(('.xls', '.xlsx')):
            df = pd.read_excel(io.BytesIO(content))
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="不支持的文件格式，请上传CSV或Excel文件"
            )
        
        # 清洗数据
        cleaned_df = DataProcessingService.clean_sales_data(df, required_columns)
        
        # 计算清洗结果统计
        stats = {
            "original_rows": len(df),
            "cleaned_rows": len(cleaned_df),
            "removed_rows": len(df) - len(cleaned_df),
            "columns": list(cleaned_df.columns)
        }
        
        # 将清洗后的数据转换为记录列表
        records = cleaned_df.to_dict('records')
        
        # 限制返回的记录数量，避免响应过大
        preview_limit = 50
        preview_records = records[:preview_limit]
        
        return {
            "status": "success",
            "statistics": stats,
            "preview": preview_records,
            "has_more": len(records) > preview_limit
        }
    
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"数据清洗失败: {str(e)}"
        )


@router.post("/detect-outliers", response_model=Dict[str, Any])
async def detect_outliers(
    file: UploadFile = File(...),
    column: str = Query(...),
    method: str = Query("zscore", enum=["zscore", "iqr"]),
    threshold: float = Query(3.0, ge=1.0, le=10.0),
    db: Session = Depends(get_db),
    current_user: Dict = Depends(get_current_user)
):
    """
    检测数据中的异常值
    """
    try:
        # 读取上传的文件
        content = await file.read()
        
        # 根据文件类型读取数据
        if file.filename.endswith('.csv'):
            df = pd.read_csv(io.StringIO(content.decode('utf-8')))
        elif file.filename.endswith(('.xls', '.xlsx')):
            df = pd.read_excel(io.BytesIO(content))
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="不支持的文件格式，请上传CSV或Excel文件"
            )
        
        # 检查指定的列是否存在
        if column not in df.columns:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"列 '{column}' 不存在于数据中"
            )
        
        # 检测异常值
        result_df = DataProcessingService.detect_outliers(df, column, method, threshold)
        
        # 获取异常值记录
        outliers = result_df[result_df['is_outlier']].sort_values('outlier_score', ascending=False)
        
        # 计算统计信息
        stats = {
            "total_records": len(df),
            "outliers_count": len(outliers),
            "outliers_percentage": round(len(outliers) / len(df) * 100, 2),
            "method": method,
            "threshold": threshold
        }
        
        # 限制返回的记录数量
        preview_limit = 50
        preview_outliers = outliers.head(preview_limit).to_dict('records')
        
        return {
            "status": "success",
            "statistics": stats,
            "outliers": preview_outliers,
            "has_more": len(outliers) > preview_limit
        }
    
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"异常值检测失败: {str(e)}"
        )


@router.get("/sales-patterns/{product_id}", response_model=Dict[str, Any])
def analyze_sales_patterns(
    product_id: int,
    days: int = Query(90, ge=30, le=365),
    db: Session = Depends(get_db),
    current_user: Dict = Depends(get_current_user)
):
    """
    分析指定产品的销售模式
    """
    try:
        result = DataProcessingService.analyze_sales_patterns(db, product_id, days)
        return result
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"销售模式分析失败: {str(e)}"
        )