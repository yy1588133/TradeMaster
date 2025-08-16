"""Add API keys and usage logs tables

Revision ID: 002_add_api_keys
Revises: 001_initial_migration
Create Date: 2025-08-15 14:34:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '002_add_api_keys'
down_revision = '001_initial_migration'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add 'analyst' role to UserRole enum
    op.execute("ALTER TYPE userrole ADD VALUE 'analyst'")
    
    # Create api_keys table
    op.create_table('api_keys',
        sa.Column('id', sa.Integer(), nullable=False, comment='API密钥ID'),
        sa.Column('name', sa.String(length=100), nullable=False, comment='密钥名称'),
        sa.Column('key_hash', sa.String(length=64), nullable=False, comment='密钥哈希值'),
        sa.Column('key_prefix', sa.String(length=10), nullable=False, comment='密钥前缀（用于显示）'),
        sa.Column('user_id', sa.Integer(), nullable=False, comment='用户ID'),
        sa.Column('permissions', sa.Text(), nullable=True, comment='权限列表（JSON格式）'),
        sa.Column('ip_whitelist', sa.Text(), nullable=True, comment='IP白名单（JSON格式）'),
        sa.Column('rate_limit', sa.Integer(), nullable=True, comment='每小时请求限制'),
        sa.Column('usage_count', sa.Integer(), nullable=True, comment='总使用次数'),
        sa.Column('last_used_at', sa.DateTime(), nullable=True, comment='最后使用时间'),
        sa.Column('is_active', sa.Boolean(), nullable=True, comment='是否激活'),
        sa.Column('expires_at', sa.DateTime(), nullable=True, comment='过期时间'),
        sa.Column('created_at', sa.DateTime(), nullable=True, comment='创建时间'),
        sa.Column('updated_at', sa.DateTime(), nullable=True, comment='更新时间'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('key_hash'),
        comment='API密钥表'
    )
    
    # Create indexes for api_keys table
    op.create_index('idx_api_keys_user_id', 'api_keys', ['user_id'])
    op.create_index('idx_api_keys_key_hash', 'api_keys', ['key_hash'])
    op.create_index('idx_api_keys_active', 'api_keys', ['is_active'])
    op.create_index('idx_api_keys_expires', 'api_keys', ['expires_at'])

    # Set default values for api_keys table
    op.alter_column('api_keys', 'rate_limit', server_default='1000')
    op.alter_column('api_keys', 'usage_count', server_default='0')
    op.alter_column('api_keys', 'is_active', server_default='true')
    op.alter_column('api_keys', 'created_at', server_default=sa.text('now()'))
    op.alter_column('api_keys', 'updated_at', server_default=sa.text('now()'))

    # Create api_key_usage_logs table
    op.create_table('api_key_usage_logs',
        sa.Column('id', sa.Integer(), nullable=False, comment='使用日志ID'),
        sa.Column('api_key_id', sa.Integer(), nullable=False, comment='API密钥ID'),
        sa.Column('user_id', sa.Integer(), nullable=False, comment='用户ID'),
        sa.Column('endpoint', sa.String(length=200), nullable=True, comment='请求端点'),
        sa.Column('method', sa.String(length=10), nullable=True, comment='请求方法'),
        sa.Column('ip_address', sa.String(length=45), nullable=True, comment='客户端IP地址'),
        sa.Column('user_agent', sa.Text(), nullable=True, comment='用户代理'),
        sa.Column('status_code', sa.Integer(), nullable=True, comment='响应状态码'),
        sa.Column('response_time', sa.Integer(), nullable=True, comment='响应时间（毫秒）'),
        sa.Column('created_at', sa.DateTime(), nullable=True, comment='创建时间'),
        sa.ForeignKeyConstraint(['api_key_id'], ['api_keys.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id'),
        comment='API密钥使用日志表'
    )
    
    # Create indexes for api_key_usage_logs table
    op.create_index('idx_api_key_logs_key_id', 'api_key_usage_logs', ['api_key_id'])
    op.create_index('idx_api_key_logs_user_id', 'api_key_usage_logs', ['user_id'])
    op.create_index('idx_api_key_logs_created_at', 'api_key_usage_logs', ['created_at'])
    op.create_index('idx_api_key_logs_endpoint', 'api_key_usage_logs', ['endpoint'])

    # Set default values for api_key_usage_logs table
    op.alter_column('api_key_usage_logs', 'created_at', server_default=sa.text('now()'))


def downgrade() -> None:
    # Drop api_key_usage_logs table
    op.drop_index('idx_api_key_logs_endpoint', table_name='api_key_usage_logs')
    op.drop_index('idx_api_key_logs_created_at', table_name='api_key_usage_logs')
    op.drop_index('idx_api_key_logs_user_id', table_name='api_key_usage_logs')
    op.drop_index('idx_api_key_logs_key_id', table_name='api_key_usage_logs')
    op.drop_table('api_key_usage_logs')
    
    # Drop api_keys table
    op.drop_index('idx_api_keys_expires', table_name='api_keys')
    op.drop_index('idx_api_keys_active', table_name='api_keys')
    op.drop_index('idx_api_keys_key_hash', table_name='api_keys')
    op.drop_index('idx_api_keys_user_id', table_name='api_keys')
    op.drop_table('api_keys')
    
    # Note: Cannot remove 'analyst' from enum in PostgreSQL without recreating the enum
    # This would require more complex migration logic
    pass