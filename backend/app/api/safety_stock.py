from typing import Dict, Any
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api import deps
from app.services.safety_stock_service import SafetyStockService

router = APIRouter()

@router.post("/calculate")
def calculate_safety_stock(
    product_id: int,
    service_level: float = Query(0.95, ge=0.8, le=0.99),
    history_months: int = Query(6, ge=1, le=24),
    lead_time_days: int = Query(7, ge=1, le=90),
    consider_seasonality: bool = True,
    db: Session = Depends(deps.get_db)
) -> Dict[str, Any]:
    """
    计算单个产品的安全库存
    """
    return SafetyStockService.calculate_safety_stock(
        db,
        product_id,
        service_level,
        history_months,
        lead_time_days,
        consider_seasonality
    )

@router.post("/batch-calculate")
def batch_calculate_safety_stock(
    params: Dict[str, Any],
    skip: int = 0,
    limit: int = 100,
    category: str = None,
    db: Session = Depends(deps.get_db)
) -> Dict[str, Any]:
    """
    批量计算安全库存
    """
    return SafetyStockService.batch_calculate_safety_stock(
        db,
        params,
        skip,
        limit,
        category
    )

@router.put("/{product_id}")
def update_safety_stock(
    product_id: int,
    safety_stock: int = Query(..., gt=0),
    db: Session = Depends(deps.get_db)
) -> Dict[str, Any]:
    """
    更新产品的安全库存
    """
    product = SafetyStockService.update_safety_stock(
        db,
        product_id,
        safety_stock
    )
    return {
        "id": product.id,
        "name": product.name,
        "safety_stock": product.safety_stock,
        "needs_replenishment": product.needs_replenishment
    }

@router.post("/auto-update")
def auto_update_safety_stocks(
    service_level: float = Query(0.95, ge=0.8, le=0.99),
    history_months: int = Query(6, ge=1, le=24),
    lead_time_days: int = Query(7, ge=1, le=90),
    consider_seasonality: bool = True,
    confidence_threshold: float = Query(0.7, ge=0.5, le=0.9),
    db: Session = Depends(deps.get_db)
) -> Dict[str, Any]:
    """
    自动更新所有产品的安全库存
    """
    return SafetyStockService.auto_update_all_safety_stocks(
        db,
        service_level,
        history_months,
        lead_time_days,
        consider_seasonality,
        confidence_threshold
    )