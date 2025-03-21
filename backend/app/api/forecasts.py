from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.services.forecast_service import ForecastService
from app.api.deps import get_current_user

router = APIRouter()


@router.post("/train/{product_id}/sarima", response_model=Dict[str, Any])
def train_sarima_model(
    product_id: int,
    db: Session = Depends(get_db),
    current_user: Dict = Depends(get_current_user)
):
    """
    训练指定产品的SARIMA预测模型
    """
    try:
        result = ForecastService.train_sarima_model(db, product_id)
        return result
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"模型训练失败: {str(e)}"
        )


@router.post("/train/{product_id}/random-forest", response_model=Dict[str, Any])
def train_random_forest_model(
    product_id: int,
    db: Session = Depends(get_db),
    current_user: Dict = Depends(get_current_user)
):
    """
    训练指定产品的RandomForest预测模型
    """
    try:
        result = ForecastService.train_random_forest_model(db, product_id)
        return result
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"模型训练失败: {str(e)}"
        )


@router.get("/predict/{product_id}", response_model=Dict[str, Any])
def predict_sales(
    product_id: int,
    days: int = Query(30, ge=1, le=90),
    model_type: str = Query("RandomForest", enum=["SARIMA", "RandomForest"]),
    db: Session = Depends(get_db),
    current_user: Dict = Depends(get_current_user)
):
    """
    预测指定产品的未来销量
    """
    try:
        result = ForecastService.predict_sales(db, product_id, days, model_type)
        return result
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"预测失败: {str(e)}"
        )


@router.get("/replenishment/{product_id}", response_model=Dict[str, Any])
def calculate_replenishment(
    product_id: int,
    forecast_days: int = Query(30, ge=1, le=90),
    model_type: str = Query("RandomForest", enum=["SARIMA", "RandomForest"]),
    db: Session = Depends(get_db),
    current_user: Dict = Depends(get_current_user)
):
    """
    计算指定产品的补货建议
    """
    try:
        result = ForecastService.calculate_replenishment_quantity(
            db, product_id, forecast_days, model_type
        )
        return result
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"计算补货建议失败: {str(e)}"
        )