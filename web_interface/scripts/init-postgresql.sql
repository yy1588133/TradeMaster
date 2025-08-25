-- TradeMaster PostgreSQL 数据库初始化脚本
-- 创建数据库、用户和基础配置

-- 设置字符编码
SET client_encoding = 'UTF8';

-- 创建扩展（如果需要）
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_stat_statements";

-- 创建数据库（如果不存在）
-- 注意：在docker-entrypoint-initdb.d中，数据库已经通过环境变量创建

-- 确认当前数据库和用户
\echo '==========================================';
\echo '  TradeMaster PostgreSQL 初始化脚本';
\echo '==========================================';

\echo '当前数据库信息:';
SELECT current_database() as database_name;
SELECT current_user as current_user;

-- 设置数据库配置
\echo '配置数据库参数...';

-- 设置时区
SET timezone = 'Asia/Shanghai';

-- 创建必要的schema（如果需要）
-- CREATE SCHEMA IF NOT EXISTS trademaster;

-- 设置搜索路径
-- SET search_path TO trademaster, public;

-- 创建一些基础表结构（示例）
\echo '创建基础表结构...';

-- 用户表示例（如果后端需要）
-- CREATE TABLE IF NOT EXISTS users (
--     id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
--     username VARCHAR(255) UNIQUE NOT NULL,
--     email VARCHAR(255) UNIQUE NOT NULL,
--     password_hash TEXT NOT NULL,
--     is_active BOOLEAN DEFAULT true,
--     is_superuser BOOLEAN DEFAULT false,
--     created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
--     updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
-- );

-- 会话表示例
-- CREATE TABLE IF NOT EXISTS user_sessions (
--     id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
--     user_id UUID REFERENCES users(id) ON DELETE CASCADE,
--     session_token TEXT UNIQUE NOT NULL,
--     expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
--     created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
-- );

-- 创建索引
\echo '创建索引...';

-- CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);
-- CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
-- CREATE INDEX IF NOT EXISTS idx_sessions_token ON user_sessions(session_token);
-- CREATE INDEX IF NOT EXISTS idx_sessions_user_id ON user_sessions(user_id);

-- 设置数据库权限
\echo '配置数据库权限...';

-- 确保trademaster用户有所有必要权限
GRANT ALL PRIVILEGES ON DATABASE trademaster_web TO trademaster;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO trademaster;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO trademaster;
GRANT ALL PRIVILEGES ON ALL FUNCTIONS IN SCHEMA public TO trademaster;

-- 设置默认权限
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO trademaster;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO trademaster;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON FUNCTIONS TO trademaster;

-- 创建数据库维护函数
\echo '创建维护函数...';

-- 数据库统计信息函数
CREATE OR REPLACE FUNCTION get_database_stats() 
RETURNS TABLE (
    table_name TEXT,
    row_count BIGINT,
    size_pretty TEXT
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        schemaname||'.'||tablename as table_name,
        n_tup_ins - n_tup_del as row_count,
        pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size_pretty
    FROM pg_stat_user_tables 
    ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;
END;
$$ LANGUAGE plpgsql;

-- 数据库健康检查函数
CREATE OR REPLACE FUNCTION health_check() 
RETURNS TABLE (
    check_name TEXT,
    status TEXT,
    details TEXT
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        'Database Connection'::TEXT as check_name,
        'OK'::TEXT as status,
        'Connected to ' || current_database() as details
    UNION ALL
    SELECT 
        'Current Time'::TEXT as check_name,
        'OK'::TEXT as status,
        CURRENT_TIMESTAMP::TEXT as details
    UNION ALL
    SELECT 
        'Extensions'::TEXT as check_name,
        'OK'::TEXT as status,
        string_agg(extname, ', ') as details
    FROM pg_extension;
END;
$$ LANGUAGE plpgsql;

-- 完成初始化
\echo '==========================================';
\echo '  PostgreSQL 数据库初始化完成!';
\echo '==========================================';

-- 显示初始化结果
\echo '数据库连接测试:';
SELECT health_check();

\echo '数据库信息:';
SELECT 
    current_database() as database,
    current_user as user,
    inet_server_addr() as server_ip,
    inet_server_port() as server_port,
    version() as postgresql_version;