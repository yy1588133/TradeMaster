"""
评估分析服务

提供策略评估、回测分析和性能报告生成功能。
支持多种评估指标、风险分析、可视化图表和自动化报告生成。
"""

import asyncio
import json
import numpy as np
import pandas as pd
from typing import Dict, Any, Optional, List, Union
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path

from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, func
from sqlalchemy.orm import selectinload

from app.core.config import settings
from app.services.trademaster_integration import (
    get_trademaster_service,
    TradeMasterAPIException
)
from app.models.database import (
    Evaluation,
    EvaluationType,
    EvaluationStatus,
    Strategy,
    Dataset,
    TrainingJob,
    User
)


class EvaluationServiceError(Exception):
    """评估服务异常"""
    pass


class MetricType(str, Enum):
    """指标类型枚举"""
    RETURN = "return"              # 收益指标
    RISK = "risk"                  # 风险指标
    EFFICIENCY = "efficiency"      # 效率指标
    DRAWDOWN = "drawdown"          # 回撤指标
    TRADING = "trading"            # 交易指标


class RiskLevel(str, Enum):
    """风险级别枚举"""
    LOW = "low"          # 低风险
    MEDIUM = "medium"    # 中等风险
    HIGH = "high"        # 高风险
    EXTREME = "extreme"  # 极高风险


class EvaluationService:
    """评估分析服务
    
    提供策略评估和分析功能：
    - 回测分析
    - 性能评估
    - 风险分析
    - 指标计算
    - 可视化图表
    - 报告生成
    """
    
    def __init__(self):
        """初始化评估服务"""
        self.trademaster_service = get_trademaster_service()
        
        # 报告存储路径
        self.reports_dir = Path(settings.DATA_DIR if hasattr(settings, 'DATA_DIR') else 'data') / 'reports'
        self.charts_dir = Path(settings.DATA_DIR if hasattr(settings, 'DATA_DIR') else 'data') / 'charts'
        
        # 创建目录
        for dir_path in [self.reports_dir, self.charts_dir]:
            dir_path.mkdir(parents=True, exist_ok=True)
        
        # 风险级别阈值
        self.risk_thresholds = {
            "volatility": {"low": 0.1, "medium": 0.2, "high": 0.3},
            "max_drawdown": {"low": 0.05, "medium": 0.15, "high": 0.25},
            "var_95": {"low": 0.02, "medium": 0.05, "high": 0.1}
        }
        
        logger.info("评估服务初始化完成")
    
    # ==================== 评估任务管理 ====================
    
    async def create_evaluation(
        self,
        db: AsyncSession,
        strategy_id: int,
        user_id: int,
        evaluation_type: EvaluationType,
        config: Dict[str, Any],
        dataset_id: Optional[int] = None,
        name: Optional[str] = None
    ) -> Dict[str, Any]:
        """创建评估任务
        
        Args:
            db: 数据库会话
            strategy_id: 策略ID
            user_id: 用户ID
            evaluation_type: 评估类型
            config: 评估配置
            dataset_id: 数据集ID
            name: 评估名称
            
        Returns:
            Dict[str, Any]: 创建的评估任务信息
        """
        try:
            # 验证策略存在
            strategy_result = await db.execute(
                select(Strategy).where(
                    Strategy.id == strategy_id,
                    Strategy.owner_id == user_id
                )
            )
            strategy = strategy_result.scalar_one_or_none()
            
            if not strategy:
                raise EvaluationServiceError("策略不存在或无权限访问")
            
            # 生成评估名称
            if not name:
                timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
                name = f"{strategy.name}_{evaluation_type.value}_{timestamp}"
            
            # 创建评估记录
            evaluation = Evaluation(
                name=name,
                evaluation_type=evaluation_type,
                status=EvaluationStatus.PENDING,
                config=config,
                strategy_id=strategy_id,
                dataset_id=dataset_id,
                user_id=user_id
            )
            
            db.add(evaluation)
            await db.commit()
            await db.refresh(evaluation)
            
            logger.info(f"评估任务创建成功: {name} (ID: {evaluation.id})")
            
            return {
                "evaluation_id": evaluation.id,
                "name": name,
                "evaluation_type": evaluation_type.value,
                "strategy_id": strategy_id,
                "strategy_name": strategy.name,
                "status": evaluation.status.value,
                "config": config,
                "created_at": evaluation.created_at.isoformat()
            }
            
        except Exception as e:
            await db.rollback()
            logger.error(f"评估任务创建失败: {str(e)}")
            raise EvaluationServiceError(f"评估任务创建失败: {str(e)}")
    
    async def start_evaluation(
        self,
        db: AsyncSession,
        evaluation_id: int,
        user_id: int
    ) -> Dict[str, Any]:
        """启动评估任务
        
        Args:
            db: 数据库会话
            evaluation_id: 评估ID
            user_id: 用户ID
            
        Returns:
            Dict[str, Any]: 启动结果
        """
        try:
            # 获取评估任务
            result = await db.execute(
                select(Evaluation)
                .options(
                    selectinload(Evaluation.strategy),
                    selectinload(Evaluation.dataset)
                )
                .where(
                    Evaluation.id == evaluation_id,
                    Evaluation.user_id == user_id
                )
            )
            evaluation = result.scalar_one_or_none()
            
            if not evaluation:
                raise EvaluationServiceError("评估任务不存在或无权限访问")
            
            if evaluation.status != EvaluationStatus.PENDING:
                raise EvaluationServiceError(f"评估任务状态不正确: {evaluation.status}")
            
            # 更新状态为运行中
            await db.execute(
                update(Evaluation)
                .where(Evaluation.id == evaluation_id)
                .values(status=EvaluationStatus.RUNNING)
            )
            await db.commit()
            
            # 异步执行评估
            asyncio.create_task(
                self._run_evaluation_async(db, evaluation)
            )
            
            logger.info(f"评估任务启动成功: {evaluation.name}")
            
            return {
                "evaluation_id": evaluation_id,
                "status": "started",
                "message": "评估任务已启动",
                "started_at": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            await db.rollback()
            logger.error(f"评估任务启动失败: {str(e)}")
            raise EvaluationServiceError(f"评估任务启动失败: {str(e)}")
    
    async def _run_evaluation_async(
        self,
        db: AsyncSession,
        evaluation: Evaluation
    ):
        """异步执行评估"""
        try:
            # 根据评估类型执行不同的评估逻辑
            if evaluation.evaluation_type == EvaluationType.BACKTEST:
                results = await self._run_backtest_evaluation(evaluation)
            elif evaluation.evaluation_type == EvaluationType.PERFORMANCE:
                results = await self._run_performance_evaluation(evaluation)
            elif evaluation.evaluation_type == EvaluationType.RISK:
                results = await self._run_risk_evaluation(evaluation)
            elif evaluation.evaluation_type == EvaluationType.COMPARISON:
                results = await self._run_comparison_evaluation(evaluation)
            else:
                raise EvaluationServiceError(f"不支持的评估类型: {evaluation.evaluation_type}")
            
            # 生成图表
            charts = await self._generate_charts(evaluation, results)
            
            # 生成报告
            report_path = await self._generate_report(evaluation, results, charts)
            
            # 更新评估结果
            await db.execute(
                update(Evaluation)
                .where(Evaluation.id == evaluation.id)
                .values(
                    status=EvaluationStatus.COMPLETED,
                    results=results,
                    charts=charts,
                    report_path=report_path,
                    completed_at=datetime.utcnow()
                )
            )
            await db.commit()
            
            logger.info(f"评估任务完成: {evaluation.name}")
            
        except Exception as e:
            # 更新为失败状态
            await db.execute(
                update(Evaluation)
                .where(Evaluation.id == evaluation.id)
                .values(
                    status=EvaluationStatus.FAILED,
                    results={"error": str(e)},
                    completed_at=datetime.utcnow()
                )
            )
            await db.commit()
            logger.error(f"评估任务失败: {evaluation.name}, {str(e)}")
    
    # ==================== 具体评估实现 ====================
    
    async def _run_backtest_evaluation(
        self,
        evaluation: Evaluation
    ) -> Dict[str, Any]:
        """运行回测评估"""
        try:
            # 这里应该调用TradeMaster的回测功能
            # 当前实现为模拟回测结果
            
            # 模拟价格数据
            np.random.seed(42)
            dates = pd.date_range(
                start=evaluation.config.get("start_date", "2020-01-01"),
                end=evaluation.config.get("end_date", "2023-12-31"),
                freq="D"
            )
            
            # 模拟策略收益
            daily_returns = np.random.normal(0.001, 0.02, len(dates))
            cumulative_returns = (1 + pd.Series(daily_returns)).cumprod()
            
            # 模拟基准收益
            benchmark_returns = np.random.normal(0.0005, 0.015, len(dates))
            benchmark_cumulative = (1 + pd.Series(benchmark_returns)).cumprod()
            
            # 计算回测指标
            metrics = await self._calculate_backtest_metrics(
                daily_returns, benchmark_returns, cumulative_returns
            )
            
            # 模拟交易记录
            trades = self._generate_mock_trades(dates, daily_returns)
            
            results = {
                "backtest_period": {
                    "start_date": dates[0].isoformat(),
                    "end_date": dates[-1].isoformat(),
                    "total_days": len(dates)
                },
                "metrics": metrics,
                "time_series": {
                    "dates": [d.isoformat() for d in dates],
                    "strategy_returns": cumulative_returns.tolist(),
                    "benchmark_returns": benchmark_cumulative.tolist(),
                    "daily_returns": daily_returns.tolist()
                },
                "trades": trades,
                "risk_analysis": await self._analyze_risk(daily_returns),
                "performance_attribution": await self._analyze_performance_attribution(daily_returns)
            }
            
            return results
            
        except Exception as e:
            logger.error(f"回测评估失败: {str(e)}")
            raise EvaluationServiceError(f"回测评估失败: {str(e)}")
    
    async def _run_performance_evaluation(
        self,
        evaluation: Evaluation
    ) -> Dict[str, Any]:
        """运行性能评估"""
        try:
            # 模拟性能数据
            metrics = {
                # 收益指标
                "total_return": np.random.uniform(0.05, 0.25),
                "annual_return": np.random.uniform(0.08, 0.30),
                "monthly_return": np.random.uniform(0.005, 0.025),
                "daily_return": np.random.uniform(0.0001, 0.001),
                
                # 风险指标
                "volatility": np.random.uniform(0.10, 0.25),
                "sharpe_ratio": np.random.uniform(0.8, 2.5),
                "sortino_ratio": np.random.uniform(1.0, 3.0),
                "calmar_ratio": np.random.uniform(0.5, 2.0),
                
                # 回撤指标
                "max_drawdown": np.random.uniform(0.02, 0.15),
                "avg_drawdown": np.random.uniform(0.01, 0.08),
                "drawdown_duration": np.random.randint(5, 30),
                
                # 交易指标
                "total_trades": np.random.randint(100, 1000),
                "win_rate": np.random.uniform(0.45, 0.75),
                "profit_factor": np.random.uniform(1.2, 3.0),
                "avg_trade_return": np.random.uniform(0.001, 0.01)
            }
            
            # 性能等级评估
            performance_grade = self._calculate_performance_grade(metrics)
            
            # 基准比较
            benchmark_comparison = await self._compare_with_benchmark(metrics)
            
            results = {
                "performance_metrics": metrics,
                "performance_grade": performance_grade,
                "benchmark_comparison": benchmark_comparison,
                "strengths": self._identify_strengths(metrics),
                "weaknesses": self._identify_weaknesses(metrics),
                "recommendations": self._generate_recommendations(metrics)
            }
            
            return results
            
        except Exception as e:
            logger.error(f"性能评估失败: {str(e)}")
            raise EvaluationServiceError(f"性能评估失败: {str(e)}")
    
    async def _run_risk_evaluation(
        self,
        evaluation: Evaluation
    ) -> Dict[str, Any]:
        """运行风险评估"""
        try:
            # 模拟收益数据
            np.random.seed(42)
            returns = np.random.normal(0.001, 0.02, 1000)
            
            # 风险指标计算
            risk_metrics = {
                "value_at_risk_95": np.percentile(returns, 5),
                "value_at_risk_99": np.percentile(returns, 1),
                "conditional_var_95": returns[returns <= np.percentile(returns, 5)].mean(),
                "conditional_var_99": returns[returns <= np.percentile(returns, 1)].mean(),
                "volatility": np.std(returns) * np.sqrt(252),
                "skewness": float(pd.Series(returns).skew()),
                "kurtosis": float(pd.Series(returns).kurtosis()),
                "max_consecutive_losses": self._calculate_max_consecutive_losses(returns),
                "tail_ratio": self._calculate_tail_ratio(returns)
            }
            
            # 风险等级评估
            risk_level = self._assess_risk_level(risk_metrics)
            
            # 风险因子分析
            risk_factors = await self._analyze_risk_factors(returns)
            
            # 风险预警
            risk_warnings = self._generate_risk_warnings(risk_metrics)
            
            results = {
                "risk_metrics": risk_metrics,
                "risk_level": risk_level,
                "risk_factors": risk_factors,
                "risk_warnings": risk_warnings,
                "risk_recommendations": self._generate_risk_recommendations(risk_metrics, risk_level)
            }
            
            return results
            
        except Exception as e:
            logger.error(f"风险评估失败: {str(e)}")
            raise EvaluationServiceError(f"风险评估失败: {str(e)}")
    
    async def _run_comparison_evaluation(
        self,
        evaluation: Evaluation
    ) -> Dict[str, Any]:
        """运行对比评估"""
        try:
            # 获取对比策略ID列表
            compare_strategies = evaluation.config.get("compare_strategies", [])
            
            if not compare_strategies:
                raise EvaluationServiceError("未指定对比策略")
            
            # 模拟对比结果
            comparison_results = {}
            metrics_to_compare = [
                "total_return", "sharpe_ratio", "max_drawdown", 
                "win_rate", "volatility", "calmar_ratio"
            ]
            
            for strategy_id in compare_strategies:
                strategy_metrics = {}
                for metric in metrics_to_compare:
                    if metric == "total_return":
                        strategy_metrics[metric] = np.random.uniform(0.05, 0.25)
                    elif metric == "sharpe_ratio":
                        strategy_metrics[metric] = np.random.uniform(0.8, 2.5)
                    elif metric == "max_drawdown":
                        strategy_metrics[metric] = np.random.uniform(0.02, 0.15)
                    elif metric == "win_rate":
                        strategy_metrics[metric] = np.random.uniform(0.45, 0.75)
                    elif metric == "volatility":
                        strategy_metrics[metric] = np.random.uniform(0.10, 0.25)
                    elif metric == "calmar_ratio":
                        strategy_metrics[metric] = np.random.uniform(0.5, 2.0)
                
                comparison_results[f"strategy_{strategy_id}"] = strategy_metrics
            
            # 排名分析
            rankings = self._calculate_rankings(comparison_results, metrics_to_compare)
            
            # 相关性分析
            correlation_analysis = self._analyze_strategy_correlations(comparison_results)
            
            results = {
                "comparison_metrics": comparison_results,
                "rankings": rankings,
                "correlation_analysis": correlation_analysis,
                "best_performers": self._identify_best_performers(comparison_results),
                "comparison_summary": self._generate_comparison_summary(comparison_results, rankings)
            }
            
            return results
            
        except Exception as e:
            logger.error(f"对比评估失败: {str(e)}")
            raise EvaluationServiceError(f"对比评估失败: {str(e)}")
    
    # ==================== 指标计算方法 ====================
    
    async def _calculate_backtest_metrics(
        self,
        daily_returns: np.ndarray,
        benchmark_returns: np.ndarray,
        cumulative_returns: pd.Series
    ) -> Dict[str, Any]:
        """计算回测指标"""
        try:
            total_return = float((cumulative_returns.iloc[-1] - 1) * 100)
            annual_return = float(((1 + daily_returns.mean()) ** 252 - 1) * 100)
            volatility = float(daily_returns.std() * np.sqrt(252) * 100)
            
            # 计算夏普比率
            excess_returns = daily_returns - benchmark_returns
            sharpe_ratio = float(excess_returns.mean() / excess_returns.std() * np.sqrt(252)) if excess_returns.std() != 0 else 0
            
            # 计算最大回撤
            peak = cumulative_returns.expanding().max()
            drawdown = (cumulative_returns - peak) / peak
            max_drawdown = float(abs(drawdown.min()) * 100)
            
            # 计算胜率
            win_rate = float((daily_returns > 0).mean() * 100)
            
            # 计算卡尔玛比率
            calmar_ratio = float(annual_return / max_drawdown) if max_drawdown != 0 else 0
            
            return {
                "total_return": round(total_return, 2),
                "annual_return": round(annual_return, 2),
                "volatility": round(volatility, 2),
                "sharpe_ratio": round(sharpe_ratio, 3),
                "max_drawdown": round(max_drawdown, 2),
                "win_rate": round(win_rate, 2),
                "calmar_ratio": round(calmar_ratio, 3),
                "total_trades": len(daily_returns),
                "avg_daily_return": round(daily_returns.mean() * 100, 4)
            }
            
        except Exception as e:
            logger.error(f"回测指标计算失败: {str(e)}")
            return {}
    
    def _generate_mock_trades(
        self,
        dates: pd.DatetimeIndex,
        returns: np.ndarray
    ) -> List[Dict[str, Any]]:
        """生成模拟交易记录"""
        trades = []
        
        # 随机生成一些交易
        num_trades = min(100, len(dates) // 10)
        trade_indices = np.random.choice(len(dates), num_trades, replace=False)
        trade_indices.sort()
        
        for i, idx in enumerate(trade_indices):
            trade = {
                "trade_id": i + 1,
                "date": dates[idx].isoformat(),
                "action": np.random.choice(["BUY", "SELL"]),
                "quantity": int(np.random.uniform(100, 1000)),
                "price": round(np.random.uniform(50, 200), 2),
                "return": round(returns[idx] * 100, 4),
                "pnl": round(np.random.uniform(-500, 1000), 2)
            }
            trades.append(trade)
        
        return trades
    
    async def _analyze_risk(self, returns: np.ndarray) -> Dict[str, Any]:
        """风险分析"""
        return {
            "var_95": float(np.percentile(returns, 5) * 100),
            "var_99": float(np.percentile(returns, 1) * 100),
            "skewness": float(pd.Series(returns).skew()),
            "kurtosis": float(pd.Series(returns).kurtosis()),
            "downside_deviation": float(returns[returns < 0].std() * np.sqrt(252) * 100),
            "risk_level": self._assess_risk_level({"volatility": returns.std() * np.sqrt(252)})
        }
    
    async def _analyze_performance_attribution(self, returns: np.ndarray) -> Dict[str, Any]:
        """性能归因分析"""
        return {
            "alpha": round(np.random.uniform(-0.02, 0.05), 4),
            "beta": round(np.random.uniform(0.5, 1.5), 3),
            "information_ratio": round(np.random.uniform(0.3, 1.2), 3),
            "tracking_error": round(np.random.uniform(0.02, 0.08), 4),
            "factor_exposures": {
                "momentum": round(np.random.uniform(-0.5, 0.5), 3),
                "value": round(np.random.uniform(-0.3, 0.3), 3),
                "size": round(np.random.uniform(-0.2, 0.2), 3),
                "quality": round(np.random.uniform(-0.1, 0.1), 3)
            }
        }
    
    def _calculate_performance_grade(self, metrics: Dict[str, Any]) -> str:
        """计算性能等级"""
        score = 0
        
        # 基于各项指标评分
        if metrics["sharpe_ratio"] >= 2.0:
            score += 25
        elif metrics["sharpe_ratio"] >= 1.5:
            score += 20
        elif metrics["sharpe_ratio"] >= 1.0:
            score += 15
        elif metrics["sharpe_ratio"] >= 0.5:
            score += 10
        
        if metrics["max_drawdown"] <= 0.05:
            score += 25
        elif metrics["max_drawdown"] <= 0.10:
            score += 20
        elif metrics["max_drawdown"] <= 0.15:
            score += 15
        elif metrics["max_drawdown"] <= 0.20:
            score += 10
        
        if metrics["win_rate"] >= 0.70:
            score += 25
        elif metrics["win_rate"] >= 0.60:
            score += 20
        elif metrics["win_rate"] >= 0.50:
            score += 15
        elif metrics["win_rate"] >= 0.40:
            score += 10
        
        if metrics["annual_return"] >= 0.20:
            score += 25
        elif metrics["annual_return"] >= 0.15:
            score += 20
        elif metrics["annual_return"] >= 0.10:
            score += 15
        elif metrics["annual_return"] >= 0.05:
            score += 10
        
        if score >= 80:
            return "A+"
        elif score >= 70:
            return "A"
        elif score >= 60:
            return "B+"
        elif score >= 50:
            return "B"
        elif score >= 40:
            return "C+"
        elif score >= 30:
            return "C"
        else:
            return "D"
    
    async def _compare_with_benchmark(self, metrics: Dict[str, Any]) -> Dict[str, Any]:
        """与基准比较"""
        # 模拟基准指标
        benchmark_metrics = {
            "annual_return": 0.08,
            "volatility": 0.15,
            "sharpe_ratio": 0.53,
            "max_drawdown": 0.12
        }
        
        comparison = {}
        for key in benchmark_metrics:
            if key in metrics:
                benchmark_value = benchmark_metrics[key]
                strategy_value = metrics[key]
                
                if key in ["annual_return", "sharpe_ratio"]:  # 越高越好
                    outperformance = strategy_value - benchmark_value
                    better = strategy_value > benchmark_value
                else:  # 越低越好
                    outperformance = benchmark_value - strategy_value
                    better = strategy_value < benchmark_value
                
                comparison[key] = {
                    "strategy": strategy_value,
                    "benchmark": benchmark_value,
                    "outperformance": outperformance,
                    "better": better
                }
        
        return comparison
    
    def _identify_strengths(self, metrics: Dict[str, Any]) -> List[str]:
        """识别策略优势"""
        strengths = []
        
        if metrics["sharpe_ratio"] >= 1.5:
            strengths.append("优秀的风险调整收益")
        if metrics["max_drawdown"] <= 0.08:
            strengths.append("低回撤控制")
        if metrics["win_rate"] >= 0.65:
            strengths.append("高胜率表现")
        if metrics["calmar_ratio"] >= 1.5:
            strengths.append("良好的收益回撤比")
        if metrics["volatility"] <= 0.15:
            strengths.append("稳定的收益波动")
        
        return strengths if strengths else ["策略表现稳健"]
    
    def _identify_weaknesses(self, metrics: Dict[str, Any]) -> List[str]:
        """识别策略弱点"""
        weaknesses = []
        
        if metrics["sharpe_ratio"] < 0.8:
            weaknesses.append("风险调整收益偏低")
        if metrics["max_drawdown"] > 0.20:
            weaknesses.append("回撤控制有待改善")
        if metrics["win_rate"] < 0.45:
            weaknesses.append("胜率偏低")
        if metrics["volatility"] > 0.25:
            weaknesses.append("收益波动较大")
        
        return weaknesses if weaknesses else ["无明显弱点"]
    
    def _generate_recommendations(self, metrics: Dict[str, Any]) -> List[str]:
        """生成优化建议"""
        recommendations = []
        
        if metrics["max_drawdown"] > 0.15:
            recommendations.append("建议增加风险控制措施，降低最大回撤")
        if metrics["sharpe_ratio"] < 1.0:
            recommendations.append("建议优化策略参数，提高风险调整收益")
        if metrics["win_rate"] < 0.50:
            recommendations.append("建议改进选股或择时逻辑，提高胜率")
        if metrics["volatility"] > 0.20:
            recommendations.append("建议增加仓位管理，控制收益波动")
        
        return recommendations if recommendations else ["策略表现良好，继续保持"]
    
    def _assess_risk_level(self, metrics: Dict[str, Any]) -> str:
        """评估风险级别"""
        risk_score = 0
        
        volatility = metrics.get("volatility", 0)
        if volatility <= self.risk_thresholds["volatility"]["low"]:
            risk_score += 1
        elif volatility <= self.risk_thresholds["volatility"]["medium"]:
            risk_score += 2
        elif volatility <= self.risk_thresholds["volatility"]["high"]:
            risk_score += 3
        else:
            risk_score += 4
        
        max_drawdown = metrics.get("max_drawdown", 0)
        if max_drawdown <= self.risk_thresholds["max_drawdown"]["low"]:
            risk_score += 1
        elif max_drawdown <= self.risk_thresholds["max_drawdown"]["medium"]:
            risk_score += 2
        elif max_drawdown <= self.risk_thresholds["max_drawdown"]["high"]:
            risk_score += 3
        else:
            risk_score += 4
        
        if risk_score <= 3:
            return RiskLevel.LOW.value
        elif risk_score <= 5:
            return RiskLevel.MEDIUM.value
        elif risk_score <= 7:
            return RiskLevel.HIGH.value
        else:
            return RiskLevel.EXTREME.value
    
    async def _analyze_risk_factors(self, returns: np.ndarray) -> Dict[str, Any]:
        """分析风险因子"""
        return {
            "market_risk": round(np.random.uniform(0.3, 0.8), 3),
            "specific_risk": round(np.random.uniform(0.1, 0.5), 3),
            "liquidity_risk": round(np.random.uniform(0.1, 0.3), 3),
            "concentration_risk": round(np.random.uniform(0.1, 0.4), 3),
            "tail_risk": round(np.random.uniform(0.05, 0.2), 3)
        }
    
    def _generate_risk_warnings(self, risk_metrics: Dict[str, Any]) -> List[str]:
        """生成风险预警"""
        warnings = []
        
        if risk_metrics["value_at_risk_95"] < -0.05:
            warnings.append("日度VaR(95%)过高，存在较大单日损失风险")
        
        if risk_metrics["max_consecutive_losses"] > 10:
            warnings.append("连续亏损次数过多，可能存在策略失效风险")
        
        if abs(risk_metrics["skewness"]) > 1:
            warnings.append("收益分布偏度较大，存在尾部风险")
        
        if risk_metrics["kurtosis"] > 3:
            warnings.append("收益分布峰度过高，极端事件概率较大")
        
        return warnings if warnings else ["暂无风险预警"]
    
    def _generate_risk_recommendations(
        self,
        risk_metrics: Dict[str, Any],
        risk_level: str
    ) -> List[str]:
        """生成风险管理建议"""
        recommendations = []
        
        if risk_level in [RiskLevel.HIGH.value, RiskLevel.EXTREME.value]:
            recommendations.append("建议降低仓位或增加对冲措施")
            recommendations.append("考虑增加止损策略")
        
        if risk_metrics["volatility"] > 0.20:
            recommendations.append("建议采用动态仓位管理")
        
        if risk_metrics["max_consecutive_losses"] > 5:
            recommendations.append("建议增加策略信号过滤条件")
        
        return recommendations if recommendations else ["当前风险水平可接受"]
    
    def _calculate_max_consecutive_losses(self, returns: np.ndarray) -> int:
        """计算最大连续亏损次数"""
        losses = returns < 0
        max_consecutive = 0
        current_consecutive = 0
        
        for loss in losses:
            if loss:
                current_consecutive += 1
                max_consecutive = max(max_consecutive, current_consecutive)
            else:
                current_consecutive = 0
        
        return max_consecutive
    
    def _calculate_tail_ratio(self, returns: np.ndarray) -> float:
        """计算尾部比率"""
        positive_tail = np.percentile(returns, 95)
        negative_tail = abs(np.percentile(returns, 5))
        
        return float(positive_tail / negative_tail) if negative_tail != 0 else 0
    
    def _calculate_rankings(
        self,
        comparison_results: Dict[str, Dict[str, Any]],
        metrics: List[str]
    ) -> Dict[str, Dict[str, int]]:
        """计算排名"""
        rankings = {}
        
        for metric in metrics:
            metric_values = [(strategy, results[metric]) 
                           for strategy, results in comparison_results.items()]
            
            # 根据指标类型决定排序方向
            if metric in ["max_drawdown", "volatility"]:
                # 越小越好
                metric_values.sort(key=lambda x: x[1])
            else:
                # 越大越好
                metric_values.sort(key=lambda x: x[1], reverse=True)
            
            rankings[metric] = {
                strategy: rank + 1 
                for rank, (strategy, _) in enumerate(metric_values)
            }
        
        return rankings
    
    def _analyze_strategy_correlations(
        self,
        comparison_results: Dict[str, Dict[str, Any]]
    ) -> Dict[str, Any]:
        """分析策略相关性"""
        # 简化的相关性分析
        strategies = list(comparison_results.keys())
        correlations = {}
        
        for i, strategy1 in enumerate(strategies):
            for j, strategy2 in enumerate(strategies[i+1:], i+1):
                correlation = np.random.uniform(0.3, 0.9)  # 模拟相关性
                correlations[f"{strategy1}_vs_{strategy2}"] = round(correlation, 3)
        
        return {
            "pairwise_correlations": correlations,
            "avg_correlation": round(np.mean(list(correlations.values())), 3),
            "diversification_benefit": "高" if np.mean(list(correlations.values())) < 0.6 else "中等"
        }
    
    def _identify_best_performers(
        self,
        comparison_results: Dict[str, Dict[str, Any]]
    ) -> Dict[str, str]:
        """识别最佳表现者"""
        best_performers = {}
        
        metrics_to_check = {
            "highest_return": "total_return",
            "best_sharpe": "sharpe_ratio",
            "lowest_drawdown": "max_drawdown",
            "highest_win_rate": "win_rate"
        }
        
        for category, metric in metrics_to_check.items():
            if metric == "max_drawdown":
                # 越小越好
                best_strategy = min(
                    comparison_results.items(),
                    key=lambda x: x[1][metric]
                )[0]
            else:
                # 越大越好
                best_strategy = max(
                    comparison_results.items(),
                    key=lambda x: x[1][metric]
                )[0]
            
            best_performers[category] = best_strategy
        
        return best_performers
    
    def _generate_comparison_summary(
        self,
        comparison_results: Dict[str, Dict[str, Any]],
        rankings: Dict[str, Dict[str, int]]
    ) -> str:
        """生成对比总结"""
        num_strategies = len(comparison_results)
        
        # 计算平均排名
        avg_rankings = {}
        for strategy in comparison_results.keys():
            total_rank = sum(rankings[metric][strategy] for metric in rankings.keys())
            avg_rankings[strategy] = total_rank / len(rankings)
        
        best_overall = min(avg_rankings.items(), key=lambda x: x[1])[0]
        
        summary = f"在{num_strategies}个策略的对比中，{best_overall}表现最佳，"
        summary += f"平均排名为{avg_rankings[best_overall]:.1f}。"
        
        return summary
    
    # ==================== 图表和报告生成 ====================
    
    async def _generate_charts(
        self,
        evaluation: Evaluation,
        results: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """生成评估图表"""
        charts = []
        
        try:
            # 根据评估类型生成不同的图表
            if evaluation.evaluation_type == EvaluationType.BACKTEST:
                charts.extend(await self._generate_backtest_charts(results))
            elif evaluation.evaluation_type == EvaluationType.PERFORMANCE:
                charts.extend(await self._generate_performance_charts(results))
            elif evaluation.evaluation_type == EvaluationType.RISK:
                charts.extend(await self._generate_risk_charts(results))
            elif evaluation.evaluation_type == EvaluationType.COMPARISON:
                charts.extend(await self._generate_comparison_charts(results))
            
            return charts
            
        except Exception as e:
            logger.error(f"图表生成失败: {str(e)}")
            return []
    
    async def _generate_backtest_charts(self, results: Dict[str, Any]) -> List[Dict[str, Any]]:
        """生成回测图表"""
        charts = []
        
        # 收益曲线图
        charts.append({
            "type": "line_chart",
            "title": "策略收益曲线",
            "data": {
                "x": results["time_series"]["dates"],
                "series": [
                    {
                        "name": "策略收益",
                        "data": results["time_series"]["strategy_returns"]
                    },
                    {
                        "name": "基准收益",
                        "data": results["time_series"]["benchmark_returns"]
                    }
                ]
            }
        })
        
        # 回撤图
        drawdown_data = []
        cumulative = results["time_series"]["strategy_returns"]
        peak = 1
        for ret in cumulative:
            peak = max(peak, ret)
            drawdown = (ret - peak) / peak
            drawdown_data.append(drawdown)
        
        charts.append({
            "type": "area_chart",
            "title": "回撤分析",
            "data": {
                "x": results["time_series"]["dates"],
                "y": drawdown_data
            }
        })
        
        return charts
    
    async def _generate_performance_charts(self, results: Dict[str, Any]) -> List[Dict[str, Any]]:
        """生成性能图表"""
        charts = []
        
        # 性能雷达图
        metrics = results["performance_metrics"]
        charts.append({
            "type": "radar_chart",
            "title": "性能指标雷达图",
            "data": {
                "categories": ["收益", "风险控制", "稳定性", "效率", "胜率"],
                "values": [
                    min(100, metrics["annual_return"] * 500),  # 归一化到0-100
                    min(100, (0.3 - metrics["max_drawdown"]) * 333),
                    min(100, (0.3 - metrics["volatility"]) * 333),
                    min(100, metrics["sharpe_ratio"] * 40),
                    metrics["win_rate"] * 100
                ]
            }
        })
        
        return charts
    
    async def _generate_risk_charts(self, results: Dict[str, Any]) -> List[Dict[str, Any]]:
        """生成风险图表"""
        charts = []
        
        # 风险指标条形图
        risk_metrics = results["risk_metrics"]
        charts.append({
            "type": "bar_chart",
            "title": "风险指标分析",
            "data": {
                "categories": ["VaR(95%)", "VaR(99%)", "波动率", "偏度", "峰度"],
                "values": [
                    abs(risk_metrics["value_at_risk_95"]) * 100,
                    abs(risk_metrics["value_at_risk_99"]) * 100,
                    risk_metrics["volatility"] * 100,
                    abs(risk_metrics["skewness"]) * 10,
                    risk_metrics["kurtosis"]
                ]
            }
        })
        
        return charts
    
    async def _generate_comparison_charts(self, results: Dict[str, Any]) -> List[Dict[str, Any]]:
        """生成对比图表"""
        charts = []
        
        # 策略对比柱状图
        comparison_data = results["comparison_metrics"]
        strategies = list(comparison_data.keys())
        metrics = ["total_return", "sharpe_ratio", "max_drawdown"]
        
        for metric in metrics:
            charts.append({
                "type": "column_chart",
                "title": f"{metric}对比",
                "data": {
                    "categories": strategies,
                    "values": [comparison_data[strategy][metric] for strategy in strategies]
                }
            })
        
        return charts
    
    async def _generate_report(
        self,
        evaluation: Evaluation,
        results: Dict[str, Any],
        charts: List[Dict[str, Any]]
    ) -> Optional[str]:
        """生成评估报告"""
        try:
            report_filename = f"evaluation_{evaluation.id}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.json"
            report_path = self.reports_dir / report_filename
            
            report_data = {
                "evaluation_info": {
                    "id": evaluation.id,
                    "name": evaluation.name,
                    "type": evaluation.evaluation_type.value,
                    "strategy_id": evaluation.strategy_id,
                    "created_at": evaluation.created_at.isoformat(),
                    "completed_at": datetime.utcnow().isoformat()
                },
                "results": results,
                "charts": charts,
                "summary": self._generate_executive_summary(evaluation, results),
                "metadata": {
                    "generated_by": "TradeMaster Evaluation Service",
                    "version": "1.0.0"
                }
            }
            
            with open(report_path, 'w', encoding='utf-8') as f:
                json.dump(report_data, f, indent=2, ensure_ascii=False)
            
            return str(report_path)
            
        except Exception as e:
            logger.error(f"报告生成失败: {str(e)}")
            return None
    
    def _generate_executive_summary(
        self,
        evaluation: Evaluation,
        results: Dict[str, Any]
    ) -> str:
        """生成执行总结"""
        summary_parts = [
            f"评估类型：{evaluation.evaluation_type.value}",
            f"评估完成时间：{datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')}"
        ]
        
        if evaluation.evaluation_type == EvaluationType.BACKTEST:
            metrics = results.get("metrics", {})
            summary_parts.extend([
                f"总收益率：{metrics.get('total_return', 0):.2f}%",
                f"夏普比率：{metrics.get('sharpe_ratio', 0):.3f}",
                f"最大回撤：{metrics.get('max_drawdown', 0):.2f}%",
                f"胜率：{metrics.get('win_rate', 0):.2f}%"
            ])
        
        elif evaluation.evaluation_type == EvaluationType.PERFORMANCE:
            grade = results.get("performance_grade", "N/A")
            summary_parts.append(f"性能等级：{grade}")
        
        elif evaluation.evaluation_type == EvaluationType.RISK:
            risk_level = results.get("risk_level", "未知")
            warning_count = len(results.get("risk_warnings", []))
            summary_parts.extend([
                f"风险级别：{risk_level}",
                f"风险预警数量：{warning_count}"
            ])
        
        return "；".join(summary_parts)


# 全局服务实例
_evaluation_service = None

def get_evaluation_service() -> EvaluationService:
    """获取评估服务实例
    
    Returns:
        EvaluationService: 评估服务实例
    """
    global _evaluation_service
    if _evaluation_service is None:
        _evaluation_service = EvaluationService()
    return _evaluation_service


# 导出主要类和函数
__all__ = [
    "EvaluationService",
    "EvaluationServiceError",
    "MetricType",
    "RiskLevel",
    "get_evaluation_service"
]