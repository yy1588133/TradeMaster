"""
数据管理API端点

提供数据上传、处理、验证、管理等功能的REST API接口。
支持多种数据格式，包括CSV、Excel、JSON等，并提供数据质量评估和清洗功能。
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
import os
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Query, BackgroundTasks
from fastapi.responses import FileResponse, StreamingResponse
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.dependencies import (
    get_db,
    get_current_active_user,
    CurrentUser,
    DatabaseSession
)
from app.services.data_service import get_data_service, DataServiceError
from app.core.config import settings
from loguru import logger

router = APIRouter()

# ==================== 请求/响应模型 ====================

class DataUploadRequest(BaseModel):
    """数据上传请求模型"""
    name: str = Field(..., description="数据集名称")
    description: Optional[str] = Field(None, description="数据集描述")
    data_type: str = Field("csv", description="数据类型")
    symbols: Optional[List[str]] = Field(None, description="包含的证券代码")
    start_date: Optional[str] = Field(None, description="数据开始日期")
    end_date: Optional[str] = Field(None, description="数据结束日期")
    tags: Optional[List[str]] = Field([], description="标签列表")


class DataProcessingRequest(BaseModel):
    """数据处理请求模型"""
    dataset_id: str = Field(..., description="数据集ID")
    processing_type: str = Field("basic", description="处理类型")
    parameters: Dict[str, Any] = Field({}, description="处理参数")
    output_format: str = Field("csv", description="输出格式")


class DataValidationRequest(BaseModel):
    """数据验证请求模型"""
    dataset_id: str = Field(..., description="数据集ID")
    validation_rules: Dict[str, Any] = Field({}, description="验证规则")
    fix_issues: bool = Field(False, description="是否自动修复问题")


class DataDownloadRequest(BaseModel):
    """数据下载请求模型"""
    dataset_ids: List[str] = Field(..., description="数据集ID列表")
    format: str = Field("csv", description="下载格式")
    include_metadata: bool = Field(True, description="是否包含元数据")


# ==================== 数据上传API ====================

@router.post("/upload", response_model=Dict[str, Any])
async def upload_data(
    background_tasks: BackgroundTasks,
    current_user: CurrentUser,
    db: DatabaseSession,
    file: UploadFile = File(...),
    name: str = Form(...),
    description: str = Form(""),
    data_type: str = Form("csv"),
    symbols: str = Form(""),
    start_date: str = Form(""),
    end_date: str = Form(""),
    tags: str = Form("")
):
    """
    上传数据文件
    
    支持的文件格式：
    - CSV (.csv)
    - Excel (.xlsx, .xls)
    - JSON (.json)
    - Parquet (.parquet)
    """
    try:
        data_service = get_data_service()
        
        # 解析标签和证券代码
        symbol_list = [s.strip() for s in symbols.split(",") if s.strip()] if symbols else []
        tag_list = [t.strip() for t in tags.split(",") if t.strip()] if tags else []
        
        # 构建上传请求
        upload_request = DataUploadRequest(
            name=name,
            description=description,
            data_type=data_type,
            symbols=symbol_list,
            start_date=start_date if start_date else None,
            end_date=end_date if end_date else None,
            tags=tag_list
        )
        
        # 执行上传
        result = await data_service.upload_dataset(
            file=file,
            request_data=upload_request.dict(),
            user_id=current_user["id"]
        )
        
        logger.info(f"用户 {current_user['username']} 成功上传数据集: {name}")
        
        return result
        
    except DataServiceError as e:
        logger.error(f"数据上传失败: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"数据上传异常: {str(e)}")
        raise HTTPException(status_code=500, detail="数据上传失败")


@router.post("/upload/batch", response_model=Dict[str, Any])
async def upload_batch_data(
    background_tasks: BackgroundTasks,
    current_user: CurrentUser,
    db: DatabaseSession,
    files: List[UploadFile] = File(...),
    batch_config: str = Form(...)
):
    """
    批量上传数据文件
    
    batch_config应为JSON字符串，包含每个文件的配置信息
    """
    try:
        import json
        data_service = get_data_service()
        
        # 解析批量配置
        try:
            batch_config_data = json.loads(batch_config)
        except json.JSONDecodeError:
            raise HTTPException(status_code=400, detail="批量配置格式错误")
        
        # 执行批量上传
        result = await data_service.upload_batch_datasets(
            files=files,
            batch_config=batch_config_data,
            user_id=current_user["id"]
        )
        
        logger.info(f"用户 {current_user['username']} 成功批量上传 {len(files)} 个数据集")
        
        return result
        
    except DataServiceError as e:
        logger.error(f"批量数据上传失败: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"批量数据上传异常: {str(e)}")
        raise HTTPException(status_code=500, detail="批量数据上传失败")


# ==================== 数据管理API ====================

@router.get("/datasets", response_model=Dict[str, Any])
async def list_datasets(
    current_user: CurrentUser,
    db: DatabaseSession,
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    search: Optional[str] = Query(None, description="搜索关键词"),
    data_type: Optional[str] = Query(None, description="数据类型筛选"),
    tags: Optional[str] = Query(None, description="标签筛选，逗号分隔"),
    sort_by: str = Query("created_at", description="排序字段"),
    sort_order: str = Query("desc", description="排序方向"),
):
    """
    获取数据集列表
    
    支持分页、搜索、筛选和排序功能
    """
    try:
        data_service = get_data_service()
        
        # 构建查询参数
        query_params = {
            "page": page,
            "page_size": page_size,
            "user_id": current_user["id"],
            "search": search,
            "data_type": data_type,
            "tags": [t.strip() for t in tags.split(",") if t.strip()] if tags else None,
            "sort_by": sort_by,
            "sort_order": sort_order
        }
        
        result = await data_service.list_datasets(query_params)
        
        return result
        
    except DataServiceError as e:
        logger.error(f"获取数据集列表失败: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"获取数据集列表异常: {str(e)}")
        raise HTTPException(status_code=500, detail="获取数据集列表失败")


@router.get("/datasets/{dataset_id}", response_model=Dict[str, Any])
async def get_dataset(
    dataset_id: str,
    current_user: CurrentUser,
    db: DatabaseSession,
    include_preview: bool = Query(True, description="是否包含数据预览"),
    preview_rows: int = Query(10, ge=1, le=100, description="预览行数")
):
    """
    获取数据集详情
    
    包括元数据、统计信息和数据预览
    """
    try:
        data_service = get_data_service()
        
        result = await data_service.get_dataset_details(
            dataset_id=dataset_id,
            user_id=current_user["id"],
            include_preview=include_preview,
            preview_rows=preview_rows
        )
        
        return result
        
    except DataServiceError as e:
        logger.error(f"获取数据集详情失败: {dataset_id}, {str(e)}")
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"获取数据集详情异常: {dataset_id}, {str(e)}")
        raise HTTPException(status_code=500, detail="获取数据集详情失败")


@router.put("/datasets/{dataset_id}", response_model=Dict[str, Any])
async def update_dataset(
    dataset_id: str,
    update_data: Dict[str, Any],
    current_user: CurrentUser,
    db: DatabaseSession
):
    """
    更新数据集信息
    
    可更新的字段：name, description, tags, symbols等
    """
    try:
        data_service = get_data_service()
        
        result = await data_service.update_dataset(
            dataset_id=dataset_id,
            update_data=update_data,
            user_id=current_user["id"]
        )
        
        logger.info(f"用户 {current_user['username']} 更新数据集: {dataset_id}")
        
        return result
        
    except DataServiceError as e:
        logger.error(f"更新数据集失败: {dataset_id}, {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"更新数据集异常: {dataset_id}, {str(e)}")
        raise HTTPException(status_code=500, detail="更新数据集失败")


@router.delete("/datasets/{dataset_id}", response_model=Dict[str, Any])
async def delete_dataset(
    dataset_id: str,
    current_user: CurrentUser,
    db: DatabaseSession,
    force: bool = Query(False, description="是否强制删除")
):
    """
    删除数据集
    
    支持软删除和硬删除
    """
    try:
        data_service = get_data_service()
        
        result = await data_service.delete_dataset(
            dataset_id=dataset_id,
            user_id=current_user["id"],
            force=force
        )
        
        logger.info(f"用户 {current_user['username']} 删除数据集: {dataset_id}")
        
        return result
        
    except DataServiceError as e:
        logger.error(f"删除数据集失败: {dataset_id}, {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"删除数据集异常: {dataset_id}, {str(e)}")
        raise HTTPException(status_code=500, detail="删除数据集失败")


# ==================== 数据处理API ====================

@router.post("/process", response_model=Dict[str, Any])
async def process_dataset(
    request: DataProcessingRequest,
    background_tasks: BackgroundTasks,
    current_user: CurrentUser,
    db: DatabaseSession
):
    """
    处理数据集
    
    支持的处理类型：
    - basic: 基础清洗
    - advanced: 高级处理
    - feature_engineering: 特征工程
    - normalization: 标准化
    """
    try:
        data_service = get_data_service()
        
        result = await data_service.process_dataset(
            dataset_id=request.dataset_id,
            processing_config={
                "type": request.processing_type,
                "parameters": request.parameters,
                "output_format": request.output_format
            },
            user_id=current_user["id"]
        )
        
        logger.info(f"用户 {current_user['username']} 启动数据处理: {request.dataset_id}")
        
        return result
        
    except DataServiceError as e:
        logger.error(f"数据处理失败: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"数据处理异常: {str(e)}")
        raise HTTPException(status_code=500, detail="数据处理失败")


@router.post("/validate", response_model=Dict[str, Any])
async def validate_dataset(
    request: DataValidationRequest,
    current_user: CurrentUser,
    db: DatabaseSession
):
    """
    验证数据集质量
    
    检查数据完整性、一致性和有效性
    """
    try:
        data_service = get_data_service()
        
        result = await data_service.validate_dataset(
            dataset_id=request.dataset_id,
            validation_config={
                "rules": request.validation_rules,
                "fix_issues": request.fix_issues
            },
            user_id=current_user["id"]
        )
        
        logger.info(f"用户 {current_user['username']} 验证数据集: {request.dataset_id}")
        
        return result
        
    except DataServiceError as e:
        logger.error(f"数据验证失败: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"数据验证异常: {str(e)}")
        raise HTTPException(status_code=500, detail="数据验证失败")


@router.get("/datasets/{dataset_id}/quality", response_model=Dict[str, Any])
async def get_dataset_quality(
    dataset_id: str,
    current_user: CurrentUser,
    db: DatabaseSession
):
    """
    获取数据集质量报告
    
    包括数据质量评分、问题统计和改进建议
    """
    try:
        data_service = get_data_service()
        
        result = await data_service.get_dataset_quality_report(
            dataset_id=dataset_id,
            user_id=current_user["id"]
        )
        
        return result
        
    except DataServiceError as e:
        logger.error(f"获取数据质量报告失败: {dataset_id}, {str(e)}")
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"获取数据质量报告异常: {dataset_id}, {str(e)}")
        raise HTTPException(status_code=500, detail="获取数据质量报告失败")


# ==================== 数据下载API ====================

@router.get("/datasets/{dataset_id}/download")
async def download_dataset(
    dataset_id: str,
    current_user: CurrentUser,
    db: DatabaseSession,
    format: str = Query("csv", description="下载格式"),
    include_metadata: bool = Query(False, description="是否包含元数据")
):
    """
    下载数据集
    
    支持的格式：csv, xlsx, json, parquet
    """
    try:
        data_service = get_data_service()
        
        # 获取下载文件信息
        download_info = await data_service.prepare_dataset_download(
            dataset_id=dataset_id,
            user_id=current_user["id"],
            format=format,
            include_metadata=include_metadata
        )
        
        file_path = Path(download_info["file_path"])
        if not file_path.exists():
            raise HTTPException(status_code=404, detail="文件不存在")
        
        logger.info(f"用户 {current_user['username']} 下载数据集: {dataset_id}")
        
        return FileResponse(
            path=str(file_path),
            filename=download_info["filename"],
            media_type=download_info["media_type"]
        )
        
    except DataServiceError as e:
        logger.error(f"数据下载失败: {dataset_id}, {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"数据下载异常: {dataset_id}, {str(e)}")
        raise HTTPException(status_code=500, detail="数据下载失败")


# ==================== 任务状态API ====================

@router.get("/tasks/{task_id}", response_model=Dict[str, Any])
async def get_data_task_status(
    task_id: str,
    current_user: CurrentUser,
    db: DatabaseSession
):
    """
    获取数据处理任务状态
    """
    try:
        data_service = get_data_service()
        
        result = await data_service.get_task_status(
            task_id=task_id,
            user_id=current_user["id"]
        )
        
        return result
        
    except DataServiceError as e:
        logger.error(f"获取任务状态失败: {task_id}, {str(e)}")
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"获取任务状态异常: {task_id}, {str(e)}")
        raise HTTPException(status_code=500, detail="获取任务状态失败")


# 导出路由器
__all__ = ["router"]