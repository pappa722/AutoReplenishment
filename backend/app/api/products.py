from typing import Any, List, Optional, Dict

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from app.api import deps
from app.models.user import User
from app.schemas.product import (
    Product, ProductCreate, ProductUpdate, 
    ProductWithStats, ProductStockUpdate
)
from app.services.product_service import ProductService

router = APIRouter()


@router.get("/", response_model=List[Product])
def read_products(
    db: Session = Depends(deps.get_db),
    skip: int = 0,
    limit: int = 100,
    category: Optional[str] = None,
    name: Optional[str] = None,
    sku: Optional[str] = None,
    is_active: Optional[bool] = None,
    needs_replenishment: Optional[bool] = None,
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    获取产品列表，支持多种过滤条件
    """
    products = ProductService.get_products(
        db, 
        skip=skip, 
        limit=limit,
        category=category,
        name=name,
        sku=sku,
        is_active=is_active,
        needs_replenishment=needs_replenishment
    )
    return products


@router.get("/stats", response_model=List[ProductWithStats])
def read_products_with_stats(
    db: Session = Depends(deps.get_db),
    skip: int = 0,
    limit: int = 100,
    category: Optional[str] = None,
    days: int = 30,
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    获取产品列表，包含销售统计数据
    """
    products = ProductService.get_products_with_stats(
        db, 
        skip=skip, 
        limit=limit,
        category=category,
        days=days
    )
    return products


@router.get("/categories", response_model=List[str])
def read_product_categories(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    获取所有产品分类列表
    """
    categories = ProductService.get_all_categories(db)
    return categories


@router.get("/low-stock", response_model=List[Product])
def read_low_stock_products(
    db: Session = Depends(deps.get_db),
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    获取库存不足的产品列表
    """
    products = ProductService.get_low_stock_products(db, skip=skip, limit=limit)
    return products


@router.post("/", response_model=Product)
def create_product(
    *,
    db: Session = Depends(deps.get_db),
    product_in: ProductCreate,
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    创建新产品
    """
    # 检查SKU是否已存在
    existing_product = ProductService.get_product_by_sku(db, sku=product_in.sku)
    if existing_product:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="产品SKU已存在"
        )
    
    product = ProductService.create_product(db, product_in=product_in)
    return product


@router.get("/{product_id}", response_model=Product)
def read_product(
    *,
    db: Session = Depends(deps.get_db),
    product_id: int,
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    根据ID获取产品详情
    """
    product = ProductService.get_product_by_id(db, product_id=product_id)
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="产品不存在"
        )
    return product


@router.put("/{product_id}", response_model=Product)
def update_product(
    *,
    db: Session = Depends(deps.get_db),
    product_id: int,
    product_in: ProductUpdate,
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    更新产品信息
    """
    product = ProductService.get_product_by_id(db, product_id=product_id)
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="产品不存在"
        )
    
    # 如果更新SKU，检查新SKU是否与其他产品冲突
    if product_in.sku and product_in.sku != product.sku:
        existing_product = ProductService.get_product_by_sku(db, sku=product_in.sku)
        if existing_product and existing_product.id != product_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="产品SKU已存在"
            )
    
    product = ProductService.update_product(
        db, product_id=product_id, product_in=product_in
    )
    return product


@router.delete("/{product_id}", response_model=Product)
def delete_product(
    *,
    db: Session = Depends(deps.get_db),
    product_id: int,
    current_user: User = Depends(deps.get_current_active_superuser),
) -> Any:
    """
    删除产品，仅超级管理员可访问
    """
    product = ProductService.get_product_by_id(db, product_id=product_id)
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="产品不存在"
        )
    
    product = ProductService.delete_product(db, product_id=product_id)
    return product


@router.patch("/{product_id}/stock", response_model=Product)
def update_product_stock(
    *,
    db: Session = Depends(deps.get_db),
    product_id: int,
    stock_update: ProductStockUpdate,
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    更新产品库存
    """
    product = ProductService.get_product_by_id(db, product_id=product_id)
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="产品不存在"
        )
    
    # 验证库存更新数量
    if stock_update.quantity < 0 and abs(stock_update.quantity) > product.stock_quantity:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="库存不足，无法减少这么多"
        )
    
    product = ProductService.update_stock(
        db, 
        product_id=product_id, 
        quantity=stock_update.quantity,
        operation_type=stock_update.operation_type
    )
    return product


@router.patch("/{product_id}/activate", response_model=Product)
def activate_product(
    *,
    db: Session = Depends(deps.get_db),
    product_id: int,
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    激活产品
    """
    product = ProductService.get_product_by_id(db, product_id=product_id)
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="产品不存在"
        )
    
    product = ProductService.activate_product(db, product_id=product_id)
    return product


@router.patch("/{product_id}/deactivate", response_model=Product)
def deactivate_product(
    *,
    db: Session = Depends(deps.get_db),
    product_id: int,
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    停用产品
    """
    product = ProductService.get_product_by_id(db, product_id=product_id)
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="产品不存在"
        )
    
    product = ProductService.deactivate_product(db, product_id=product_id)
    return product


@router.get("/{product_id}/sales-history", response_model=Dict)
def get_product_sales_history(
    *,
    db: Session = Depends(deps.get_db),
    product_id: int,
    days: int = 30,
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    获取产品销售历史
    """
    product = ProductService.get_product_by_id(db, product_id=product_id)
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="产品不存在"
        )
    
    sales_history = ProductService.get_product_sales_history(
        db, product_id=product_id, days=days
    )
    return sales_history