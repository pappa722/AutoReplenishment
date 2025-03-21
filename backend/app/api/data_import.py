from typing import Any, List, Optional, Dict
import os
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, BackgroundTasks
from sqlalchemy.orm import Session

from app.api import deps
from app.models.user import User
from app.schemas.data_import import (
    ImportTask, ImportTaskCreate, ImportTaskUpdate,
    ImportTaskWithDetails, ImportTemplate
)
from app.services.data_import_service import DataImportService

router = APIRouter()


@router.get("/tasks", response_model=List[ImportTask])
def read_import_tasks(
    db: Session = Depends(deps.get_db),
    skip: int = 0,
    limit: int = 100,
    status: Optional[str] = None,
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    获取数据导入任务列表
    """
    tasks = DataImportService.get_import_tasks(
        db,
        skip=skip,
        limit=limit,
        status=status
    )
    return tasks


@router.get("/templates", response_model=List[ImportTemplate])
def read_import_templates(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    获取可用的导入模板列表
    """
    templates = DataImportService.get_import_templates(db)
    return templates


@router.get("/templates/{template_id}", response_model=ImportTemplate)
def read_import_template(
    *,
    db: Session = Depends(deps.get_db),
    template_id: int,
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    获取导入模板详情
    """
    template = DataImportService.get_template_by_id(db, template_id=template_id)
    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="导入模板不存在"
        )
    return template


@router.post("/templates/{template_id}/download")
def download_import_template(
    *,
    db: Session = Depends(deps.get_db),
    template_id: int,
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    下载导入模板
    """
    template = DataImportService.get_template_by_id(db, template_id=template_id)
    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="导入模板不存在"
        )
    
    template_file = DataImportService.get_template_file(template_id=template_id)
    if not template_file:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="模板文件不存在"
        )
    
    return template_file


@router.post("/upload/{template_id}", response_model=ImportTask)
async def upload_import_file(
    *,
    db: Session = Depends(deps.get_db),
    template_id: int,
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    上传数据文件并创建导入任务
    """
    # 检查模板是否存在
    template = DataImportService.get_template_by_id(db, template_id=template_id)
    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="导入模板不存在"
        )
    
    # 检查文件类型
    if not file.filename.endswith(('.xlsx', '.xls', '.csv')):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="不支持的文件类型，请上传Excel或CSV文件"
        )
    
    # 保存文件并创建导入任务
    try:
        # 读取文件内容
        contents = await file.read()
        
        # 创建导入任务
        task = DataImportService.create_import_task(
            db,
            template_id=template_id,
            filename=file.filename,
            file_content=contents,
            created_by=current_user.id
        )
        
        # 后台处理导入任务
        background_tasks.add_task(
            DataImportService.process_import_task,
            db,
            task.id
        )
        
        return task
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"创建导入任务失败: {str(e)}"
        )


@router.get("/tasks/{task_id}", response_model=ImportTaskWithDetails)
def read_import_task(
    *,
    db: Session = Depends(deps.get_db),
    task_id: int,
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    获取导入任务详情
    """
    task = DataImportService.get_task_by_id(db, task_id=task_id)
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="导入任务不存在"
        )
    return task


@router.delete("/tasks/{task_id}", response_model=ImportTask)
def delete_import_task(
    *,
    db: Session = Depends(deps.get_db),
    task_id: int,
    current_user: User = Depends(deps.get_current_active_superuser),
) -> Any:
    """
    删除导入任务，仅超级管理员可访问
    """
    task = DataImportService.get_task_by_id(db, task_id=task_id)
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="导入任务不存在"
        )
    
    task = DataImportService.delete_task(db, task_id=task_id)
    return task


@router.post("/tasks/{task_id}/retry", response_model=ImportTask)
def retry_import_task(
    *,
    db: Session = Depends(deps.get_db),
    task_id: int,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    重试失败的导入任务
    """
    task = DataImportService.get_task_by_id(db, task_id=task_id)
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="导入任务不存在"
        )
    
    if task.status != "failed":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="只能重试失败的导入任务"
        )
    
    # 重置任务状态并重新处理
    task = DataImportService.reset_task(db, task_id=task_id)
    
    # 后台处理导入任务
    background_tasks.add_task(
        DataImportService.process_import_task,
        db,
        task.id
    )
    
    return task