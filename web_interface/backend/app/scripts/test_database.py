"""
数据库测试脚本

测试数据库连接、模型创建、基本CRUD操作等功能。
用于验证数据模型系统的正确性和完整性。
"""

import asyncio
import sys
import os
from datetime import datetime
from typing import List, Dict, Any

# 添加项目路径
current_path = os.path.dirname(os.path.abspath(__file__))
parent_path = os.path.dirname(os.path.dirname(current_path))
sys.path.insert(0, parent_path)

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from passlib.context import CryptContext

from app.core.config import settings
from app.core.database import (
    check_database_connection, get_database_info, get_db_session
)
from app.models.database import (
    User, UserRole, UserSession,
    Strategy, StrategyType, StrategyStatus, StrategyVersion,
    Dataset, DatasetStatus,
    TrainingJob, TrainingStatus, TrainingMetric,
    Evaluation, EvaluationType, EvaluationStatus,
    SystemLog, LogLevel,
    CeleryTask, TaskStatus
)

# 测试结果存储
test_results: List[Dict[str, Any]] = []

def log_test_result(test_name: str, success: bool, message: str = "", error: str = ""):
    """记录测试结果"""
    test_results.append({
        "test_name": test_name,
        "success": success,
        "message": message,
        "error": error,
        "timestamp": datetime.utcnow()
    })
    
    status = "✅ 通过" if success else "❌ 失败"
    print(f"{status} - {test_name}")
    if message:
        print(f"    消息: {message}")
    if error:
        print(f"    错误: {error}")


async def test_database_connection():
    """测试数据库连接"""
    try:
        is_connected = await check_database_connection()
        if is_connected:
            db_info = await get_database_info()
            message = f"数据库版本: {db_info.get('version', 'Unknown')}"
            log_test_result("数据库连接测试", True, message)
        else:
            log_test_result("数据库连接测试", False, "", "无法连接到数据库")
    except Exception as e:
        log_test_result("数据库连接测试", False, "", str(e))


async def test_user_model(session: AsyncSession):
    """测试用户模型"""
    try:
        # 创建测试用户
        pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        test_user = User(
            username="test_user",
            email="test@example.com",
            hashed_password=pwd_context.hash("test123"),
            full_name="测试用户",
            role=UserRole.USER,
            settings={"theme": "light"}
        )
        
        session.add(test_user)
        await session.flush()
        
        # 测试查询
        result = await session.execute(
            select(User).where(User.username == "test_user")
        )
        retrieved_user = result.scalar_one_or_none()
        
        if retrieved_user and retrieved_user.id == test_user.id:
            log_test_result("用户模型测试", True, f"用户ID: {test_user.id}")
        else:
            log_test_result("用户模型测试", False, "", "用户创建或查询失败")
            
        # 清理测试数据
        await session.delete(test_user)
        
    except Exception as e:
        log_test_result("用户模型测试", False, "", str(e))


async def test_strategy_model(session: AsyncSession):
    """测试策略模型"""
    try:
        # 先创建用户
        pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        owner = User(
            username="strategy_owner",
            email="owner@example.com",
            hashed_password=pwd_context.hash("test123"),
            role=UserRole.USER
        )
        session.add(owner)
        await session.flush()
        
        # 创建测试策略
        test_strategy = Strategy(
            name="测试策略",
            description="这是一个测试策略",
            strategy_type=StrategyType.ALGORITHMIC_TRADING,
            status=StrategyStatus.DRAFT,
            config={
                "task_name": "algorithmic_trading",
                "dataset_name": "test_dataset",
                "agent_name": "test_agent"
            },
            parameters={"learning_rate": 0.001},
            tags=["测试", "DQN"],
            owner_id=owner.id
        )
        
        session.add(test_strategy)
        await session.flush()
        
        # 测试关系查询
        result = await session.execute(
            select(Strategy).where(Strategy.name == "测试策略")
        )
        retrieved_strategy = result.scalar_one_or_none()
        
        if retrieved_strategy and retrieved_strategy.owner_id == owner.id:
            log_test_result("策略模型测试", True, f"策略ID: {test_strategy.id}")
        else:
            log_test_result("策略模型测试", False, "", "策略创建或关系查询失败")
        
        # 清理测试数据
        await session.delete(test_strategy)
        await session.delete(owner)
        
    except Exception as e:
        log_test_result("策略模型测试", False, "", str(e))


async def test_dataset_model(session: AsyncSession):
    """测试数据集模型"""
    try:
        # 创建用户
        pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        owner = User(
            username="dataset_owner",
            email="dataset@example.com",
            hashed_password=pwd_context.hash("test123"),
            role=UserRole.USER
        )
        session.add(owner)
        await session.flush()
        
        # 创建测试数据集
        test_dataset = Dataset(
            name="测试数据集",
            description="这是一个测试数据集",
            file_path="/test/data.csv",
            file_size=1024,
            file_type="csv",
            row_count=100,
            column_count=5,
            columns=[
                {"name": "col1", "dtype": "float64", "description": "列1"},
                {"name": "col2", "dtype": "int64", "description": "列2"}
            ],
            status=DatasetStatus.READY,
            statistics={"mean": 10.5, "std": 2.3},
            owner_id=owner.id
        )
        
        session.add(test_dataset)
        await session.flush()
        
        # 测试JSONB字段
        result = await session.execute(
            select(Dataset).where(Dataset.name == "测试数据集")
        )
        retrieved_dataset = result.scalar_one_or_none()
        
        if (retrieved_dataset and 
            retrieved_dataset.statistics["mean"] == 10.5 and
            len(retrieved_dataset.columns) == 2):
            log_test_result("数据集模型测试", True, f"数据集ID: {test_dataset.id}")
        else:
            log_test_result("数据集模型测试", False, "", "数据集JSONB字段测试失败")
        
        # 清理测试数据
        await session.delete(test_dataset)
        await session.delete(owner)
        
    except Exception as e:
        log_test_result("数据集模型测试", False, "", str(e))


async def test_training_job_model(session: AsyncSession):
    """测试训练任务模型"""
    try:
        # 创建依赖数据
        pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        user = User(
            username="trainer",
            email="trainer@example.com",
            hashed_password=pwd_context.hash("test123"),
            role=UserRole.USER
        )
        session.add(user)
        await session.flush()
        
        strategy = Strategy(
            name="训练策略",
            strategy_type=StrategyType.ALGORITHMIC_TRADING,
            config={"task_name": "test"},
            owner_id=user.id
        )
        session.add(strategy)
        await session.flush()
        
        # 创建训练任务
        training_job = TrainingJob(
            name="测试训练任务",
            description="这是一个测试训练任务",
            status=TrainingStatus.PENDING,
            progress=0.0,
            current_epoch=0,
            total_epochs=100,
            config={
                "task_name": "algorithmic_trading",
                "epochs": 100,
                "batch_size": 32
            },
            hyperparameters={
                "learning_rate": 0.001,
                "gamma": 0.99
            },
            strategy_id=strategy.id,
            user_id=user.id
        )
        
        session.add(training_job)
        await session.flush()
        
        # 创建训练指标
        metric = TrainingMetric(
            training_job_id=training_job.id,
            epoch=1,
            step=100,
            metrics={
                "loss": 0.5,
                "accuracy": 0.8,
                "val_loss": 0.6
            }
        )
        session.add(metric)
        await session.flush()
        
        # 测试关系查询
        result = await session.execute(
            select(TrainingJob).where(TrainingJob.name == "测试训练任务")
        )
        retrieved_job = result.scalar_one_or_none()
        
        if retrieved_job and retrieved_job.strategy_id == strategy.id:
            log_test_result("训练任务模型测试", True, f"任务ID: {training_job.id}")
        else:
            log_test_result("训练任务模型测试", False, "", "训练任务创建或关系查询失败")
        
        # 清理测试数据
        await session.delete(metric)
        await session.delete(training_job)
        await session.delete(strategy)
        await session.delete(user)
        
    except Exception as e:
        log_test_result("训练任务模型测试", False, "", str(e))


async def test_evaluation_model(session: AsyncSession):
    """测试评估模型"""
    try:
        # 创建依赖数据  
        pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        user = User(
            username="evaluator",
            email="evaluator@example.com", 
            hashed_password=pwd_context.hash("test123"),
            role=UserRole.USER
        )
        session.add(user)
        await session.flush()
        
        strategy = Strategy(
            name="评估策略",
            strategy_type=StrategyType.ALGORITHMIC_TRADING,
            config={"task_name": "test"},
            owner_id=user.id
        )
        session.add(strategy)
        await session.flush()
        
        # 创建评估任务
        evaluation = Evaluation(
            name="测试评估任务",
            evaluation_type=EvaluationType.BACKTEST,
            status=EvaluationStatus.PENDING,
            config={
                "start_date": "2023-01-01",
                "end_date": "2023-12-31",
                "initial_capital": 100000
            },
            results={
                "total_return": 15.5,
                "sharpe_ratio": 1.8,
                "max_drawdown": -5.2
            },
            charts=[
                {
                    "type": "line",
                    "title": "收益曲线",
                    "data": [1, 1.1, 1.05, 1.15]
                }
            ],
            strategy_id=strategy.id,
            user_id=user.id
        )
        
        session.add(evaluation)
        await session.flush()
        
        # 测试查询
        result = await session.execute(
            select(Evaluation).where(Evaluation.name == "测试评估任务")
        )
        retrieved_eval = result.scalar_one_or_none()
        
        if (retrieved_eval and 
            retrieved_eval.results["total_return"] == 15.5 and
            len(retrieved_eval.charts) == 1):
            log_test_result("评估模型测试", True, f"评估ID: {evaluation.id}")
        else:
            log_test_result("评估模型测试", False, "", "评估任务创建或JSONB查询失败")
        
        # 清理测试数据
        await session.delete(evaluation)
        await session.delete(strategy)
        await session.delete(user)
        
    except Exception as e:
        log_test_result("评估模型测试", False, "", str(e))


async def test_system_log_model(session: AsyncSession):
    """测试系统日志模型"""
    try:
        # 创建系统日志
        log_entry = SystemLog(
            level=LogLevel.INFO,
            message="这是一条测试日志",
            module="test_module",
            function_name="test_function",
            metadata={
                "test_data": "value",
                "number": 123
            }
        )
        
        session.add(log_entry)
        await session.flush()
        
        # 测试查询
        result = await session.execute(
            select(SystemLog).where(SystemLog.message == "这是一条测试日志")
        )
        retrieved_log = result.scalar_one_or_none()
        
        if (retrieved_log and 
            retrieved_log.level == LogLevel.INFO and
            retrieved_log.extra_metadata["test_data"] == "value"):
            log_test_result("系统日志模型测试", True, f"日志ID: {log_entry.id}")
        else:
            log_test_result("系统日志模型测试", False, "", "系统日志创建或查询失败")
        
        # 清理测试数据
        await session.delete(log_entry)
        
    except Exception as e:
        log_test_result("系统日志模型测试", False, "", str(e))


async def test_celery_task_model(session: AsyncSession):
    """测试Celery任务模型"""
    try:
        # 创建Celery任务记录
        celery_task = CeleryTask(
            id="test-task-123",
            task_name="test.task",
            status=TaskStatus.SUCCESS,
            args=[1, 2, 3],
            kwargs={"param1": "value1"},
            result={"output": "success"},
            worker_name="worker-1"
        )
        
        session.add(celery_task)
        await session.flush()
        
        # 测试查询
        result = await session.execute(
            select(CeleryTask).where(CeleryTask.id == "test-task-123")
        )
        retrieved_task = result.scalar_one_or_none()
        
        if (retrieved_task and 
            retrieved_task.status == TaskStatus.SUCCESS and
            retrieved_task.result["output"] == "success"):
            log_test_result("Celery任务模型测试", True, f"任务ID: {celery_task.id}")
        else:
            log_test_result("Celery任务模型测试", False, "", "Celery任务创建或查询失败")
        
        # 清理测试数据
        await session.delete(celery_task)
        
    except Exception as e:
        log_test_result("Celery任务模型测试", False, "", str(e))


async def test_model_relationships(session: AsyncSession):
    """测试模型关系"""
    try:
        # 创建完整的关系链
        pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        user = User(
            username="relationship_test",
            email="rel@example.com",
            hashed_password=pwd_context.hash("test123"),
            role=UserRole.USER
        )
        session.add(user)
        await session.flush()
        
        dataset = Dataset(
            name="关系测试数据集",
            file_path="/test/rel.csv",
            file_size=1024,
            owner_id=user.id
        )
        session.add(dataset)
        await session.flush()
        
        strategy = Strategy(
            name="关系测试策略",
            strategy_type=StrategyType.ALGORITHMIC_TRADING,
            config={"task_name": "test"},
            owner_id=user.id
        )
        session.add(strategy)
        await session.flush()
        
        training_job = TrainingJob(
            name="关系测试训练",
            config={"epochs": 10},
            strategy_id=strategy.id,
            dataset_id=dataset.id,
            user_id=user.id
        )
        session.add(training_job)
        await session.flush()
        
        evaluation = Evaluation(
            name="关系测试评估",
            evaluation_type=EvaluationType.BACKTEST,
            config={"test": True},
            strategy_id=strategy.id,
            dataset_id=dataset.id,
            user_id=user.id
        )
        session.add(evaluation)
        await session.flush()
        
        # 测试用户的所有关联对象数量
        user_strategies_count = await session.scalar(
            select(func.count(Strategy.id)).where(Strategy.owner_id == user.id)
        )
        user_datasets_count = await session.scalar(
            select(func.count(Dataset.id)).where(Dataset.owner_id == user.id)
        )
        user_jobs_count = await session.scalar(
            select(func.count(TrainingJob.id)).where(TrainingJob.user_id == user.id)
        )
        user_evals_count = await session.scalar(
            select(func.count(Evaluation.id)).where(Evaluation.user_id == user.id)
        )
        
        if (user_strategies_count == 1 and user_datasets_count == 1 and 
            user_jobs_count == 1 and user_evals_count == 1):
            message = f"用户关联: 策略{user_strategies_count}, 数据集{user_datasets_count}, 训练{user_jobs_count}, 评估{user_evals_count}"
            log_test_result("模型关系测试", True, message)
        else:
            log_test_result("模型关系测试", False, "", "模型关系计数错误")
        
        # 清理测试数据
        await session.delete(evaluation)
        await session.delete(training_job)
        await session.delete(strategy)
        await session.delete(dataset)
        await session.delete(user)
        
    except Exception as e:
        log_test_result("模型关系测试", False, "", str(e))


async def run_all_tests():
    """运行所有测试"""
    print("开始数据库模型测试...")
    print("=" * 60)
    
    # 测试数据库连接
    await test_database_connection()
    
    # 运行模型测试
    async with get_db_session() as session:
        try:
            await test_user_model(session)
            await test_strategy_model(session)
            await test_dataset_model(session)
            await test_training_job_model(session)
            await test_evaluation_model(session)
            await test_system_log_model(session)
            await test_celery_task_model(session)
            await test_model_relationships(session)
            
            # 提交所有测试事务
            await session.commit()
            
        except Exception as e:
            await session.rollback()
            print(f"测试过程中发生错误: {e}")
    
    # 输出测试总结
    print("\n" + "=" * 60)
    print("测试总结")
    print("=" * 60)
    
    total_tests = len(test_results)
    passed_tests = sum(1 for result in test_results if result["success"])
    failed_tests = total_tests - passed_tests
    
    print(f"总测试数: {total_tests}")
    print(f"通过: {passed_tests}")
    print(f"失败: {failed_tests}")
    print(f"通过率: {passed_tests/total_tests*100:.1f}%")
    
    if failed_tests > 0:
        print("\n失败的测试:")
        for result in test_results:
            if not result["success"]:
                print(f"  - {result['test_name']}: {result['error']}")
    
    return failed_tests == 0


async def main():
    """主函数"""
    print("TradeMaster 数据库模型测试")
    print("=" * 60)
    
    try:
        success = await run_all_tests()
        
        if success:
            print("\n🎉 所有测试通过!")
            sys.exit(0)
        else:
            print("\n❌ 部分测试失败!")
            sys.exit(1)
            
    except Exception as e:
        print(f"\n💥 测试执行失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())