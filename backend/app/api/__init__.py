from fastapi import APIRouter

from app.api import (
    auth, users, products, sales, replenishments, 
    data_import, safety_stock, data_audit, forecasts,
    data_processing
)

# 创建主API路由
api_router = APIRouter()

# 注册各个模块的路由
api_router.include_router(auth.router, prefix="/auth", tags=["认证"])
api_router.include_router(users.router, prefix="/users", tags=["用户管理"])
api_router.include_router(products.router, prefix="/products", tags=["产品管理"])
api_router.include_router(sales.router, prefix="/sales", tags=["销售管理"])
api_router.include_router(replenishments.router, prefix="/replenishments", tags=["补货管理"])
api_router.include_router(data_import.router, prefix="/data-import", tags=["数据导入"])
api_router.include_router(safety_stock.router, prefix="/safety-stock", tags=["安全库存管理"])
api_router.include_router(data_audit.router, prefix="/data-audit", tags=["数据审核"])
api_router.include_router(forecasts.router, prefix="/forecasts", tags=["销售预测"])
api_router.include_router(data_processing.router, prefix="/data-processing", tags=["数据处理"])