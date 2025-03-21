from typing import List, Dict, Any
import pandas as pd
import numpy as np
from datetime import datetime
from app.schemas.data_import import ImportType
from app.core.config import settings

class DataAuditService:
    """数据审核服务"""
    
    @staticmethod
    def validate_data_completeness(df: pd.DataFrame, import_type: ImportType) -> Dict[str, Any]:
        """
        验证数据完整性
        """
        required_fields = {
            ImportType.SALES: ['date', 'product_id', 'quantity', 'unit_price'],
            ImportType.INVENTORY: ['product_id', 'quantity', 'warehouse_id'],
            ImportType.PRODUCT: ['product_id', 'name', 'category', 'unit_cost']
        }
        
        missing_fields = [field for field in required_fields[import_type] 
                         if field not in df.columns]
        
        null_counts = df[required_fields[import_type]].isnull().sum().to_dict()
        
        return {
            'missing_fields': missing_fields,
            'null_counts': null_counts,
            'total_rows': len(df),
            'complete_rows': len(df.dropna()),
            'timestamp': datetime.now().isoformat()
        }
    
    @staticmethod
    def validate_data_consistency(df: pd.DataFrame, import_type: ImportType) -> Dict[str, Any]:
        """
        验证数据一致性
        """
        consistency_checks = {
            'negative_values': {},
            'duplicate_records': 0,
            'format_errors': {},
            'value_range_violations': {}
        }
        
        if import_type == ImportType.SALES:
            # 检查负数
            consistency_checks['negative_values'].update({
                'quantity': len(df[df['quantity'] < 0]),
                'unit_price': len(df[df['unit_price'] < 0])
            })
            
            # 检查重复记录
            key_fields = ['date', 'product_id']
            consistency_checks['duplicate_records'] = len(df[df.duplicated(subset=key_fields, keep=False)])
            
            # 检查日期格式
            try:
                pd.to_datetime(df['date'])
            except Exception as e:
                consistency_checks['format_errors']['date'] = str(e)
                
        elif import_type == ImportType.INVENTORY:
            consistency_checks['negative_values']['quantity'] = len(df[df['quantity'] < 0])
            
        return consistency_checks
    
    @staticmethod
    def validate_data_accuracy(df: pd.DataFrame, import_type: ImportType) -> Dict[str, Any]:
        """
        验证数据准确性
        """
        accuracy_checks = {
            'outliers': {},
            'statistical_summary': {},
            'potential_errors': []
        }
        
        if import_type == ImportType.SALES:
            # 检测数值型字段的异常值
            numeric_columns = ['quantity', 'unit_price']
            for col in numeric_columns:
                Q1 = df[col].quantile(0.25)
                Q3 = df[col].quantile(0.75)
                IQR = Q3 - Q1
                outlier_count = len(df[(df[col] < (Q1 - 1.5 * IQR)) | 
                                    (df[col] > (Q3 + 1.5 * IQR))])
                accuracy_checks['outliers'][col] = outlier_count
                
                # 基本统计信息
                accuracy_checks['statistical_summary'][col] = {
                    'mean': df[col].mean(),
                    'std': df[col].std(),
                    'min': df[col].min(),
                    'max': df[col].max()
                }
        
        return accuracy_checks
    
    @staticmethod
    def generate_audit_report(df: pd.DataFrame, import_type: ImportType) -> Dict[str, Any]:
        """
        生成完整的数据审核报告
        """
        audit_service = DataAuditService()
        
        report = {
            'completeness': audit_service.validate_data_completeness(df, import_type),
            'consistency': audit_service.validate_data_consistency(df, import_type),
            'accuracy': audit_service.validate_data_accuracy(df, import_type),
            'summary': {
                'total_issues': 0,
                'critical_issues': 0,
                'warnings': 0,
                'suggestions': []
            }
        }
        
        # 统计问题数量
        critical_issues = (
            len(report['completeness']['missing_fields']) +
            sum(report['consistency']['negative_values'].values()) +
            report['consistency']['duplicate_records']
        )
        
        warnings = sum(report['accuracy']['outliers'].values())
        
        report['summary'].update({
            'total_issues': critical_issues + warnings,
            'critical_issues': critical_issues,
            'warnings': warnings
        })
        
        # 生成改进建议
        if critical_issues > 0:
            report['summary']['suggestions'].append(
                "发现严重问题，建议检查数据完整性和一致性"
            )
        if warnings > 0:
            report['summary']['suggestions'].append(
                "发现潜在异常值，建议进行数据清洗"
            )
            
        return report