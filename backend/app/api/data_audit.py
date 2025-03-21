from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from typing import Dict, Any, List
import pandas as pd
from io import BytesIO
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.data_import import ImportType
from app.services.data_audit_service import DataAuditService
from app.api.deps import get_current_user
from app.schemas.user import User

router = APIRouter()

@router.post("/audit/upload", response_model=Dict[str, Any])
async def audit_uploaded_file(
    file: UploadFile = File(...),
    import_type: ImportType = Form(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    上传文件并进行数据审核
    """
    try:
        # 读取上传的Excel文件
        contents = await file.read()
        df = pd.read_excel(BytesIO(contents))
        
        # 生成审核报告
        audit_service = DataAuditService()
        audit_report = audit_service.generate_audit_report(df, import_type)
        
        return {
            "status": "success",
            "message": "文件审核完成",
            "data": {
                "filename": file.filename,
                "import_type": import_type,
                "row_count": len(df),
                "audit_report": audit_report
            }
        }
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"文件审核失败: {str(e)}"
        )

@router.post("/audit/rules", response_model=Dict[str, Any])
async def get_audit_rules(
    import_type: ImportType,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    获取特定导入类型的审核规则
    """
    rules = {
        ImportType.SALES: {
            "required_fields": ['date', 'product_id', 'quantity', 'unit_price'],
            "data_types": {
                "date": "datetime",
                "product_id": "string",
                "quantity": "numeric",
                "unit_price": "numeric"
            },
            "constraints": {
                "quantity": "positive",
                "unit_price": "positive"
            }
        },
        ImportType.INVENTORY: {
            "required_fields": ['product_id', 'quantity', 'warehouse_id'],
            "data_types": {
                "product_id": "string",
                "quantity": "numeric",
                "warehouse_id": "string"
            },
            "constraints": {
                "quantity": "non-negative"
            }
        },
        ImportType.PRODUCT: {
            "required_fields": ['product_id', 'name', 'category', 'unit_cost'],
            "data_types": {
                "product_id": "string",
                "name": "string",
                "category": "string",
                "unit_cost": "numeric"
            },
            "constraints": {
                "unit_cost": "positive"
            }
        }
    }
    
    return {
        "status": "success",
        "data": {
            "import_type": import_type,
            "rules": rules.get(import_type, {})
        }
    }

@router.post("/audit/fix-suggestions", response_model=Dict[str, Any])
async def get_fix_suggestions(
    audit_report: Dict[str, Any],
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    基于审核报告提供修复建议
    """
    suggestions = []
    
    # 处理缺失字段
    if audit_report.get("completeness", {}).get("missing_fields", []):
        missing_fields = audit_report["completeness"]["missing_fields"]
        suggestions.append({
            "issue": f"缺少必要字段: {', '.join(missing_fields)}",
            "suggestion": "请确保上传的文件包含所有必要字段，或选择正确的导入类型",
            "severity": "critical"
        })
    
    # 处理空值
    null_counts = audit_report.get("completeness", {}).get("null_counts", {})
    for field, count in null_counts.items():
        if count > 0:
            suggestions.append({
                "issue": f"字段 '{field}' 有 {count} 个空值",
                "suggestion": "可以使用均值/中位数填充数值型空值，或使用最常见值填充分类型空值",
                "severity": "warning" if count / audit_report["completeness"]["total_rows"] < 0.05 else "critical"
            })
    
    # 处理负值
    negative_values = audit_report.get("consistency", {}).get("negative_values", {})
    for field, count in negative_values.items():
        if count > 0:
            suggestions.append({
                "issue": f"字段 '{field}' 有 {count} 个负值",
                "suggestion": "检查这些记录是否应为正值，或者是否表示特殊情况（如退货）",
                "severity": "critical"
            })
    
    # 处理重复记录
    duplicate_count = audit_report.get("consistency", {}).get("duplicate_records", 0)
    if duplicate_count > 0:
        suggestions.append({
            "issue": f"发现 {duplicate_count} 条重复记录",
            "suggestion": "检查重复记录是否为真实重复或数据录入错误",
            "severity": "warning"
        })
    
    # 处理异常值
    outliers = audit_report.get("accuracy", {}).get("outliers", {})
    for field, count in outliers.items():
        if count > 0:
            suggestions.append({
                "issue": f"字段 '{field}' 有 {count} 个潜在异常值",
                "suggestion": "检查这些异常值是否为错误数据或特殊情况",
                "severity": "warning"
            })
    
    return {
        "status": "success",
        "data": {
            "suggestions": suggestions,
            "automatic_fixes_available": len(suggestions) > 0
        }
    }