from enum import Enum
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, validator
from datetime import date, datetime

class ImportType(str, Enum):
    """导入数据类型枚举"""
    SALES = "sales"
    REPLENISHMENT = "replenishment"
    PRODUCTS = "products"
    INVENTORY = "inventory"
    PRODUCT = "product"  # 与 data_audit.py 中保持一致

class ImportStatus(str, Enum):
    """导入状态枚举"""
    PENDING = "pending"
    VALIDATING = "validating"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"

class ImportTaskBase(BaseModel):
    """导入任务基础Schema"""
    template_id: int
    filename: str
    status: ImportStatus = ImportStatus.PENDING
    total_rows: Optional[int] = None
    processed_rows: Optional[int] = None
    error_rows: Optional[int] = None
    created_at: datetime = Field(default_factory=datetime.now)
    created_by: Optional[int] = None

class ImportTaskCreate(ImportTaskBase):
    """创建导入任务时的Schema"""
    pass

class ImportTaskUpdate(BaseModel):
    """更新导入任务时的Schema"""
    status: Optional[ImportStatus] = None
    total_rows: Optional[int] = None
    processed_rows: Optional[int] = None
    error_rows: Optional[int] = None
    error_details: Optional[List[Dict[str, Any]]] = None

class ImportTemplate(BaseModel):
    """导入模板Schema"""
    id: int
    name: str
    description: Optional[str] = None
    file_path: str
    import_type: ImportType
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: Optional[datetime] = None

class ImportTask(ImportTaskBase):
    """返回给API的导入任务Schema"""
    id: int
    error_details: Optional[List[Dict[str, Any]]] = None
    template: ImportTemplate

    class Config:
        orm_mode = True

class ImportTaskWithDetails(ImportTask):
    """带有详细信息的导入任务Schema"""
    success_count: Optional[int] = None
    fail_count: Optional[int] = None
    validation_errors: Optional[List[Dict[str, Any]]] = None
    processing_errors: Optional[List[Dict[str, Any]]] = None

    class Config:
        orm_mode = True