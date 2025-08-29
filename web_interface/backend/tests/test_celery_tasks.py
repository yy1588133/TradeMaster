"""
Celery异步任务执行逻辑测试

测试重点：
1. 训练任务的完整执行流程
2. 任务状态管理和进度跟踪
3. 错误处理和重试机制
4. 资源使用监控
5. 任务取消和清理机制

这些测试直接解决代码质量评审中发现的Celery任务执行逻辑不完整问题。
"""

import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock, MagicMock, call
import subprocess
import json
import tempfile
from datetime import datetime
from pathlib import Path

from app.tasks.training_tasks import execute_training_task
from app.tasks.backtest_tasks import execute_backtest_task
from app.models.database import StrategySession, SessionStatus, PerformanceMetric


class TestTrainingTaskExecution:
    """训练任务执行测试"""
    
    @pytest.fixture
    def mock_session(self):
        """模拟训练会话"""
        session = Mock(spec=StrategySession)
        session.id = 123
        session.strategy_id = 1
        session.user_id = 1
        session.status = SessionStatus.PENDING
        session.trademaster_config = {
            "task": "algorithmic_trading",
            "dataset": {"type": "BTC"},
            "agent": {"type": "dqn", "lr": 0.001},
            "epochs": 10
        }
        session.total_epochs = 10
        session.current_epoch = 0
        session.progress = 0.0
        return session
    
    @pytest.fixture
    def mock_process(self):
        """模拟TradeMaster训练进程"""
        process = Mock(spec=subprocess.Popen)
        process.pid = 12345
        process.poll.return_value = None  # 进程运行中
        process.wait.return_value = 0  # 成功退出码
        
        # 模拟训练输出
        training_outputs = [
            "Initializing TradeMaster training...",
            "[METRICS] {\"epoch\": 1, \"loss\": 0.5, \"reward\": 10.2}",
            "Epoch: 2, Loss: 0.45, Reward: 12.5",
            "[METRICS] {\"epoch\": 3, \"loss\": 0.4, \"reward\": 15.1}",
            "Training completed successfully"
        ]
        
        process.stdout.readline.side_effect = training_outputs + [""] * 10
        return process
    
    @patch('app.tasks.training_tasks._get_session')
    @patch('app.tasks.training_tasks._update_session_status')
    @patch('app.tasks.training_tasks._create_trademaster_config')
    @patch('app.tasks.training_tasks._start_trademaster_process')
    @patch('app.tasks.training_tasks._monitor_training_process')
    @patch('app.tasks.training_tasks._update_session_final_status')
    def test_execute_training_task_success(
        self, 
        mock_update_final, mock_monitor, mock_start_process, 
        mock_create_config, mock_update_status, mock_get_session,
        mock_session
    ):
        """测试训练任务成功执行"""
        # 设置模拟返回值
        mock_get_session.return_value = mock_session
        mock_create_config.return_value = "/tmp/config.yaml"
        mock_start_process.return_value = Mock(pid=12345)
        mock_monitor.return_value = {
            "success": True,
            "return_code": 0,
            "final_metrics": {"loss": 0.1, "reward": 25.5}
        }
        
        # 执行训练任务
        result = execute_training_task(session_id=123)
        
        # 验证执行流程
        mock_get_session.assert_called_once()
        mock_update_status.assert_called()  # 状态更新被调用
        mock_create_config.assert_called_once_with(mock_session)
        mock_start_process.assert_called_once()
        mock_monitor.assert_called_once()
        mock_update_final.assert_called_once()
        
        # 验证返回结果
        assert result["success"] is True
        assert result["return_code"] == 0
        assert "final_metrics" in result
    
    @patch('app.tasks.training_tasks._get_session')
    def test_execute_training_task_session_not_found(self, mock_get_session):
        """测试会话不存在时的错误处理"""
        mock_get_session.return_value = None
        
        with pytest.raises(ValueError, match="会话不存在"):
            execute_training_task(session_id=999)
    
    @patch('app.tasks.training_tasks._get_session')
    @patch('app.tasks.training_tasks._update_session_status')
    def test_execute_training_task_exception_handling(
        self, mock_update_status, mock_get_session, mock_session
    ):
        """测试训练任务异常处理"""
        mock_get_session.return_value = mock_session
        
        # 模拟异常
        with patch('app.tasks.training_tasks._create_trademaster_config', 
                  side_effect=Exception("配置创建失败")):
            
            with pytest.raises(Exception, match="配置创建失败"):
                execute_training_task(session_id=123)
            
            # 验证错误状态更新被调用
            mock_update_status.assert_called_with(
                123, SessionStatus.FAILED, error_message="配置创建失败"
            )
    
    def test_create_trademaster_config(self, mock_session):
        """测试TradeMaster配置文件创建"""
        from app.tasks.training_tasks import _create_trademaster_config
        
        with patch('builtins.open', create=True) as mock_open:
            mock_file = Mock()
            mock_open.return_value.__enter__.return_value = mock_file
            
            with patch('yaml.dump') as mock_yaml_dump:
                config_path = _create_trademaster_config(mock_session)
                
                # 验证配置文件路径
                assert "/tmp/trademaster_configs/session_123_config.yaml" in config_path
                
                # 验证YAML配置被写入
                mock_yaml_dump.assert_called_once_with(
                    mock_session.trademaster_config,
                    mock_file,
                    default_flow_style=False
                )
    
    def test_start_trademaster_process(self, mock_session):
        """测试TradeMaster进程启动"""
        from app.tasks.training_tasks import _start_trademaster_process
        
        config_path = "/tmp/config.yaml"
        
        with patch('subprocess.Popen') as mock_popen:
            with patch('app.tasks.training_tasks._update_session_process_info') as mock_update_info:
                mock_process = Mock()
                mock_process.pid = 12345
                mock_popen.return_value = mock_process
                
                result_process = _start_trademaster_process(config_path, session_id=123)
                
                # 验证Popen调用参数
                mock_popen.assert_called_once()
                args, kwargs = mock_popen.call_args
                
                # 验证命令行参数
                assert "python" in args[0][0] or "python3" in args[0][0]
                assert "-m" in args[0]
                assert "trademaster.tools.train" in args[0]
                assert "--config" in args[0]
                assert config_path in args[0]
                
                # 验证环境变量
                assert "env" in kwargs
                assert "SESSION_ID" in kwargs["env"]
                
                # 验证进程信息更新
                mock_update_info.assert_called_once()
                
                assert result_process == mock_process
    
    def test_monitor_training_process(self, mock_process):
        """测试训练进程监控"""
        from app.tasks.training_tasks import _monitor_training_process
        
        with patch('app.tasks.training_tasks._parse_training_output') as mock_parse:
            with patch('app.tasks.training_tasks._save_performance_metrics') as mock_save_metrics:
                with patch('app.tasks.training_tasks._update_session_progress') as mock_update_progress:
                    with patch('app.tasks.training_tasks._collect_final_metrics') as mock_collect_final:
                        with patch('app.tasks.training_tasks.RealTimeDataPusher') as mock_pusher:
                            
                            # 设置解析返回值
                            mock_parse.side_effect = [
                                None,  # 普通日志行
                                {"epoch": 1, "loss": 0.5, "reward": 10.2},  # 指标行
                                {"epoch": 2, "loss": 0.45, "reward": 12.5},  # 指标行
                                None,  # 普通日志行
                            ]
                            
                            mock_collect_final.return_value = {"final_loss": 0.1}
                            
                            result = _monitor_training_process(mock_process, session_id=123)
                            
                            # 验证监控结果
                            assert result["success"] is True
                            assert result["return_code"] == 0
                            assert result["final_metrics"] == {"final_loss": 0.1}
                            
                            # 验证指标保存被调用
                            assert mock_save_metrics.call_count == 2
                            
                            # 验证进度更新被调用
                            assert mock_update_progress.call_count == 2
    
    def test_parse_training_output_json_format(self):
        """测试JSON格式训练输出解析"""
        from app.tasks.training_tasks import _parse_training_output
        
        # 测试JSON格式输出
        json_output = '[METRICS] {"epoch": 5, "loss": 0.25, "reward": 20.5, "accuracy": 0.85}'
        result = _parse_training_output(json_output)
        
        assert result is not None
        assert result["epoch"] == 5
        assert result["loss"] == 0.25
        assert result["reward"] == 20.5
        assert result["accuracy"] == 0.85
    
    def test_parse_training_output_text_format(self):
        """测试文本格式训练输出解析"""
        from app.tasks.training_tasks import _parse_training_output
        
        # 测试文本格式输出
        text_output = "Epoch: 10, Loss: 0.123, Reward: 15.67"
        result = _parse_training_output(text_output)
        
        assert result is not None
        assert result["epoch"] == 10
        assert result["loss"] == 0.123
        assert result["reward"] == 15.67
    
    def test_parse_training_output_invalid(self):
        """测试无效训练输出解析"""
        from app.tasks.training_tasks import _parse_training_output
        
        # 测试无效输出
        invalid_outputs = [
            "This is just a regular log line",
            "[METRICS] {invalid json}",
            "Random text without metrics",
            ""
        ]
        
        for output in invalid_outputs:
            result = _parse_training_output(output)
            assert result is None
    
    @patch('app.tasks.training_tasks.get_database')
    async def test_save_performance_metrics(self, mock_get_db):
        """测试性能指标保存"""
        from app.tasks.training_tasks import _save_performance_metrics
        
        mock_db = AsyncMock()
        mock_get_db.return_value.__aenter__.return_value = mock_db
        
        metrics = {
            "epoch": 5,
            "loss": 0.25,
            "reward": 20.5,
            "accuracy": 0.85,
            "step": 100
        }
        
        await _save_performance_metrics(session_id=123, metrics=metrics)
        
        # 验证数据库添加操作
        assert mock_db.add.call_count == 4  # 4个数值指标
        mock_db.commit.assert_called_once()
        
        # 验证添加的指标
        calls = mock_db.add.call_args_list
        metric_names = [call[0][0].metric_name for call in calls]
        assert "loss" in metric_names
        assert "reward" in metric_names  
        assert "accuracy" in metric_names
        # epoch和step不是数值指标，不应该被添加
        assert "epoch" not in metric_names
        assert "step" not in metric_names


class TestBacktestTaskExecution:
    """回测任务执行测试"""
    
    @pytest.fixture
    def mock_backtest_session(self):
        """模拟回测会话"""
        session = Mock(spec=StrategySession)
        session.id = 456
        session.strategy_id = 2
        session.user_id = 1
        session.status = SessionStatus.PENDING
        session.session_type = "backtest"
        session.trademaster_config = {
            "mode": "backtest",
            "start_date": "2023-01-01",
            "end_date": "2023-12-31",
            "initial_capital": 100000
        }
        return session
    
    @patch('app.tasks.backtest_tasks._get_session')
    @patch('app.tasks.backtest_tasks._update_session_status')
    @patch('app.tasks.backtest_tasks._execute_backtest')
    @patch('app.tasks.backtest_tasks._update_session_final_status')
    def test_execute_backtest_task_success(
        self,
        mock_update_final, mock_execute, mock_update_status, mock_get_session,
        mock_backtest_session
    ):
        """测试回测任务成功执行"""
        mock_get_session.return_value = mock_backtest_session
        mock_execute.return_value = {
            "success": True,
            "results": {
                "total_return": 0.15,
                "sharpe_ratio": 1.25,
                "max_drawdown": 0.08
            }
        }
        
        result = execute_backtest_task(session_id=456)
        
        # 验证执行流程
        mock_get_session.assert_called_once()
        mock_update_status.assert_called_with(456, SessionStatus.RUNNING)
        mock_execute.assert_called_once_with(mock_backtest_session)
        mock_update_final.assert_called_once()
        
        # 验证返回结果
        assert result["success"] is True
        assert "results" in result
        assert result["results"]["total_return"] == 0.15
    
    def test_execute_backtest(self, mock_backtest_session):
        """测试回测执行逻辑"""
        from app.tasks.backtest_tasks import _execute_backtest
        
        with patch('app.tasks.backtest_tasks._run_backtest_analysis') as mock_analysis:
            mock_analysis.return_value = {
                "total_return": 0.12,
                "volatility": 0.18,
                "sharpe_ratio": 0.67
            }
            
            result = _execute_backtest(mock_backtest_session)
            
            assert result["success"] is True
            assert "results" in result
            assert result["results"]["total_return"] == 0.12


class TestTaskResourceManagement:
    """任务资源管理测试"""
    
    def test_process_cleanup_on_cancellation(self):
        """测试任务取消时的进程清理"""
        from app.tasks.training_tasks import _monitor_training_process
        
        mock_process = Mock()
        mock_process.stdout.readline.side_effect = KeyboardInterrupt("任务被取消")
        mock_process.kill = Mock()
        
        with patch('app.tasks.training_tasks.RealTimeDataPusher'):
            result = _monitor_training_process(mock_process, session_id=123)
            
            # 验证进程被杀死
            mock_process.kill.assert_called_once()
            
            # 验证返回失败结果
            assert result["success"] is False
            assert "error" in result
    
    def test_temporary_file_cleanup(self, mock_session):
        """测试临时文件清理"""
        from app.tasks.training_tasks import _create_trademaster_config
        
        with patch('tempfile.mkdtemp') as mock_mkdtemp:
            with patch('pathlib.Path.mkdir') as mock_mkdir:
                with patch('builtins.open', create=True):
                    with patch('yaml.dump'):
                        mock_mkdtemp.return_value = "/tmp/test_dir"
                        
                        config_path = _create_trademaster_config(mock_session)
                        
                        # 验证临时目录创建
                        assert "/tmp/trademaster_configs" in config_path or "/tmp/test_dir" in config_path
    
    @patch('psutil.Process')
    def test_resource_monitoring(self, mock_process):
        """测试资源使用监控"""
        # 模拟psutil进程
        mock_proc = Mock()
        mock_proc.cpu_percent.return_value = 75.5
        mock_proc.memory_info.return_value = Mock(rss=1024*1024*512)  # 512MB
        mock_process.return_value = mock_proc
        
        from app.tasks.monitoring_tasks import monitor_training_resources
        
        with patch('app.tasks.monitoring_tasks._save_resource_usage') as mock_save:
            monitor_training_resources(session_id=123, process_id=12345)
            
            # 验证资源数据保存
            mock_save.assert_called()
            args = mock_save.call_args[1]
            assert args["session_id"] == 123
            assert args["cpu_percent"] == 75.5
            assert args["memory_mb"] >= 512


class TestTaskErrorHandling:
    """任务错误处理测试"""
    
    @patch('app.tasks.training_tasks._get_session')
    def test_database_connection_error(self, mock_get_session):
        """测试数据库连接错误处理"""
        from sqlalchemy.exc import OperationalError
        
        mock_get_session.side_effect = OperationalError("connection failed", None, None)
        
        with pytest.raises(Exception):
            execute_training_task(session_id=123)
    
    def test_process_timeout_handling(self):
        """测试进程超时处理"""
        from app.tasks.training_tasks import _monitor_training_process
        
        mock_process = Mock()
        mock_process.stdout.readline.return_value = ""
        mock_process.poll.return_value = None  # 进程仍在运行
        mock_process.wait.side_effect = subprocess.TimeoutExpired("timeout", timeout=3600)
        mock_process.kill = Mock()
        
        with patch('app.tasks.training_tasks.RealTimeDataPusher'):
            result = _monitor_training_process(mock_process, session_id=123)
            
            # 验证超时时进程被杀死
            mock_process.kill.assert_called_once()
            assert result["success"] is False
    
    def test_invalid_config_error(self, mock_session):
        """测试无效配置错误处理"""
        from app.tasks.training_tasks import _create_trademaster_config
        
        # 设置无效配置
        mock_session.trademaster_config = None
        
        with pytest.raises(Exception):
            _create_trademaster_config(mock_session)


class TestTaskPerformance:
    """任务性能测试"""
    
    def test_large_log_processing_performance(self):
        """测试大量日志处理性能"""
        from app.tasks.training_tasks import _parse_training_output
        
        # 生成大量测试日志
        test_logs = [
            f"Epoch: {i}, Loss: {0.5 - i*0.01:.3f}, Reward: {10 + i*0.5:.2f}"
            for i in range(1000)
        ]
        
        import time
        start_time = time.time()
        
        results = []
        for log in test_logs:
            result = _parse_training_output(log)
            if result:
                results.append(result)
        
        end_time = time.time()
        duration = end_time - start_time
        
        # 验证性能指标
        assert duration < 1.0  # 1000条日志解析应该在1秒内完成
        assert len(results) == 1000  # 所有日志都应该被成功解析
    
    @pytest.mark.asyncio
    async def test_metric_batch_save_performance(self):
        """测试指标批量保存性能"""
        from app.tasks.training_tasks import _save_performance_metrics
        
        with patch('app.tasks.training_tasks.get_database') as mock_get_db:
            mock_db = AsyncMock()
            mock_get_db.return_value.__aenter__.return_value = mock_db
            
            # 模拟批量指标数据
            metrics_batch = {
                f"metric_{i}": float(i) for i in range(100)
            }
            metrics_batch["epoch"] = 50
            
            start_time = asyncio.get_event_loop().time()
            await _save_performance_metrics(session_id=123, metrics=metrics_batch)
            end_time = asyncio.get_event_loop().time()
            
            duration = end_time - start_time
            
            # 验证性能指标
            assert duration < 0.5  # 100个指标保存应该在0.5秒内完成
            assert mock_db.add.call_count == 100  # 所有指标都被添加
            mock_db.commit.assert_called_once()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])