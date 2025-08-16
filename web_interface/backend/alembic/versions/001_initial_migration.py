"""Initial migration - Create core tables

Revision ID: 001
Revises: 
Create Date: 2025-01-15 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    """升级数据库结构"""
    
    # 创建枚举类型
    op.execute("CREATE TYPE userrole AS ENUM ('admin', 'user', 'viewer', 'analyst')")
    op.execute("CREATE TYPE strategytype AS ENUM ('algorithmic_trading', 'portfolio_management', 'order_execution', 'high_frequency_trading')")
    op.execute("CREATE TYPE strategystatus AS ENUM ('draft', 'active', 'paused', 'stopped', 'error')")
    op.execute("CREATE TYPE datasetstatus AS ENUM ('uploading', 'processing', 'ready', 'error')")
    op.execute("CREATE TYPE trainingstatus AS ENUM ('pending', 'running', 'completed', 'failed', 'cancelled')")
    op.execute("CREATE TYPE evaluationtype AS ENUM ('backtest', 'performance', 'risk', 'comparison')")
    op.execute("CREATE TYPE evaluationstatus AS ENUM ('pending', 'running', 'completed', 'failed')")
    op.execute("CREATE TYPE loglevel AS ENUM ('DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL')")
    op.execute("CREATE TYPE taskstatus AS ENUM ('PENDING', 'STARTED', 'SUCCESS', 'FAILURE', 'RETRY', 'REVOKED')")
    
    # 创建用户表
    op.create_table('users',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('uuid', postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column('username', sa.String(length=50), nullable=False),
        sa.Column('email', sa.String(length=100), nullable=False),
        sa.Column('hashed_password', sa.String(length=255), nullable=False),
        sa.Column('full_name', sa.String(length=100), nullable=True),
        sa.Column('avatar_url', sa.String(length=500), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, default=True),
        sa.Column('is_superuser', sa.Boolean(), nullable=False, default=False),
        sa.Column('is_verified', sa.Boolean(), nullable=False, default=False),
        sa.Column('role', postgresql.ENUM('admin', 'user', 'viewer', name='userrole'), nullable=False, default='user'),
        sa.Column('last_login_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('login_count', sa.Integer(), nullable=False, default=0),
        sa.Column('settings', postgresql.JSONB(astext_type=sa.Text()), nullable=False, default={}),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('username'),
        sa.UniqueConstraint('email'),
        sa.UniqueConstraint('uuid')
    )
    
    # 创建用户会话表
    op.create_table('user_sessions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('session_token', sa.String(length=255), nullable=False),
        sa.Column('refresh_token', sa.String(length=255), nullable=True),
        sa.Column('ip_address', postgresql.INET(), nullable=True),
        sa.Column('user_agent', sa.Text(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, default=True),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('last_activity_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('session_token'),
        sa.UniqueConstraint('refresh_token')
    )
    
    # 创建策略表
    op.create_table('strategies',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('uuid', postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('strategy_type', postgresql.ENUM('algorithmic_trading', 'portfolio_management', 'order_execution', 'high_frequency_trading', name='strategytype'), nullable=False),
        sa.Column('status', postgresql.ENUM('draft', 'active', 'paused', 'stopped', 'error', name='strategystatus'), nullable=False, default='draft'),
        sa.Column('version', sa.String(length=20), nullable=False, default='1.0.0'),
        sa.Column('config', postgresql.JSONB(astext_type=sa.Text()), nullable=False, default={}),
        sa.Column('parameters', postgresql.JSONB(astext_type=sa.Text()), nullable=False, default={}),
        sa.Column('total_return', sa.Numeric(precision=10, scale=4), nullable=True),
        sa.Column('sharpe_ratio', sa.Numeric(precision=8, scale=4), nullable=True),
        sa.Column('max_drawdown', sa.Numeric(precision=8, scale=4), nullable=True),
        sa.Column('win_rate', sa.Numeric(precision=5, scale=2), nullable=True),
        sa.Column('owner_id', sa.Integer(), nullable=False),
        sa.Column('parent_strategy_id', sa.Integer(), nullable=True),
        sa.Column('tags', postgresql.ARRAY(sa.String()), nullable=False, default=[]),
        sa.Column('category', sa.String(length=50), nullable=True),
        sa.Column('last_run_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.CheckConstraint('total_return >= -100 AND total_return <= 1000', name='valid_return_range'),
        sa.CheckConstraint('sharpe_ratio >= -10 AND sharpe_ratio <= 10', name='valid_sharpe_ratio'),
        sa.ForeignKeyConstraint(['owner_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['parent_strategy_id'], ['strategies.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('uuid')
    )
    
    # 创建策略版本表
    op.create_table('strategy_versions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('strategy_id', sa.Integer(), nullable=False),
        sa.Column('version', sa.String(length=20), nullable=False),
        sa.Column('config', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('parameters', postgresql.JSONB(astext_type=sa.Text()), nullable=False, default={}),
        sa.Column('changelog', sa.Text(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, default=False),
        sa.Column('created_by', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['strategy_id'], ['strategies.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['created_by'], ['users.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('strategy_id', 'version', name='uq_strategy_version')
    )
    
    # 创建数据集表
    op.create_table('datasets',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('uuid', postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('file_path', sa.String(length=500), nullable=False),
        sa.Column('file_size', sa.BigInteger(), nullable=True),
        sa.Column('file_type', sa.String(length=20), nullable=True),
        sa.Column('row_count', sa.Integer(), nullable=True),
        sa.Column('column_count', sa.Integer(), nullable=True),
        sa.Column('columns', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('status', postgresql.ENUM('uploading', 'processing', 'ready', 'error', name='datasetstatus'), nullable=False, default='uploading'),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('statistics', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('sample_data', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('owner_id', sa.Integer(), nullable=False),
        sa.Column('processed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['owner_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('uuid')
    )
    
    # 创建训练任务表
    op.create_table('training_jobs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('uuid', postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('status', postgresql.ENUM('pending', 'running', 'completed', 'failed', 'cancelled', name='trainingstatus'), nullable=False, default='pending'),
        sa.Column('progress', sa.Numeric(precision=5, scale=2), nullable=False, default=0.0),
        sa.Column('current_epoch', sa.Integer(), nullable=False, default=0),
        sa.Column('total_epochs', sa.Integer(), nullable=True),
        sa.Column('config', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('hyperparameters', postgresql.JSONB(astext_type=sa.Text()), nullable=False, default={}),
        sa.Column('metrics', postgresql.JSONB(astext_type=sa.Text()), nullable=False, default={}),
        sa.Column('best_metrics', postgresql.JSONB(astext_type=sa.Text()), nullable=False, default={}),
        sa.Column('model_path', sa.String(length=500), nullable=True),
        sa.Column('logs', sa.Text(), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('trademaster_session_id', sa.String(length=100), nullable=True),
        sa.Column('strategy_id', sa.Integer(), nullable=False),
        sa.Column('dataset_id', sa.Integer(), nullable=True),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('parent_job_id', sa.Integer(), nullable=True),
        sa.Column('estimated_duration', sa.Integer(), nullable=True),
        sa.Column('actual_duration', sa.Integer(), nullable=True),
        sa.Column('cpu_usage', sa.Numeric(precision=5, scale=2), nullable=True),
        sa.Column('memory_usage', sa.Numeric(precision=5, scale=2), nullable=True),
        sa.Column('gpu_usage', sa.Numeric(precision=5, scale=2), nullable=True),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.CheckConstraint('progress >= 0 AND progress <= 100', name='valid_progress_range'),
        sa.ForeignKeyConstraint(['strategy_id'], ['strategies.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['dataset_id'], ['datasets.id']),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['parent_job_id'], ['training_jobs.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('uuid')
    )
    
    # 创建训练指标历史表
    op.create_table('training_metrics',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('training_job_id', sa.Integer(), nullable=False),
        sa.Column('epoch', sa.Integer(), nullable=False),
        sa.Column('step', sa.Integer(), nullable=True),
        sa.Column('metrics', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('recorded_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['training_job_id'], ['training_jobs.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    
    # 创建评估表
    op.create_table('evaluations',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('uuid', postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('evaluation_type', postgresql.ENUM('backtest', 'performance', 'risk', 'comparison', name='evaluationtype'), nullable=False),
        sa.Column('status', postgresql.ENUM('pending', 'running', 'completed', 'failed', name='evaluationstatus'), nullable=False, default='pending'),
        sa.Column('config', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('time_range', postgresql.TSRANGE(), nullable=True),
        sa.Column('results', postgresql.JSONB(astext_type=sa.Text()), nullable=False, default={}),
        sa.Column('report_path', sa.String(length=500), nullable=True),
        sa.Column('charts', postgresql.JSONB(astext_type=sa.Text()), nullable=False, default=[]),
        sa.Column('strategy_id', sa.Integer(), nullable=False),
        sa.Column('dataset_id', sa.Integer(), nullable=True),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['strategy_id'], ['strategies.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['dataset_id'], ['datasets.id']),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('uuid')
    )
    
    # 创建系统日志表
    op.create_table('system_logs',
        sa.Column('id', sa.BigInteger(), nullable=False),
        sa.Column('level', postgresql.ENUM('DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL', name='loglevel'), nullable=False),
        sa.Column('message', sa.Text(), nullable=False),
        sa.Column('module', sa.String(length=100), nullable=True),
        sa.Column('function_name', sa.String(length=100), nullable=True),
        sa.Column('user_id', sa.Integer(), nullable=True),
        sa.Column('session_id', sa.String(length=255), nullable=True),
        sa.Column('request_id', sa.String(length=100), nullable=True),
        sa.Column('metadata', postgresql.JSONB(astext_type=sa.Text()), nullable=False, default={}),
        sa.Column('stack_trace', sa.Text(), nullable=True),
        sa.Column('ip_address', postgresql.INET(), nullable=True),
        sa.Column('user_agent', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
        sa.PrimaryKeyConstraint('id')
    )
    
    # 创建Celery任务表
    op.create_table('celery_tasks',
        sa.Column('id', sa.String(length=155), nullable=False),
        sa.Column('task_name', sa.String(length=255), nullable=False),
        sa.Column('status', postgresql.ENUM('PENDING', 'STARTED', 'SUCCESS', 'FAILURE', 'RETRY', 'REVOKED', name='taskstatus'), nullable=False, default='PENDING'),
        sa.Column('args', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('kwargs', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('result', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('worker_name', sa.String(length=100), nullable=True),
        sa.Column('retries', sa.Integer(), nullable=False, default=0),
        sa.Column('max_retries', sa.Integer(), nullable=False, default=3),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('user_id', sa.Integer(), nullable=True),
        sa.Column('related_id', sa.Integer(), nullable=True),
        sa.Column('related_type', sa.String(length=50), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
        sa.PrimaryKeyConstraint('id')
    )
    
    # 创建索引
    op.create_index('idx_users_username', 'users', ['username'])
    op.create_index('idx_users_email', 'users', ['email'])
    op.create_index('idx_users_active', 'users', ['is_active'])
    op.create_index('idx_users_created_at', 'users', ['created_at'])
    
    op.create_index('idx_sessions_user_id', 'user_sessions', ['user_id'])
    op.create_index('idx_sessions_token', 'user_sessions', ['session_token'])
    op.create_index('idx_sessions_expires', 'user_sessions', ['expires_at'])
    
    op.create_index('idx_strategies_owner', 'strategies', ['owner_id'])
    op.create_index('idx_strategies_type', 'strategies', ['strategy_type'])
    op.create_index('idx_strategies_status', 'strategies', ['status'])
    op.create_index('idx_strategies_created', 'strategies', ['created_at'])
    op.create_index('idx_strategies_tags', 'strategies', ['tags'], postgresql_using='gin')
    op.create_index('idx_strategies_config', 'strategies', ['config'], postgresql_using='gin')
    
    op.create_index('idx_strategy_versions_strategy', 'strategy_versions', ['strategy_id'])
    op.create_index('idx_strategy_versions_active', 'strategy_versions', ['strategy_id', 'is_active'])
    
    op.create_index('idx_datasets_owner', 'datasets', ['owner_id'])
    op.create_index('idx_datasets_status', 'datasets', ['status'])
    op.create_index('idx_datasets_created', 'datasets', ['created_at'])
    op.create_index('idx_datasets_columns', 'datasets', ['columns'], postgresql_using='gin')
    
    op.create_index('idx_training_jobs_user', 'training_jobs', ['user_id'])
    op.create_index('idx_training_jobs_strategy', 'training_jobs', ['strategy_id'])
    op.create_index('idx_training_jobs_dataset', 'training_jobs', ['dataset_id'])
    op.create_index('idx_training_jobs_status', 'training_jobs', ['status'])
    op.create_index('idx_training_jobs_created', 'training_jobs', ['created_at'])
    op.create_index('idx_training_jobs_session', 'training_jobs', ['trademaster_session_id'])
    
    op.create_index('idx_training_metrics_job', 'training_metrics', ['training_job_id'])
    op.create_index('idx_training_metrics_epoch', 'training_metrics', ['training_job_id', 'epoch'])
    
    op.create_index('idx_evaluations_user', 'evaluations', ['user_id'])
    op.create_index('idx_evaluations_strategy', 'evaluations', ['strategy_id'])
    op.create_index('idx_evaluations_dataset', 'evaluations', ['dataset_id'])
    op.create_index('idx_evaluations_type', 'evaluations', ['evaluation_type'])
    op.create_index('idx_evaluations_status', 'evaluations', ['status'])
    
    op.create_index('idx_system_logs_level', 'system_logs', ['level'])
    op.create_index('idx_system_logs_user', 'system_logs', ['user_id'])
    op.create_index('idx_system_logs_created', 'system_logs', ['created_at'])
    op.create_index('idx_system_logs_module', 'system_logs', ['module'])
    
    op.create_index('idx_celery_tasks_status', 'celery_tasks', ['status'])
    op.create_index('idx_celery_tasks_user', 'celery_tasks', ['user_id'])
    op.create_index('idx_celery_tasks_created', 'celery_tasks', ['created_at'])
    op.create_index('idx_celery_tasks_related', 'celery_tasks', ['related_type', 'related_id'])
    
    # 创建更新触发器函数
    op.execute("""
        CREATE OR REPLACE FUNCTION update_updated_at_column()
        RETURNS TRIGGER AS $$
        BEGIN
            NEW.updated_at = CURRENT_TIMESTAMP;
            RETURN NEW;
        END;
        $$ language 'plpgsql';
    """)
    
    # 为需要的表创建更新触发器
    for table in ['users', 'user_sessions', 'strategies', 'strategy_versions', 'datasets', 
                  'training_jobs', 'evaluations', 'celery_tasks']:
        op.execute(f"""
            CREATE TRIGGER update_{table}_updated_at 
            BEFORE UPDATE ON {table} 
            FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
        """)


def downgrade() -> None:
    """回滚数据库结构"""
    
    # 删除触发器
    for table in ['users', 'user_sessions', 'strategies', 'strategy_versions', 'datasets', 
                  'training_jobs', 'evaluations', 'celery_tasks']:
        op.execute(f"DROP TRIGGER IF EXISTS update_{table}_updated_at ON {table};")
    
    # 删除触发器函数
    op.execute("DROP FUNCTION IF EXISTS update_updated_at_column();")
    
    # 删除表 (按依赖关系逆序)
    op.drop_table('celery_tasks')
    op.drop_table('system_logs')
    op.drop_table('evaluations')
    op.drop_table('training_metrics')
    op.drop_table('training_jobs')
    op.drop_table('datasets')
    op.drop_table('strategy_versions')
    op.drop_table('strategies')
    op.drop_table('user_sessions')
    op.drop_table('users')
    
    # 删除枚举类型
    op.execute("DROP TYPE IF EXISTS taskstatus;")
    op.execute("DROP TYPE IF EXISTS loglevel;")
    op.execute("DROP TYPE IF EXISTS evaluationstatus;")
    op.execute("DROP TYPE IF EXISTS evaluationtype;")
    op.execute("DROP TYPE IF EXISTS trainingstatus;")
    op.execute("DROP TYPE IF EXISTS datasetstatus;")
    op.execute("DROP TYPE IF EXISTS strategystatus;")
    op.execute("DROP TYPE IF EXISTS strategytype;")
    op.execute("DROP TYPE IF EXISTS userrole;")