from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings

# 导入所有模型以确保它们被正确注册
from app.models import base
from app.models.user import User
from app.models.product import Product
from app.models.sale import Sale
from app.models.replenishment import Replenishment

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    openapi_url=f"{settings.API_V1_STR}/openapi.json"
)

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 在生产环境中应该设置具体的前端域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 导入路由
from app.api import api_router
app.include_router(api_router, prefix=settings.API_V1_STR)

@app.get("/")
async def root():
    return {"message": "Welcome to Retail Inventory System"}