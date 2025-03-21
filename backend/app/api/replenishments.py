from typing import Any, List, Optional, Dict
from datetime import datetime, date

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from app.api import deps
from app.models.user import User
from app.schemas.replenishment import (
    Replenishment, ReplenishmentCreate, ReplenishmentUpdate,
    ReplenishmentWithDetails, ReplenishmentSummary, 
    ReplenishmentRecommendation
)
from app.services.replenishment_service import ReplenishmentService
from app.services.product_service import ProductService

router = APIRouter()


@router.get("/", response_model=List[Replenishment])
def read_replenishments(
    db: Session = Depends(deps.get_db),
    skip: int = 0,
    limit: int = 100,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    product_id: Optional[int] = None,
    status: Optional[str] = None,
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    获取补货记录列表，支持日期、产品和状态过滤
    """
    replenishments = ReplenishmentService.get_replenishments(
        db,
        skip=skip,
        limit=limit,
        start_date=start_date,
        end_date=end_date,
        product_id=product_id,
        status=status
    )
    return replenishments


@router.get("/summary", response_model=ReplenishmentSummary)
def get_replenishment_summary(
    db: Session = Depends(deps.get_db),
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    获取补货汇总数据
    """
    summary = ReplenishmentService.get_replenishment_summary(
        db,
        start_date=start_date,
        end_date=end_date
    )
    return summary


@router.get("/recommendations", response_model=List[ReplenishmentRecommendation])
def get_replenishment_recommendations(
    db: Session = Depends(deps.get_db),
    skip: int = 0,
    limit: int = 100,
    category: Optional[str] = None,
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    获取智能补货建议
    """
    recommendations = ReplenishmentService.get_replenishment_recommendations(
        db,
        skip=skip,
        limit=limit,
        category=category
    )
    return recommendations


@router.post("/", response_model=Replenishment)
def create_replenishment(
    *,
    db: Session = Depends(deps.get_db),
    replenishment_in: ReplenishmentCreate,
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    创建新的补货记录
    """
    # 检查产品是否存在且有效
    product = ProductService.get_product_by_id(db, product_id=replenishment_in.product_id)
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="产品不存在"
        )
    
    if not product.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="产品已停用，无法创建补货记录"
        )
    
    # 创建补货记录
    replenishment = ReplenishmentService.create_replenishment(
        db, 
        replenishment_in=replenishment_in,
        created_by=current_user.id
    )
    return replenishment


@router.get("/{replenishment_id}", response_model=ReplenishmentWithDetails)
def read_replenishment(
    *,
    db: Session = Depends(deps.get_db),
    replenishment_id: int,
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    根据ID获取补货记录详情
    """
    replenishment = ReplenishmentService.get_replenishment_by_id(
        db, 
        replenishment_id=replenishment_id
    )
    if not replenishment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="补货记录不存在"
        )
    return replenishment


@router.put("/{replenishment_id}", response_model=Replenishment)
def update_replenishment(
    *,
    db: Session = Depends(deps.get_db),
    replenishment_id: int,
    replenishment_in: ReplenishmentUpdate,
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    更新补货记录
    """
    replenishment = ReplenishmentService.get_replenishment_by_id(
        db, 
        replenishment_id=replenishment_id
    )
    if not replenishment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="补货记录不存在"
        )
    
    # 只有创建者或超级管理员可以更新补货记录
    if replenishment.created_by != current_user.id and not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="权限不足，无法更新此补货记录"
        )
    
    # 已完成的补货记录不能再更新
    if replenishment.status == "completed":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="已完成的补货记录不能再更新"
        )
    
    replenishment = ReplenishmentService.update_replenishment(
        db,
        replenishment_id=replenishment_id,
        replenishment_in=replenishment_in,
        updated_by=current_user.id
    )
    return replenishment


@router.delete("/{replenishment_id}", response_model=Replenishment)
def delete_replenishment(
    *,
    db: Session = Depends(deps.get_db),
    replenishment_id: int,
    current_user: User = Depends(deps.get_current_active_superuser),
) -> Any:
    """
    删除补货记录，仅超级管理员可访问
    """
    replenishment = ReplenishmentService.get_replenishment_by_id(
        db, 
        replenishment_id=replenishment_id
    )
    if not replenishment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="补货记录不存在"
        )
    
    # 已完成的补货记录不能删除
    if replenishment.status == "completed":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="已完成的补货记录不能删除"
        )
    
    replenishment = ReplenishmentService.delete_replenishment(
        db, 
        replenishment_id=replenishment_id
    )
    return replenishment


@router.patch("/{replenishment_id}/complete", response_model=Replenishment)
def complete_replenishment(
    *,
    db: Session = Depends(deps.get_db),
    replenishment_id: int,
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    完成补货，更新产品库存
    """
    replenishment = ReplenishmentService.get_replenishment_by_id(
        db, 
        replenishment_id=replenishment_id
    )
    if not replenishment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="补货记录不存在"
        )
    
    # 已完成的补货记录不能再次完成
    if replenishment.status == "completed":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="补货记录已经完成"
        )
    
    # 只有创建者或超级管理员可以完成补货
    if replenishment.created_by != current_user.id and not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="权限不足，无法完成此补货记录"
        )
    
    replenishment = ReplenishmentService.complete_replenishment(
        db,
        replenishment_id=replenishment_id,
        completed_by=current_user.id
    )
    return replenishment


@router.patch("/{replenishment_id}/cancel", response_model=Replenishment)
def cancel_replenishment(
    *,
    db: Session = Depends(deps.get_db),
    replenishment_id: int,
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    取消补货
    """
    replenishment = ReplenishmentService.get_replenishment_by_id(
        db, 
        replenishment_id=replenishment_id
    )
    if not replenishment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="补货记录不存在"
        )
    
    # 已完成的补货记录不能取消
    if replenishment.status == "completed":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="已完成的补货记录不能取消"
        )
    
    # 已取消的补货记录不能再次取消
    if replenishment.status == "cancelled":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="补货记录已经取消"
        )
    
    # 只有创建者或超级管理员可以取消补货
    if replenishment.created_by != current_user.id and not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="权限不足，无法取消此补货记录"
        )
    
    replenishment = ReplenishmentService.cancel_replenishment(
        db,
        replenishment_id=replenishment_id,
        cancelled_by=current_user.id
    )
    return replenishment