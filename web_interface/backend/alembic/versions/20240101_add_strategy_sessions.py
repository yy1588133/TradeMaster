"""Add strategy sessions and metrics tables

Revision ID: add_strategy_sessions
Revises: 
Create Date: 2024-01-01 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'add_strategy_sessions'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add strategy sessions and metrics tables"""
    
    # Create strategy_sessions table
    op.create_table('strategy_sessions',
        sa.Column('id', sa.Integer(), nullable=False, comment='会话ID'),
        sa.Column('uuid', sa.String(36), nullable=False, comment='全局唯一标识符'),
        sa.Column('session_type', sa.Enum('training', 'backtest', 'live_trading', name='sessiontype'), 
                  nullable=False, comment='会话类型'),
        sa.Column('status', sa.Enum('pending', 'running', 'completed', 'failed', 'cancelled', name='sessionstatus'), 
                  nullable=False, comment='会话状态'),
        
        # 关联信息
        sa.Column('strategy_id', sa.Integer(), nullable=False, comment='策略ID'),
        sa.Column('user_id', sa.Integer(), nullable=False, comment='用户ID'),
        
        # TradeMaster集成
        sa.Column('trademaster_config', postgresql.JSONB(astext_type=sa.Text()), 
                  nullable=False, comment='TradeMaster配置'),
        sa.Column('trademaster_session_id', sa.String(100), nullable=True, comment='TradeMaster会话ID'),
        sa.Column('celery_task_id', sa.String(155), nullable=True, comment='Celery任务ID'),
        
        # 执行进度
        sa.Column('progress', sa.Numeric(precision=5, scale=2), nullable=False, comment='进度百分比'),
        sa.Column('current_epoch', sa.Integer(), nullable=False, comment='当前轮次'),
        sa.Column('total_epochs', sa.Integer(), nullable=True, comment='总轮次'),
        
        # 结果数据
        sa.Column('final_metrics', postgresql.JSONB(astext_type=sa.Text()), 
                  nullable=False, comment='最终指标'),
        sa.Column('model_path', sa.String(500), nullable=True, comment='模型文件路径'),
        sa.Column('log_file_path', sa.String(500), nullable=True, comment='日志文件路径'),
        sa.Column('error_message', sa.Text(), nullable=True, comment='错误信息'),
        
        # 时间戳
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=True, comment='开始时间'),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True, comment='完成时间'),
        sa.Column('created_at', sa.DateTime(timezone=True), 
                  server_default=sa.text('now()'), nullable=False, comment='创建时间'),
        sa.Column('updated_at', sa.DateTime(timezone=True), 
                  server_default=sa.text('now()'), nullable=False, comment='更新时间'),
        
        # 约束
        sa.CheckConstraint('progress >= 0 AND progress <= 100', name='valid_session_progress'),
        sa.ForeignKeyConstraint(['strategy_id'], ['strategies.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('uuid'),
        comment='策略执行会话表'
    )
    
    # Create performance_metrics table
    op.create_table('performance_metrics',
        sa.Column('id', sa.Integer(), nullable=False, comment='指标ID'),
        sa.Column('session_id', sa.Integer(), nullable=False, comment='会话ID'),
        
        # 指标信息
        sa.Column('metric_name', sa.String(50), nullable=False, comment='指标名称'),
        sa.Column('metric_value', sa.Numeric(precision=15, scale=8), nullable=False, comment='指标值'),
        sa.Column('epoch', sa.Integer(), nullable=True, comment='轮次'),
        sa.Column('step', sa.Integer(), nullable=True, comment='步数'),
        
        # 元数据
        sa.Column('metric_metadata', postgresql.JSONB(astext_type=sa.Text()), 
                  nullable=False, comment='元数据'),
        sa.Column('recorded_at', sa.DateTime(timezone=True), 
                  server_default=sa.text('now()'), nullable=False, comment='记录时间'),
        
        # 约束
        sa.ForeignKeyConstraint(['session_id'], ['strategy_sessions.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        comment='性能指标表'
    )
    
    # Create resource_usage table
    op.create_table('resource_usage',
        sa.Column('id', sa.Integer(), nullable=False, comment='记录ID'),
        sa.Column('session_id', sa.Integer(), nullable=False, comment='会话ID'),
        
        # 资源指标
        sa.Column('cpu_percent', sa.Numeric(precision=5, scale=2), nullable=True, comment='CPU使用率(%)'),
        sa.Column('memory_mb', sa.Integer(), nullable=True, comment='内存使用量(MB)'),
        sa.Column('gpu_percent', sa.Numeric(precision=5, scale=2), nullable=True, comment='GPU使用率(%)'),
        sa.Column('gpu_memory_mb', sa.Integer(), nullable=True, comment='GPU内存使用量(MB)'),
        sa.Column('disk_io_mb', sa.Numeric(precision=10, scale=2), nullable=True, comment='磁盘IO(MB)'),
        sa.Column('network_io_mb', sa.Numeric(precision=10, scale=2), nullable=True, comment='网络IO(MB)'),
        
        sa.Column('recorded_at', sa.DateTime(timezone=True), 
                  server_default=sa.text('now()'), nullable=False, comment='记录时间'),
        
        # 约束
        sa.ForeignKeyConstraint(['session_id'], ['strategy_sessions.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        comment='资源使用记录表'
    )
    
    # Create websocket_connections table
    op.create_table('websocket_connections',
        sa.Column('id', sa.Integer(), nullable=False, comment='记录ID'),
        sa.Column('user_id', sa.Integer(), nullable=False, comment='用户ID'),
        sa.Column('connection_id', sa.String(100), nullable=False, comment='连接ID'),
        sa.Column('session_ids', postgresql.ARRAY(sa.Integer()), nullable=False, comment='订阅的会话ID列表'),
        
        # 连接信息
        sa.Column('ip_address', postgresql.INET(), nullable=True, comment='IP地址'),
        sa.Column('user_agent', sa.Text(), nullable=True, comment='用户代理'),
        sa.Column('is_active', sa.Boolean(), nullable=False, comment='是否活跃'),
        
        # 时间信息
        sa.Column('connected_at', sa.DateTime(timezone=True), 
                  server_default=sa.text('now()'), nullable=False, comment='连接时间'),
        sa.Column('last_activity', sa.DateTime(timezone=True), 
                  server_default=sa.text('now()'), nullable=False, comment='最后活动时间'),
        sa.Column('created_at', sa.DateTime(timezone=True), 
                  server_default=sa.text('now()'), nullable=False, comment='创建时间'),
        sa.Column('updated_at', sa.DateTime(timezone=True), 
                  server_default=sa.text('now()'), nullable=False, comment='更新时间'),
        
        # 约束
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('connection_id'),
        comment='WebSocket连接表'
    )
    
    # Create indexes for strategy_sessions
    op.create_index('idx_strategy_sessions_strategy', 'strategy_sessions', ['strategy_id'])
    op.create_index('idx_strategy_sessions_status', 'strategy_sessions', ['status'])
    op.create_index('idx_strategy_sessions_type_status', 'strategy_sessions', ['session_type', 'status'])
    op.create_index('idx_strategy_sessions_user', 'strategy_sessions', ['user_id'])
    op.create_index('idx_strategy_sessions_celery_task', 'strategy_sessions', ['celery_task_id'])
    
    # Create indexes for performance_metrics
    op.create_index('idx_performance_metrics_session', 'performance_metrics', ['session_id'])
    op.create_index('idx_performance_metrics_epoch', 'performance_metrics', ['session_id', 'epoch'])
    op.create_index('idx_performance_metrics_name_time', 'performance_metrics', ['metric_name', 'recorded_at'])
    
    # Create indexes for resource_usage
    op.create_index('idx_resource_usage_session', 'resource_usage', ['session_id'])
    op.create_index('idx_resource_usage_time', 'resource_usage', ['session_id', 'recorded_at'])
    
    # Create indexes for websocket_connections
    op.create_index('idx_websocket_connections_user', 'websocket_connections', ['user_id'])
    op.create_index('idx_websocket_connections_active', 'websocket_connections', ['is_active'])
    op.create_index('idx_websocket_connections_id', 'websocket_connections', ['connection_id'])


def downgrade() -> None:
    """Remove strategy sessions and metrics tables"""
    
    # Drop indexes first
    op.drop_index('idx_websocket_connections_id', 'websocket_connections')
    op.drop_index('idx_websocket_connections_active', 'websocket_connections')
    op.drop_index('idx_websocket_connections_user', 'websocket_connections')
    
    op.drop_index('idx_resource_usage_time', 'resource_usage')
    op.drop_index('idx_resource_usage_session', 'resource_usage')
    
    op.drop_index('idx_performance_metrics_name_time', 'performance_metrics')
    op.drop_index('idx_performance_metrics_epoch', 'performance_metrics')
    op.drop_index('idx_performance_metrics_session', 'performance_metrics')
    
    op.drop_index('idx_strategy_sessions_celery_task', 'strategy_sessions')
    op.drop_index('idx_strategy_sessions_user', 'strategy_sessions')
    op.drop_index('idx_strategy_sessions_type_status', 'strategy_sessions')
    op.drop_index('idx_strategy_sessions_status', 'strategy_sessions')
    op.drop_index('idx_strategy_sessions_strategy', 'strategy_sessions')
    
    # Drop tables
    op.drop_table('websocket_connections')
    op.drop_table('resource_usage')
    op.drop_table('performance_metrics')
    op.drop_table('strategy_sessions')
    
    # Drop enums
    op.execute('DROP TYPE IF EXISTS sessionstatus')
    op.execute('DROP TYPE IF EXISTS sessiontype')