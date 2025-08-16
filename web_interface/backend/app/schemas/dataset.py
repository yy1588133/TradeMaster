"""
数据集相关的Pydantic模式定义

提供数据集管理相关的数据验证和序列化模式，包括数据上传、处理、
预处理、统计分析等功能的API数据模式。
"""

from datetime import datetime
from typing import Any, Dict, List, Optional, Union
from enum import Enum

from pydantic import Field, validator, root_validator

from app.schemas.base import BaseSchema, TimestampSchema, UUIDSchema
from app.models.database import DatasetStatus


# ==================== 数据集相关枚举 ====================

class DatasetFileType(str, Enum):
    """数据集文件类型枚举"""
    CSV = "csv"
    JSON = "json"
    XLSX = "xlsx"
    XLS = "xls"
    PARQUET = "parquet"
    PICKLE = "pickle"


class DataProcessingOperation(str, Enum):
    """数据处理操作类型枚举"""
    FILL_MISSING = "fill_missing"
    DROP_MISSING = "drop_missing"
    NORMALIZE = "normalize"
    STANDARDIZE = "standardize"
    REMOVE_OUTLIERS = "remove_outliers"
    FEATURE_ENGINEERING = "feature_engineering"
    DATA_SPLIT = "data_split"


class FillMethod(str, Enum):
    """缺失值填充方法枚举"""
    FORWARD_FILL = "forward_fill"
    BACKWARD_FILL = "backward_fill"
    MEAN = "mean"
    MEDIAN = "median"
    MODE = "mode"
    CONSTANT = "constant"
    INTERPOLATE = "interpolate"


class NormalizationMethod(str, Enum):
    """标准化方法枚举"""
    MIN_MAX = "min_max"
    Z_SCORE = "z_score"
    ROBUST = "robust"
    QUANTILE = "quantile_uniform"


# ==================== 数据集基础模式 ====================

class DatasetBase(BaseSchema):
    """数据集基础信息模式"""
    name: str = Field(
        ..., 
        min_length=1, 
        max_length=100, 
        description="数据集名称"
    )
    description: Optional[str] = Field(None, description="数据集描述")
    
    @validator('name')
    def validate_name(cls, v):
        """验证数据集名称"""
        if not v or not v.strip():
            raise ValueError('数据集名称不能为空')
        return v.strip()


class DatasetCreate(DatasetBase):
    """数据集创建模式（用于文件上传后的元数据创建）"""
    file_path: str = Field(..., description="文件路径")
    file_size: int = Field(..., ge=0, description="文件大小(字节)")
    file_type: DatasetFileType = Field(..., description="文件类型")


class DatasetUpdate(BaseSchema):
    """数据集更新模式"""
    name: Optional[str] = Field(None, min_length=1, max_length=100, description="数据集名称")
    description: Optional[str] = Field(None, description="数据集描述")
    
    @validator('name')
    def validate_name(cls, v):
        """验证数据集名称"""
        if v is not None:
            if not v or not v.strip():
                raise ValueError('数据集名称不能为空')
            return v.strip()
        return v


# ==================== 数据集响应模式 ====================

class ColumnInfo(BaseSchema):
    """列信息模式"""
    name: str = Field(..., description="列名")
    dtype: str = Field(..., description="数据类型")
    description: Optional[str] = Field(None, description="列描述")
    nullable: bool = Field(True, description="是否可为空")
    unique_count: Optional[int] = Field(None, description="唯一值数量")
    missing_count: Optional[int] = Field(None, description="缺失值数量")
    sample_values: Optional[List[Any]] = Field(None, description="样本值")


class DatasetStatistics(BaseSchema):
    """数据集统计信息模式"""
    # 基本统计
    total_rows: int = Field(..., description="总行数")
    total_columns: int = Field(..., description="总列数")
    missing_values_count: int = Field(..., description="缺失值总数")
    duplicate_rows_count: int = Field(..., description="重复行数")
    
    # 数据类型分布
    column_types: Dict[str, int] = Field(..., description="数据类型分布")
    
    # 数值列统计
    numerical_summary: Optional[Dict[str, Dict[str, float]]] = Field(
        None, description="数值列统计摘要"
    )
    
    # 分类列统计
    categorical_summary: Optional[Dict[str, Dict[str, Any]]] = Field(
        None, description="分类列统计摘要"
    )
    
    # 时间序列统计
    temporal_summary: Optional[Dict[str, Any]] = Field(
        None, description="时间序列统计摘要"
    )


class DatasetInDB(DatasetBase, TimestampSchema, UUIDSchema):
    """数据库中的数据集模式"""
    id: int = Field(..., description="数据集ID")
    file_path: str = Field(..., description="文件路径")
    file_size: int = Field(..., description="文件大小(字节)")
    file_type: str = Field(..., description="文件类型")
    
    # 数据信息
    row_count: Optional[int] = Field(None, description="行数")
    column_count: Optional[int] = Field(None, description="列数")
    columns: Optional[List[Dict[str, Any]]] = Field(None, description="列信息")
    
    # 状态信息
    status: DatasetStatus = Field(..., description="处理状态")
    error_message: Optional[str] = Field(None, description="错误信息")
    
    # 统计信息
    statistics: Optional[Dict[str, Any]] = Field(None, description="统计信息")
    sample_data: Optional[List[Dict[str, Any]]] = Field(None, description="样本数据")
    
    # 关联信息
    owner_id: int = Field(..., description="所有者ID")
    
    # 时间信息
    processed_at: Optional[datetime] = Field(None, description="处理完成时间")


class DatasetResponse(BaseSchema):
    """数据集响应模式"""
    id: int = Field(..., description="数据集ID")
    uuid: str = Field(..., description="数据集UUID")
    name: str = Field(..., description="数据集名称")
    description: Optional[str] = Field(None, description="数据集描述")
    file_type: str = Field(..., description="文件类型")
    file_size: int = Field(..., description="文件大小(字节)")
    
    # 数据信息
    row_count: Optional[int] = Field(None, description="行数")
    column_count: Optional[int] = Field(None, description="列数")
    
    # 状态信息
    status: DatasetStatus = Field(..., description="处理状态")
    error_message: Optional[str] = Field(None, description="错误信息")
    
    # 关联信息
    owner_id: int = Field(..., description="所有者ID")
    
    # 时间信息
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")
    processed_at: Optional[datetime] = Field(None, description="处理完成时间")


class DatasetDetail(DatasetResponse):
    """数据集详情模式"""
    columns: Optional[List[ColumnInfo]] = Field(None, description="列信息")
    statistics: Optional[DatasetStatistics] = Field(None, description="统计信息")
    sample_data: Optional[List[Dict[str, Any]]] = Field(None, description="样本数据")
    
    # 使用统计
    training_jobs_count: int = Field(0, description="关联的训练任务数量")
    evaluations_count: int = Field(0, description="关联的评估任务数量")


class DatasetSummary(BaseSchema):
    """数据集摘要信息模式"""
    id: int = Field(..., description="数据集ID")
    name: str = Field(..., description="数据集名称")
    file_type: str = Field(..., description="文件类型")
    status: DatasetStatus = Field(..., description="处理状态")
    row_count: Optional[int] = Field(None, description="行数")
    column_count: Optional[int] = Field(None, description="列数")
    created_at: datetime = Field(..., description="创建时间")


# ==================== 文件上传模式 ====================

class FileUploadRequest(BaseSchema):
    """文件上传请求模式"""
    name: str = Field(..., min_length=1, max_length=100, description="数据集名称")
    description: Optional[str] = Field(None, description="数据集描述")
    
    @validator('name')
    def validate_name(cls, v):
        """验证数据集名称"""
        if not v or not v.strip():
            raise ValueError('数据集名称不能为空')
        return v.strip()


class FileUploadResponse(BaseSchema):
    """文件上传响应模式"""
    dataset_id: int = Field(..., description="数据集ID")
    upload_status: str = Field(..., description="上传状态")
    processing_status: str = Field(..., description="处理状态")
    file_info: Dict[str, Any] = Field(..., description="文件信息")


class UploadProgress(BaseSchema):
    """上传进度模式"""
    dataset_id: int = Field(..., description="数据集ID")
    upload_progress: float = Field(..., ge=0, le=100, description="上传进度百分比")
    processing_progress: float = Field(..., ge=0, le=100, description="处理进度百分比")
    current_step: Optional[str] = Field(None, description="当前处理步骤")
    eta: Optional[int] = Field(None, description="预计剩余时间(秒)")


# ==================== 数据预处理模式 ====================

class PreprocessingOperation(BaseSchema):
    """数据预处理操作模式"""
    type: DataProcessingOperation = Field(..., description="操作类型")
    columns: Optional[List[str]] = Field(None, description="目标列，None表示所有适用列")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="操作参数")
    
    @root_validator
    def validate_operation_parameters(cls, values):
        """验证操作参数"""
        operation_type = values.get('type')
        parameters = values.get('parameters', {})
        
        # 根据操作类型验证必需参数
        if operation_type == DataProcessingOperation.FILL_MISSING:
            if 'method' not in parameters:
                raise ValueError('fill_missing操作需要method参数')
            method = parameters['method']
            if method not in [m.value for m in FillMethod]:
                raise ValueError(f'无效的填充方法: {method}')
            
            # 常数填充需要value参数
            if method == FillMethod.CONSTANT and 'value' not in parameters:
                raise ValueError('constant填充方法需要value参数')
        
        elif operation_type == DataProcessingOperation.NORMALIZE:
            if 'method' not in parameters:
                raise ValueError('normalize操作需要method参数')
            method = parameters['method']
            if method not in [m.value for m in NormalizationMethod]:
                raise ValueError(f'无效的标准化方法: {method}')
        
        elif operation_type == DataProcessingOperation.REMOVE_OUTLIERS:
            if 'method' not in parameters:
                parameters['method'] = 'iqr'  # 默认使用IQR方法
        
        elif operation_type == DataProcessingOperation.DATA_SPLIT:
            if 'train_ratio' not in parameters:
                parameters['train_ratio'] = 0.7  # 默认7:3分割
            train_ratio = parameters['train_ratio']
            if not 0 < train_ratio < 1:
                raise ValueError('train_ratio必须在0和1之间')
        
        return values


class PreprocessingRequest(BaseSchema):
    """数据预处理请求模式"""
    operations: List[PreprocessingOperation] = Field(..., min_items=1, description="预处理操作列表")
    save_as_new: bool = Field(False, description="是否保存为新数据集")
    new_name: Optional[str] = Field(None, description="新数据集名称（save_as_new为True时必需）")
    
    @root_validator
    def validate_save_as_new(cls, values):
        """验证保存为新数据集的参数"""
        save_as_new = values.get('save_as_new', False)
        new_name = values.get('new_name')
        
        if save_as_new and not new_name:
            raise ValueError('保存为新数据集时必须提供new_name')
        
        return values


class PreprocessingResponse(BaseSchema):
    """数据预处理响应模式"""
    task_id: str = Field(..., description="处理任务ID")
    dataset_id: int = Field(..., description="原数据集ID")
    new_dataset_id: Optional[int] = Field(None, description="新数据集ID（如果创建了新数据集）")
    status: str = Field(..., description="处理状态")
    operations_count: int = Field(..., description="操作数量")


class PreprocessingProgress(BaseSchema):
    """预处理进度模式"""
    task_id: str = Field(..., description="任务ID")
    progress: float = Field(..., ge=0, le=100, description="进度百分比")
    current_operation: int = Field(..., description="当前操作索引")
    total_operations: int = Field(..., description="总操作数")
    current_step: Optional[str] = Field(None, description="当前步骤描述")
    estimated_time_remaining: Optional[int] = Field(None, description="预计剩余时间(秒)")


# ==================== 数据查询和分析模式 ====================

class DatasetListQuery(BaseSchema):
    """数据集列表查询模式"""
    search: Optional[str] = Field(None, max_length=100, description="搜索关键词")
    file_type: Optional[DatasetFileType] = Field(None, description="文件类型筛选")
    status: Optional[DatasetStatus] = Field(None, description="状态筛选")
    owner_id: Optional[int] = Field(None, description="所有者筛选")
    min_size: Optional[int] = Field(None, ge=0, description="最小文件大小筛选")
    max_size: Optional[int] = Field(None, ge=0, description="最大文件大小筛选")
    sort: Optional[str] = Field("created_at:desc", description="排序字段")
    
    @validator('sort')
    def validate_sort(cls, v):
        """验证排序参数"""
        if v is None:
            return "created_at:desc"
        
        allowed_fields = [
            'id', 'name', 'file_type', 'file_size', 'status',
            'row_count', 'column_count', 'created_at', 'updated_at', 'processed_at'
        ]
        
        if ':' in v:
            field, order = v.split(':', 1)
            if field not in allowed_fields:
                raise ValueError(f'排序字段必须是: {", ".join(allowed_fields)}')
            if order.lower() not in ['asc', 'desc']:
                raise ValueError('排序方向必须是 asc 或 desc')
            return f"{field}:{order.lower()}"
        else:
            if v not in allowed_fields:
                raise ValueError(f'排序字段必须是: {", ".join(allowed_fields)}')
            return f"{v}:asc"


class DataSampleRequest(BaseSchema):
    """数据样本请求模式"""
    limit: int = Field(10, ge=1, le=1000, description="返回记录数，最大1000")
    offset: int = Field(0, ge=0, description="偏移量")
    columns: Optional[List[str]] = Field(None, description="指定列，None表示所有列")
    filters: Optional[Dict[str, Any]] = Field(None, description="过滤条件")


class DataSampleResponse(BaseSchema):
    """数据样本响应模式"""
    data: List[Dict[str, Any]] = Field(..., description="样本数据")
    total_rows: int = Field(..., description="总行数")
    columns: List[str] = Field(..., description="列名列表")
    has_more: bool = Field(..., description="是否还有更多数据")


class ColumnAnalysisRequest(BaseSchema):
    """列分析请求模式"""
    columns: List[str] = Field(..., min_items=1, description="要分析的列名列表")
    analysis_types: List[str] = Field(
        default_factory=lambda: ['basic', 'distribution', 'correlation'],
        description="分析类型列表"
    )
    
    @validator('analysis_types')
    def validate_analysis_types(cls, v):
        """验证分析类型"""
        allowed_types = ['basic', 'distribution', 'correlation', 'outliers', 'missing_pattern']
        invalid_types = [t for t in v if t not in allowed_types]
        if invalid_types:
            raise ValueError(f'无效的分析类型: {", ".join(invalid_types)}')
        return v


class ColumnAnalysisResponse(BaseSchema):
    """列分析响应模式"""
    column_name: str = Field(..., description="列名")
    data_type: str = Field(..., description="数据类型")
    basic_stats: Dict[str, Any] = Field(..., description="基本统计信息")
    distribution: Optional[Dict[str, Any]] = Field(None, description="分布信息")
    outliers: Optional[Dict[str, Any]] = Field(None, description="异常值信息")
    missing_pattern: Optional[Dict[str, Any]] = Field(None, description="缺失值模式")


# ==================== 数据导出模式 ====================

class DataExportRequest(BaseSchema):
    """数据导出请求模式"""
    format: DatasetFileType = Field(..., description="导出格式")
    columns: Optional[List[str]] = Field(None, description="导出列，None表示所有列")
    filters: Optional[Dict[str, Any]] = Field(None, description="过滤条件")
    limit: Optional[int] = Field(None, ge=1, description="导出行数限制")
    include_header: bool = Field(True, description="是否包含表头")


class DataExportResponse(BaseSchema):
    """数据导出响应模式"""
    task_id: str = Field(..., description="导出任务ID")
    format: str = Field(..., description="导出格式")
    estimated_size: Optional[int] = Field(None, description="预计文件大小(字节)")
    download_url: Optional[str] = Field(None, description="下载链接（任务完成后可用）")


# ==================== 数据集统计模式 ====================

class DatasetStats(BaseSchema):
    """数据集统计信息模式"""
    total_datasets: int = Field(..., description="总数据集数")
    ready_datasets: int = Field(..., description="就绪数据集数")
    processing_datasets: int = Field(..., description="处理中数据集数")
    error_datasets: int = Field(..., description="错误数据集数")
    
    # 文件类型分布
    file_type_distribution: Dict[str, int] = Field(..., description="文件类型分布")
    
    # 大小统计
    total_size: int = Field(..., description="总文件大小(字节)")
    avg_size: float = Field(..., description="平均文件大小(字节)")
    
    # 使用统计
    most_used_datasets: List[DatasetSummary] = Field(..., description="使用最多的数据集")
    recent_uploads: List[DatasetSummary] = Field(..., description="最近上传的数据集")


# 导出主要组件
__all__ = [
    # 枚举
    "DatasetFileType", "DataProcessingOperation", "FillMethod", "NormalizationMethod",
    
    # 基础模式
    "DatasetBase", "DatasetCreate", "DatasetUpdate",
    
    # 响应模式
    "DatasetInDB", "DatasetResponse", "DatasetDetail", "DatasetSummary",
    "ColumnInfo", "DatasetStatistics",
    
    # 上传模式
    "FileUploadRequest", "FileUploadResponse", "UploadProgress",
    
    # 预处理模式
    "PreprocessingOperation", "PreprocessingRequest", "PreprocessingResponse", "PreprocessingProgress",
    
    # 查询和分析模式
    "DatasetListQuery", "DataSampleRequest", "DataSampleResponse",
    "ColumnAnalysisRequest", "ColumnAnalysisResponse",
    
    # 导出模式
    "DataExportRequest", "DataExportResponse",
    
    # 统计模式
    "DatasetStats"
]