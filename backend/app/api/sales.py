from typing import Any, List, Optional, Dict
from datetime import datetime, date

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from app.api import deps
from app.models.user import User
from app.schemas.sale import (
    Sale, SaleCreate, SaleUpdate, 
    SaleSummary, SaleWithDetails
)
from app.services.sale_service import SaleService
from app.services.product_service import ProductService

router = APIRouter()


@router.get("/", response_model=List[Sale])
def read_sales(
    db: Session = Depends(deps.get_db),
    skip: int = 0,
    limit: int = 100,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    product_id: Optional[int] = None,
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    获取销售记录列表，支持日期和产品过滤
    """
    sales = SaleService.get_sales(
        db,
        skip=skip,
        limit=limit,
        start_date=start_date,
        end_date=end_date,
        product_id=product_id
    )
    return sales


@router.get("/summary", response_model=SaleSummary)
def get_sales_summary(
    db: Session = Depends(deps.get_db),
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    获取销售汇总数据
    """
    summary = SaleService.get_sales_summary(
        db,
        start_date=start_date,
        end_date=end_date
    )
    return summary


@router.get("/daily-stats", response_model=List[Dict])
def get_daily_sales_stats(
    db: Session = Depends(deps.get_db),
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    获取每日销售统计数据
    """
    stats = SaleService.get_daily_sales_stats(
        db,
        start_date=start_date,
        end_date=end_date
    )
    return stats


@router.get("/top-products", response_model=List[Dict])
def get_top_selling_products(
    db: Session = Depends(deps.get_db),
    limit: int = 10,
    days: int = 30,
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    获取销量最高的产品列表
    """
    top_products = SaleService.get_top_selling_products(
        db,
        limit=limit,
        days=days
    )
    return top_products


@router.post("/", response_model=Sale)
def create_sale(
    *,
    db: Session = Depends(deps.get_db),
    sale_in: SaleCreate,
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    创建新的销售记录
    """
    # 检查产品是否存在且有效
    product = ProductService.get_product_by_id(db, product_id=sale_in.product_id)
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="产品不存在"
        )
    
    if not product.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="产品已停用，无法创建销售记录"
        )
    
    # 检查库存是否充足
    if sale_in.quantity > product.stock_quantity:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="库存不足"
        )
    
    # 创建销售记录并更新库存
    sale = SaleService.create_sale(db, sale_in=sale_in)
    return sale


@router.get("/{sale_id}", response_model=SaleWithDetails)
def read_sale(
    *,
    db: Session = Depends(deps.get_db),
    sale_id: int,
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    根据ID获取销售记录详情
    """
    sale = SaleService.get_sale_by_id(db, sale_id=sale_id)
    if not sale:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="销售记录不存在"
        )
    return sale


@router.put("/{sale_id}", response_model=Sale)
def update_sale(
    *,
    db: Session = Depends(deps.get_db),
    sale_id: int,
    sale_in: SaleUpdate,
    current_user: User = Depends(deps.get_current_active_superuser),
) -> Any:
    """
    更新销售记录，仅超级管理员可访问
    """
    sale = SaleService.get_sale_by_id(db, sale_id=sale_id)
    if not sale:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="销售记录不存在"
        )
    
    # 如果更新数量，需要检查库存
    if sale_in.quantity and sale_in.quantity != sale.quantity:
        product = ProductService.get_product_by_id(db, product_id=sale.product_id)
        current_stock = product.stock_quantity + sale.quantity  # 恢复原始库存
        if sale_in.quantity > current_stock:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="库存不足"
            )
    
    sale = SaleService.update_sale(
        db,
        sale_id=sale_id,
        sale_in=sale_in
    )
    return sale


@router.delete("/{sale_id}", response_model=Sale)
def delete_sale(
    *,
    db: Session = Depends(deps.get_db),
    sale_id: int,
    current_user: User = Depends(deps.get_current_active_superuser),
) -> Any:
    """
    删除销售记录，仅超级管理员可访问
    """
    sale = SaleService.get_sale_by_id(db, sale_id=sale_id)
    if not sale:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="销售记录不存在"
        )
    
    sale = SaleService.delete_sale(db, sale_id=sale_id)
    return sale