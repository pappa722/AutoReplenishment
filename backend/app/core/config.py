from pydantic import BaseSettings
from typing import Optional
import os
from pathlib import Path

class Settings(BaseSettings):
    # 项目基础配置
    PROJECT_NAME: str = "零售单店智能补货系统"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    
    # 数据库配置
    POSTGRES_SERVER: str = os.getenv("POSTGRES_SERVER", "localhost")
    POSTGRES_USER: str = os.getenv("POSTGRES_USER", "postgres")
    POSTGRES_PASSWORD: str = os.getenv("POSTGRES_PASSWORD", "您的新密码")
    POSTGRES_DB: str = os.getenv("POSTGRES_DB", "retail_inventory")
    SQLALCHEMY_DATABASE_URI: Optional[str] = None

    # Redis配置
    REDIS_HOST: str = os.getenv("REDIS_HOST", "localhost")
    REDIS_PORT: int = int(os.getenv("REDIS_PORT", 6379))
    REDIS_DB: int = int(os.getenv("REDIS_DB", 0))
    
    # 安全配置
    SECRET_KEY: str = os.getenv("SECRET_KEY", "your-secret-key-here")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 8  # 8 days
    
    # 文件上传配置
    UPLOAD_DIR: Path = Path("uploads")
    MAX_UPLOAD_SIZE: int = 10 * 1024 * 1024  # 10MB
    ALLOWED_EXTENSIONS: set = {".xlsx", ".xls"}

    def __init__(self):
        super().__init__()
        self.SQLALCHEMY_DATABASE_URI = (
            f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_SERVER}/{self.POSTGRES_DB}"
        )
        
        # 确保上传目录存在
        self.UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

settings = Settings()