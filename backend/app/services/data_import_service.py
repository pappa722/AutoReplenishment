import os
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime
from fastapi import HTTPException, UploadFile, status
from sqlalchemy.orm import Session
from pandas_schema import Schema, Column
from pandas_schema.validation import CustomElementValidation

from app.core.config import settings
from app.models.product import Product
from app.models.sale import Sale
from app.models.replenishment import Replenishment
from app.services.product_service import ProductService
from app.services.sale_service import SaleService
from app.services.replenishment_service import ReplenishmentService

class DataImportService:
    """
    数据导入服务类：处理Excel文件导入和数据验证
    """
    
    @staticmethod
    async def save_upload_file(upload_file: UploadFile) -> str:
        """
        保存上传的文件
        
        Args:
            upload_file: 上传的文件对象
            
        Returns:
            保存的文件路径
        """
        # 确保上传目录存在
        os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
        
        # 生成文件名
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        file_name = f"{timestamp}_{upload_file.filename}"
        file_path = os.path.join(settings.UPLOAD_DIR, file_name)
        
        # 保存文件
        with open(file_path, "wb") as f:
            content = await upload_file.read()
            f.write(content)
        
        return file_path
    
    @staticmethod
    def validate_excel_file(file_path: str) -> bool:
        """
        验证Excel文件格式
        
        Args:
            file_path: 文件路径
            
        Returns:
            是否为有效的Excel文件
            
        Raises:
            HTTPException: 如果文件格式无效
        """
        try:
            # 尝试读取Excel文件
            pd.read_excel(file_path)
            return True
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"无效的Excel文件: {str(e)}"
            )
    
    @staticmethod
    def get_template_path(template_type: str) -> str:
        """
        获取模板文件路径
        
        Args:
            template_type: 模板类型（products, sales, replenishments）
            
        Returns:
            模板文件路径
            
        Raises:
            HTTPException: 如果模板类型无效
        """
        templates = {
            "products": os.path.join(settings.TEMPLATE_DIR, "product_template.xlsx"),
            "sales": os.path.join(settings.TEMPLATE_DIR, "sales_template.xlsx"),
            "replenishments": os.path.join(settings.TEMPLATE_DIR, "replenishment_template.xlsx")
        }
        
        if template_type not in templates:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"无效的模板类型: {template_type}"
            )
        
        # 确保模板文件存在
        if not os.path.exists(templates[template_type]):
            # 如果模板不存在，创建模板
            DataImportService.create_template(template_type, templates[template_type])
        
        return templates[template_type]
    
    @staticmethod
    def create_template(template_type: str, file_path: str) -> None:
        """
        创建模板文件
        
        Args:
            template_type: 模板类型
            file_path: 文件保存路径
        """
        # 确保目录存在
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        
        # 创建不同类型的模板
        if template_type == "products":
            df = pd.DataFrame({
                "sku": ["P001", "P002"],
                "name": ["产品1", "产品2"],
                "category": ["类别1", "类别2"],
                "description": ["描述1", "描述2"],
                "cost_price": [10.0, 20.0],
                "selling_price": [15.0, 30.0],
                "stock_quantity": [100, 200],
                "safety_stock": [20, 40],
                "target_stock": [150, 300],
                "supplier_info": ["供应商1", "供应商2"]
            })
        elif template_type == "sales":
            df = pd.DataFrame({
                "sku": ["P001", "P002"],
                "quantity": [5, 10],
                "sale_date": [datetime.now(), datetime.now()],
                "customer_info": ["客户1", "客户2"]
            })
        elif template_type == "replenishments":
            df = pd.DataFrame({
                "sku": ["P001", "P002"],
                "quantity": [50, 100],
                "expected_arrival": [datetime.now(), datetime.now()],
                "supplier_info": ["供应商1", "供应商2"],
                "notes": ["备注1", "备注2"]
            })
        else:
            return
        
        # 保存模板
        df.to_excel(file_path, index=False)
    
    @staticmethod
    def import_products(
        db: Session, 
        file_path: str
    ) -> Tuple[int, int, List[Dict[str, Any]]]:
        """
        导入产品数据
        
        Args:
            db: 数据库会话
            file_path: Excel文件路径
            
        Returns:
            成功导入数量，失败数量，错误列表
        """
        # 读取Excel文件
        df = pd.read_excel(file_path)
        
        # 基本数据清洗
        df = df.replace({np.nan: None})
        
        # 定义验证规则
        def check_positive(x):
            return x > 0 if x is not None else True
        
        def check_non_negative(x):
            return x >= 0 if x is not None else True
        
        # 创建验证器
        positive_validation = CustomElementValidation(check_positive, "必须是正数")
        non_negative_validation = CustomElementValidation(check_non_negative, "不能是负数")
        
        # 创建验证模式
        schema = Schema([
            Column("sku", CustomElementValidation(lambda x: x is not None and len(str(x)) > 0, "SKU不能为空")),
            Column("name", CustomElementValidation(lambda x: x is not None and len(str(x)) > 0, "名称不能为空")),
            Column("cost_price", positive_validation),
            Column("selling_price", positive_validation),
            Column("stock_quantity", non_negative_validation),
            Column("safety_stock", non_negative_validation),
            Column("target_stock", non_negative_validation)
        ])
        
        # 验证数据
        errors = schema.validate(df)
        error_rows = []
        
        for error in errors:
            error_rows.append({
                "row": error.row + 2,  # Excel行号从1开始，且有标题行
                "column": error.column,
                "message": error.message
            })
        
        if error_rows:
            return 0, len(df), error_rows
        
        # 导入数据
        success_count = 0
        fail_count = 0
        error_list = []
        
        for index, row in df.iterrows():
            try:
                # 检查产品是否已存在
                existing_product = ProductService.get_product_by_sku(db, row["sku"])
                
                if existing_product:
                    # 更新现有产品
                    product_data = {k: v for k, v in row.items() if v is not None}
                    ProductService.update_product(
                        db,
                        existing_product.id,
                        ProductService.ProductUpdate(**product_data)
                    )
                else:
                    # 创建新产品
                    ProductService.create_product(
                        db,
                        ProductService.ProductCreate(**row.to_dict())
                    )
                
                success_count += 1
                
            except Exception as e:
                fail_count += 1
                error_list.append({
                    "row": index + 2,
                    "sku": row.get("sku", ""),
                    "message": str(e)
                })
        
        return success_count, fail_count, error_list
    
    @staticmethod
    def import_sales(
        db: Session, 
        file_path: str
    ) -> Tuple[int, int, List[Dict[str, Any]]]:
        """
        导入销售数据
        
        Args:
            db: 数据库会话
            file_path: Excel文件路径
            
        Returns:
            成功导入数量，失败数量，错误列表
        """
        # 读取Excel文件
        df = pd.read_excel(file_path)
        
        # 基本数据清洗
        df = df.replace({np.nan: None})
        
        # 定义验证规则
        def check_positive(x):
            return x > 0 if x is not None else False
        
        # 创建验证器
        positive_validation = CustomElementValidation(check_positive, "必须是正数")
        
        # 创建验证模式
        schema = Schema([
            Column("sku", CustomElementValidation(lambda x: x is not None and len(str(x)) > 0, "SKU不能为空")),
            Column("quantity", positive_validation),
            Column("sale_date", CustomElementValidation(lambda x: x is not None, "销售日期不能为空"))
        ])
        
        # 验证数据
        errors = schema.validate(df)
        error_rows = []
        
        for error in errors:
            error_rows.append({
                "row": error.row + 2,
                "column": error.column,
                "message": error.message
            })
        
        if error_rows:
            return 0, len(df), error_rows
        
        # 导入数据
        success_count = 0
        fail_count = 0
        error_list = []
        
        for index, row in df.iterrows():
            try:
                # 查找产品
                product = ProductService.get_product_by_sku(db, row["sku"])
                if not product:
                    raise ValueError(f"找不到SKU为 {row['sku']} 的产品")
                
                # 创建销售记录
                sale_data = {
                    "product_id": product.id,
                    "quantity": row["quantity"],
                    "sale_date": row["sale_date"],
                    "customer_info": row.get("customer_info")
                }
                
                SaleService.create_sale(
                    db,
                    SaleService.SaleCreate(**sale_data)
                )
                
                success_count += 1
                
            except Exception as e:
                fail_count += 1
                error_list.append({
                    "row": index + 2,
                    "sku": row.get("sku", ""),
                    "message": str(e)
                })
        
        return success_count, fail_count, error_list
    
    @staticmethod
    def import_replenishments(
        db: Session, 
        file_path: str
    ) -> Tuple[int, int, List[Dict[str, Any]]]:
        """
        导入补货数据
        
        Args:
            db: 数据库会话
            file_path: Excel文件路径
            
        Returns:
            成功导入数量，失败数量，错误列表
        """
        # 读取Excel文件
        df = pd.read_excel(file_path)
        
        # 基本数据清洗
        df = df.replace({np.nan: None})
        
        # 定义验证规则
        def check_positive(x):
            return x > 0 if x is not None else False
        
        # 创建验证器
        positive_validation = CustomElementValidation(check_positive, "必须是正数")
        
        # 创建验证模式
        schema = Schema([
            Column("sku", CustomElementValidation(lambda x: x is not None and len(str(x)) > 0, "SKU不能为空")),
            Column("quantity", positive_validation)
        ])
        
        # 验证数据
        errors = schema.validate(df)
        error_rows = []
        
        for error in errors:
            error_rows.append({
                "row": error.row + 2,
                "column": error.column,
                "message": error.message
            })
        
        if error_rows:
            return 0, len(df), error_rows
        
        # 导入数据
        success_count = 0
        fail_count = 0
        error_list = []
        
        for index, row in df.iterrows():
            try:
                # 查找产品
                product = ProductService.get_product_by_sku(db, row["sku"])
                if not product:
                    raise ValueError(f"找不到SKU为 {row['sku']} 的产品")
                
                # 创建补货记录
                replenishment_data = {
                    "product_id": product.id,
                    "quantity": row["quantity"],
                    "expected_arrival": row.get("expected_arrival"),
                    "supplier_info": row.get("supplier_info"),
                    "notes": row.get("notes")
                }
                
                ReplenishmentService.create_replenishment(
                    db,
                    ReplenishmentService.ReplenishmentCreate(**replenishment_data)
                )
                
                success_count += 1
                
            except Exception as e:
                fail_count += 1
                error_list.append({
                    "row": index + 2,
                    "sku": row.get("sku", ""),
                    "message": str(e)
                })
        
        return success_count, fail_count, error_list
    
    @staticmethod
    def process_import_file(
        db: Session,
        file_path: str,
        import_type: str
    ) -> Dict[str, Any]:
        """
        处理导入文件
        
        Args:
            db: 数据库会话
            file_path: 文件路径
            import_type: 导入类型（products, sales, replenishments）
            
        Returns:
            导入结果
        """
        # 验证文件格式
        DataImportService.validate_excel_file(file_path)
        
        # 根据导入类型选择处理方法
        if import_type == "products":
            success_count, fail_count, errors = DataImportService.import_products(db, file_path)
        elif import_type == "sales":
            success_count, fail_count, errors = DataImportService.import_sales(db, file_path)
        elif import_type == "replenishments":
            success_count, fail_count, errors = DataImportService.import_replenishments(db, file_path)
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"无效的导入类型: {import_type}"
            )
        
        return {
            "success_count": success_count,
            "fail_count": fail_count,
            "total_count": success_count + fail_count,
            "errors": errors
        }