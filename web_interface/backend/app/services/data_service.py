"""
数据管理服务

提供数据集的完整生命周期管理，包括上传、预处理、验证、存储等功能。
支持多种数据格式和自动化数据分析，集成TradeMaster数据处理能力。
"""

import os
import asyncio
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, Any, Optional, List, Union, BinaryIO
from datetime import datetime, timedelta
from enum import Enum
from io import StringIO, BytesIO

from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete
from sqlalchemy.orm import selectinload

from app.core.config import settings
from app.core.trademaster_config import get_config_adapter
from app.services.trademaster_integration import (
    get_integration_service,
    TradeMasterAPIException
)
from app.models.database import (
    Dataset,
    DatasetStatus,
    User
)


class DataServiceError(Exception):
    """数据服务异常"""
    pass


class DataFormat(str, Enum):
    """数据格式枚举"""
    CSV = "csv"
    EXCEL = "excel" 
    JSON = "json"
    PARQUET = "parquet"
    HDF5 = "hdf5"


class DataType(str, Enum):
    """数据类型枚举"""
    STOCK_PRICE = "stock_price"
    CRYPTO_PRICE = "crypto_price"
    FUTURES_PRICE = "futures_price"
    OPTIONS_PRICE = "options_price"
    ECONOMIC_DATA = "economic_data"
    NEWS_DATA = "news_data"
    SOCIAL_MEDIA = "social_media"
    CUSTOM = "custom"


class DataQualityLevel(str, Enum):
    """数据质量级别"""
    EXCELLENT = "excellent"     # 90-100%
    GOOD = "good"              # 80-90%
    FAIR = "fair"              # 70-80%
    POOR = "poor"              # <70%


class DataService:
    """数据管理服务
    
    提供数据的完整生命周期管理功能：
    - 数据上传和导入
    - 数据验证和清洗
    - 数据预处理和特征工程
    - 数据质量评估
    - 数据存储和索引
    """
    
    def __init__(self):
        """初始化数据服务"""
        self.config_adapter = get_trademaster_config_adapter()
        self.trademaster_service = get_integration_service()
        
        # 数据存储路径
        self.data_root = Path(settings.DATA_DIR if hasattr(settings, 'DATA_DIR') else 'data')
        self.upload_dir = self.data_root / 'uploads'
        self.processed_dir = self.data_root / 'processed'
        self.cache_dir = self.data_root / 'cache'
        
        # 创建目录
        for dir_path in [self.upload_dir, self.processed_dir, self.cache_dir]:
            dir_path.mkdir(parents=True, exist_ok=True)
        
        # 支持的文件格式
        self.supported_formats = {
            '.csv': DataFormat.CSV,
            '.xlsx': DataFormat.EXCEL,
            '.xls': DataFormat.EXCEL,
            '.json': DataFormat.JSON,
            '.parquet': DataFormat.PARQUET,
            '.h5': DataFormat.HDF5,
            '.hdf5': DataFormat.HDF5
        }
        
        # 必需的价格数据列
        self.required_price_columns = {
            DataType.STOCK_PRICE: ['date', 'open', 'high', 'low', 'close', 'volume'],
            DataType.CRYPTO_PRICE: ['date', 'open', 'high', 'low', 'close', 'volume'],
            DataType.FUTURES_PRICE: ['date', 'open', 'high', 'low', 'close', 'volume'],
            DataType.OPTIONS_PRICE: ['date', 'strike', 'expiry', 'option_type', 'price']
        }
        
        logger.info("数据服务初始化完成")
    
    # ==================== 数据上传和导入 ====================
    
    async def upload_dataset(
        self,
        db: AsyncSession,
        file: BinaryIO,
        filename: str,
        data_type: DataType,
        user_id: int,
        description: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """上传数据集
        
        Args:
            db: 数据库会话
            file: 文件对象
            filename: 文件名
            data_type: 数据类型
            user_id: 用户ID
            description: 数据描述
            metadata: 元数据
            
        Returns:
            Dict[str, Any]: 上传结果
            
        Raises:
            DataServiceError: 上传失败时抛出
        """
        try:
            # 验证文件格式
            file_ext = Path(filename).suffix.lower()
            if file_ext not in self.supported_formats:
                raise DataServiceError(f"不支持的文件格式: {file_ext}")
            
            data_format = self.supported_formats[file_ext]
            
            # 生成唯一文件名
            timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            unique_filename = f"{user_id}_{timestamp}_{filename}"
            file_path = self.upload_dir / unique_filename
            
            # 保存文件
            content = await self._read_file_content(file)
            with open(file_path, 'wb') as f:
                f.write(content)
            
            file_size = len(content)
            
            # 创建数据集记录
            dataset = Dataset(
                name=Path(filename).stem,
                description=description,
                file_path=str(file_path),
                file_size=file_size,
                file_type=data_format.value,
                status=DatasetStatus.UPLOADING,
                owner_id=user_id
            )
            
            db.add(dataset)
            await db.commit()
            await db.refresh(dataset)
            
            # 异步处理数据
            asyncio.create_task(
                self._process_dataset_async(db, dataset.id, data_type, metadata or {})
            )
            
            logger.info(f"数据集上传成功: {filename} (ID: {dataset.id})")
            
            return {
                "dataset_id": dataset.id,
                "filename": filename,
                "file_size": file_size,
                "data_format": data_format.value,
                "status": "uploaded",
                "message": "数据集上传成功，正在处理中"
            }
            
        except Exception as e:
            await db.rollback()
            logger.error(f"数据集上传失败: {str(e)}")
            raise DataServiceError(f"数据集上传失败: {str(e)}")
    
    async def import_from_url(
        self,
        db: AsyncSession,
        url: str,
        data_type: DataType,
        user_id: int,
        name: Optional[str] = None,
        description: Optional[str] = None
    ) -> Dict[str, Any]:
        """从URL导入数据
        
        Args:
            db: 数据库会话
            url: 数据源URL
            data_type: 数据类型
            user_id: 用户ID
            name: 数据集名称
            description: 数据描述
            
        Returns:
            Dict[str, Any]: 导入结果
        """
        try:
            import httpx
            
            # 下载数据
            async with httpx.AsyncClient() as client:
                response = await client.get(url)
                response.raise_for_status()
                content = response.content
            
            # 推断文件格式
            content_type = response.headers.get('content-type', '')
            if 'csv' in content_type:
                data_format = DataFormat.CSV
                file_ext = '.csv'
            elif 'json' in content_type:
                data_format = DataFormat.JSON
                file_ext = '.json'
            else:
                # 尝试从URL推断
                file_ext = Path(url).suffix.lower()
                if file_ext not in self.supported_formats:
                    file_ext = '.csv'  # 默认CSV
                data_format = self.supported_formats[file_ext]
            
            # 生成文件名
            if not name:
                name = f"imported_data_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
            
            filename = f"{name}{file_ext}"
            file_path = self.upload_dir / filename
            
            # 保存文件
            with open(file_path, 'wb') as f:
                f.write(content)
            
            # 创建数据集记录
            dataset = Dataset(
                name=name,
                description=description or f"从URL导入: {url}",
                file_path=str(file_path),
                file_size=len(content),
                file_type=data_format.value,
                status=DatasetStatus.UPLOADING,
                owner_id=user_id
            )
            
            db.add(dataset)
            await db.commit()
            await db.refresh(dataset)
            
            # 异步处理数据
            asyncio.create_task(
                self._process_dataset_async(db, dataset.id, data_type, {"source_url": url})
            )
            
            logger.info(f"数据集导入成功: {url} (ID: {dataset.id})")
            
            return {
                "dataset_id": dataset.id,
                "name": name,
                "source_url": url,
                "file_size": len(content),
                "status": "imported",
                "message": "数据集导入成功，正在处理中"
            }
            
        except Exception as e:
            await db.rollback()
            logger.error(f"数据集导入失败: {str(e)}")
            raise DataServiceError(f"数据集导入失败: {str(e)}")
    
    # ==================== 数据处理和分析 ====================
    
    async def _process_dataset_async(
        self,
        db: AsyncSession,
        dataset_id: int,
        data_type: DataType,
        metadata: Dict[str, Any]
    ):
        """异步处理数据集"""
        try:
            # 更新状态为处理中
            await db.execute(
                update(Dataset)
                .where(Dataset.id == dataset_id)
                .values(status=DatasetStatus.PROCESSING)
            )
            await db.commit()
            
            # 获取数据集
            result = await db.execute(
                select(Dataset).where(Dataset.id == dataset_id)
            )
            dataset = result.scalar_one()
            
            # 加载数据
            df = await self._load_dataframe(dataset.file_path, dataset.file_type)
            
            # 数据验证
            validation_result = await self._validate_data(df, data_type)
            
            # 数据分析
            analysis_result = await self._analyze_data(df, data_type)
            
            # 数据清洗和预处理
            cleaned_df = await self._clean_data(df, data_type)
            
            # 保存处理后的数据
            processed_path = await self._save_processed_data(
                cleaned_df, dataset_id, dataset.name
            )
            
            # 更新数据集信息
            update_data = {
                "status": DatasetStatus.READY,
                "row_count": len(cleaned_df),
                "column_count": len(cleaned_df.columns),
                "columns": [
                    {
                        "name": col,
                        "dtype": str(cleaned_df[col].dtype),
                        "null_count": int(cleaned_df[col].isnull().sum()),
                        "unique_count": int(cleaned_df[col].nunique())
                    }
                    for col in cleaned_df.columns
                ],
                "statistics": analysis_result,
                "sample_data": cleaned_df.head(10).to_dict('records'),
                "processed_at": datetime.utcnow()
            }
            
            await db.execute(
                update(Dataset)
                .where(Dataset.id == dataset_id)
                .values(**update_data)
            )
            await db.commit()
            
            logger.info(f"数据集处理完成: {dataset.name} (ID: {dataset_id})")
            
        except Exception as e:
            # 更新为错误状态
            await db.execute(
                update(Dataset)
                .where(Dataset.id == dataset_id)
                .values(
                    status=DatasetStatus.ERROR,
                    error_message=str(e)
                )
            )
            await db.commit()
            logger.error(f"数据集处理失败: {dataset_id}, {str(e)}")
    
    async def _load_dataframe(self, file_path: str, file_type: str) -> pd.DataFrame:
        """加载数据文件为DataFrame"""
        try:
            if file_type == DataFormat.CSV.value:
                # 尝试不同的编码
                for encoding in ['utf-8', 'gbk', 'latin1']:
                    try:
                        df = pd.read_csv(file_path, encoding=encoding)
                        break
                    except UnicodeDecodeError:
                        continue
                else:
                    raise DataServiceError("无法解析CSV文件，请检查文件编码")
            
            elif file_type == DataFormat.EXCEL.value:
                df = pd.read_excel(file_path)
            
            elif file_type == DataFormat.JSON.value:
                df = pd.read_json(file_path)
            
            elif file_type == DataFormat.PARQUET.value:
                df = pd.read_parquet(file_path)
            
            elif file_type in [DataFormat.HDF5.value]:
                df = pd.read_hdf(file_path)
            
            else:
                raise DataServiceError(f"不支持的文件类型: {file_type}")
            
            if df.empty:
                raise DataServiceError("数据文件为空")
            
            return df
            
        except Exception as e:
            logger.error(f"加载数据文件失败: {file_path}, {str(e)}")
            raise DataServiceError(f"加载数据文件失败: {str(e)}")
    
    async def _validate_data(self, df: pd.DataFrame, data_type: DataType) -> Dict[str, Any]:
        """验证数据格式和质量"""
        validation_result = {
            "is_valid": True,
            "errors": [],
            "warnings": [],
            "quality_score": 100.0,
            "quality_level": DataQualityLevel.EXCELLENT
        }
        
        try:
            # 检查基本结构
            if df.empty:
                validation_result["errors"].append("数据集为空")
                validation_result["is_valid"] = False
                return validation_result
            
            # 检查必需列（针对价格数据）
            if data_type in self.required_price_columns:
                required_cols = self.required_price_columns[data_type]
                missing_cols = [col for col in required_cols if col not in df.columns]
                
                if missing_cols:
                    validation_result["errors"].append(f"缺少必需列: {missing_cols}")
                    validation_result["is_valid"] = False
            
            # 计算数据质量分数
            quality_score = 100.0
            
            # 检查缺失值
            null_ratio = df.isnull().sum().sum() / (len(df) * len(df.columns))
            if null_ratio > 0.1:
                validation_result["warnings"].append(f"缺失值比例较高: {null_ratio:.2%}")
                quality_score -= null_ratio * 30
            
            # 检查重复值
            duplicate_ratio = df.duplicated().sum() / len(df)
            if duplicate_ratio > 0.05:
                validation_result["warnings"].append(f"重复数据比例: {duplicate_ratio:.2%}")
                quality_score -= duplicate_ratio * 20
            
            # 检查数据类型
            for col in df.columns:
                if col.lower() in ['date', 'time', 'timestamp']:
                    try:
                        pd.to_datetime(df[col])
                    except:
                        validation_result["warnings"].append(f"日期列格式可能有问题: {col}")
                        quality_score -= 5
            
            # 确定质量级别
            validation_result["quality_score"] = max(0, quality_score)
            
            if quality_score >= 90:
                validation_result["quality_level"] = DataQualityLevel.EXCELLENT
            elif quality_score >= 80:
                validation_result["quality_level"] = DataQualityLevel.GOOD
            elif quality_score >= 70:
                validation_result["quality_level"] = DataQualityLevel.FAIR
            else:
                validation_result["quality_level"] = DataQualityLevel.POOR
            
            return validation_result
            
        except Exception as e:
            logger.error(f"数据验证失败: {str(e)}")
            validation_result["errors"].append(f"验证过程失败: {str(e)}")
            validation_result["is_valid"] = False
            return validation_result
    
    async def _analyze_data(self, df: pd.DataFrame, data_type: DataType) -> Dict[str, Any]:
        """分析数据统计信息"""
        try:
            analysis = {
                "basic_stats": {},
                "data_types": {},
                "missing_values": {},
                "unique_values": {},
                "outliers": {},
                "correlations": {},
                "time_series_info": {}
            }
            
            # 基本统计信息
            numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
            if numeric_cols:
                analysis["basic_stats"] = df[numeric_cols].describe().to_dict()
            
            # 数据类型信息
            analysis["data_types"] = {col: str(dtype) for col, dtype in df.dtypes.items()}
            
            # 缺失值分析
            analysis["missing_values"] = df.isnull().sum().to_dict()
            
            # 唯一值分析
            analysis["unique_values"] = df.nunique().to_dict()
            
            # 异常值检测（仅对数值列）
            for col in numeric_cols:
                Q1 = df[col].quantile(0.25)
                Q3 = df[col].quantile(0.75)
                IQR = Q3 - Q1
                outlier_count = ((df[col] < Q1 - 1.5 * IQR) | (df[col] > Q3 + 1.5 * IQR)).sum()
                analysis["outliers"][col] = int(outlier_count)
            
            # 相关性分析（仅对数值列，且列数不超过20）
            if len(numeric_cols) > 1 and len(numeric_cols) <= 20:
                corr_matrix = df[numeric_cols].corr()
                analysis["correlations"] = corr_matrix.to_dict()
            
            # 时间序列分析
            date_cols = []
            for col in df.columns:
                if col.lower() in ['date', 'time', 'timestamp'] or 'date' in col.lower():
                    try:
                        pd.to_datetime(df[col])
                        date_cols.append(col)
                    except:
                        continue
            
            if date_cols:
                date_col = date_cols[0]
                df_temp = df.copy()
                df_temp[date_col] = pd.to_datetime(df_temp[date_col])
                
                analysis["time_series_info"] = {
                    "date_column": date_col,
                    "start_date": df_temp[date_col].min().isoformat(),
                    "end_date": df_temp[date_col].max().isoformat(),
                    "time_span_days": (df_temp[date_col].max() - df_temp[date_col].min()).days,
                    "frequency": self._infer_frequency(df_temp[date_col])
                }
            
            return analysis
            
        except Exception as e:
            logger.error(f"数据分析失败: {str(e)}")
            return {"error": f"分析失败: {str(e)}"}
    
    async def _clean_data(self, df: pd.DataFrame, data_type: DataType) -> pd.DataFrame:
        """清洗和预处理数据"""
        try:
            cleaned_df = df.copy()
            
            # 删除完全重复的行
            cleaned_df = cleaned_df.drop_duplicates()
            
            # 处理日期列
            for col in cleaned_df.columns:
                if col.lower() in ['date', 'time', 'timestamp'] or 'date' in col.lower():
                    try:
                        cleaned_df[col] = pd.to_datetime(cleaned_df[col])
                    except:
                        continue
            
            # 处理数值列
            numeric_cols = cleaned_df.select_dtypes(include=[np.number]).columns
            for col in numeric_cols:
                # 处理无穷大值
                cleaned_df[col] = cleaned_df[col].replace([np.inf, -np.inf], np.nan)
                
                # 简单的异常值处理（可选）
                Q1 = cleaned_df[col].quantile(0.25)
                Q3 = cleaned_df[col].quantile(0.75)
                IQR = Q3 - Q1
                
                # 标记极端异常值为NaN
                extreme_outliers = (cleaned_df[col] < Q1 - 3 * IQR) | (cleaned_df[col] > Q3 + 3 * IQR)
                if extreme_outliers.sum() / len(cleaned_df) < 0.01:  # 只有不到1%的数据是极端异常值才处理
                    cleaned_df.loc[extreme_outliers, col] = np.nan
            
            # 按时间排序（如果有日期列）
            date_cols = [col for col in cleaned_df.columns 
                        if cleaned_df[col].dtype == 'datetime64[ns]']
            if date_cols:
                cleaned_df = cleaned_df.sort_values(date_cols[0])
                cleaned_df = cleaned_df.reset_index(drop=True)
            
            return cleaned_df
            
        except Exception as e:
            logger.error(f"数据清洗失败: {str(e)}")
            return df  # 返回原始数据
    
    async def _save_processed_data(
        self,
        df: pd.DataFrame,
        dataset_id: int,
        dataset_name: str
    ) -> str:
        """保存处理后的数据"""
        try:
            # 生成文件名
            safe_name = "".join(c for c in dataset_name if c.isalnum() or c in (' ', '-', '_')).rstrip()
            filename = f"{dataset_id}_{safe_name}_processed.parquet"
            file_path = self.processed_dir / filename
            
            # 保存为Parquet格式（高效且保持数据类型）
            df.to_parquet(file_path, index=False)
            
            return str(file_path)
            
        except Exception as e:
            logger.error(f"保存处理数据失败: {str(e)}")
            raise DataServiceError(f"保存处理数据失败: {str(e)}")
    
    async def _read_file_content(self, file: BinaryIO) -> bytes:
        """读取文件内容"""
        if hasattr(file, 'read'):
            if asyncio.iscoroutinefunction(file.read):
                return await file.read()
            else:
                return file.read()
        else:
            return file
    
    def _infer_frequency(self, date_series: pd.Series) -> str:
        """推断时间序列频率"""
        try:
            if len(date_series) < 2:
                return "unknown"
            
            # 计算时间间隔
            diff = date_series.diff().dropna()
            mode_diff = diff.mode()
            
            if len(mode_diff) == 0:
                return "irregular"
            
            mode_seconds = mode_diff.iloc[0].total_seconds()
            
            if mode_seconds == 86400:  # 1 day
                return "daily"
            elif mode_seconds == 3600:  # 1 hour
                return "hourly"
            elif mode_seconds == 60:  # 1 minute
                return "minutely"
            elif mode_seconds == 604800:  # 1 week
                return "weekly"
            elif 2592000 <= mode_seconds <= 2678400:  # ~1 month
                return "monthly"
            else:
                return f"{mode_seconds}s"
                
        except:
            return "unknown"
    
    # ==================== 数据查询和管理 ====================
    
    async def get_dataset(
        self,
        db: AsyncSession,
        dataset_id: int,
        user_id: int
    ) -> Dict[str, Any]:
        """获取数据集信息"""
        try:
            result = await db.execute(
                select(Dataset).where(
                    Dataset.id == dataset_id,
                    Dataset.owner_id == user_id
                )
            )
            dataset = result.scalar_one_or_none()
            
            if not dataset:
                raise DataServiceError("数据集不存在或无权限访问")
            
            return {
                "id": dataset.id,
                "uuid": dataset.uuid,
                "name": dataset.name,
                "description": dataset.description,
                "file_type": dataset.file_type,
                "file_size": dataset.file_size,
                "row_count": dataset.row_count,
                "column_count": dataset.column_count,
                "columns": dataset.columns,
                "status": dataset.status.value,
                "statistics": dataset.statistics,
                "sample_data": dataset.sample_data,
                "created_at": dataset.created_at.isoformat(),
                "processed_at": dataset.processed_at.isoformat() if dataset.processed_at else None,
                "error_message": dataset.error_message
            }
            
        except Exception as e:
            logger.error(f"获取数据集失败: {str(e)}")
            raise DataServiceError(f"获取数据集失败: {str(e)}")
    
    async def list_datasets(
        self,
        db: AsyncSession,
        user_id: int,
        skip: int = 0,
        limit: int = 100,
        status_filter: Optional[DatasetStatus] = None
    ) -> Dict[str, Any]:
        """列出用户的数据集"""
        try:
            query = select(Dataset).where(Dataset.owner_id == user_id)
            
            if status_filter:
                query = query.where(Dataset.status == status_filter)
            
            # 获取总数
            count_result = await db.execute(
                select(func.count(Dataset.id)).where(Dataset.owner_id == user_id)
            )
            total = count_result.scalar()
            
            # 分页查询
            query = query.offset(skip).limit(limit).order_by(Dataset.created_at.desc())
            result = await db.execute(query)
            datasets = result.scalars().all()
            
            dataset_list = []
            for dataset in datasets:
                dataset_list.append({
                    "id": dataset.id,
                    "name": dataset.name,
                    "description": dataset.description,
                    "file_type": dataset.file_type,
                    "file_size": dataset.file_size,
                    "row_count": dataset.row_count,
                    "column_count": dataset.column_count,
                    "status": dataset.status.value,
                    "created_at": dataset.created_at.isoformat(),
                    "processed_at": dataset.processed_at.isoformat() if dataset.processed_at else None
                })
            
            return {
                "datasets": dataset_list,
                "total": total,
                "skip": skip,
                "limit": limit
            }
            
        except Exception as e:
            logger.error(f"列出数据集失败: {str(e)}")
            raise DataServiceError(f"列出数据集失败: {str(e)}")
    
    async def delete_dataset(
        self,
        db: AsyncSession,
        dataset_id: int,
        user_id: int
    ) -> Dict[str, Any]:
        """删除数据集"""
        try:
            # 获取数据集
            result = await db.execute(
                select(Dataset).where(
                    Dataset.id == dataset_id,
                    Dataset.owner_id == user_id
                )
            )
            dataset = result.scalar_one_or_none()
            
            if not dataset:
                raise DataServiceError("数据集不存在或无权限访问")
            
            # 删除文件
            try:
                if os.path.exists(dataset.file_path):
                    os.remove(dataset.file_path)
            except Exception as e:
                logger.warning(f"删除数据文件失败: {dataset.file_path}, {str(e)}")
            
            # 删除数据库记录
            await db.execute(
                delete(Dataset).where(Dataset.id == dataset_id)
            )
            await db.commit()
            
            logger.info(f"数据集删除成功: {dataset.name} (ID: {dataset_id})")
            
            return {
                "message": "数据集删除成功",
                "dataset_id": dataset_id,
                "dataset_name": dataset.name,
                "deleted_at": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            await db.rollback()
            logger.error(f"数据集删除失败: {str(e)}")
            raise DataServiceError(f"数据集删除失败: {str(e)}")


# 全局服务实例
_data_service = None

def get_data_service() -> DataService:
    """获取数据服务实例
    
    Returns:
        DataService: 数据服务实例
    """
    global _data_service
    if _data_service is None:
        _data_service = DataService()
    return _data_service


# 导出主要类和函数
__all__ = [
    "DataService",
    "DataServiceError",
    "DataFormat",
    "DataType",
    "DataQualityLevel",
    "get_data_service"
]