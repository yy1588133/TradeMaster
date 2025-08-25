"""
简单的数据库检查和用户创建脚本
"""
import sqlite3
import hashlib
import secrets
import uuid as uuid_module
from datetime import datetime

def get_password_hash(password: str) -> str:
    """简单的密码哈希函数"""
    # 生成盐值
    salt = secrets.token_hex(16)
    # 创建哈希
    pwd_hash = hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), 100000)
    return f"{salt}${pwd_hash.hex()}"

def check_and_create_users():
    """检查并创建默认用户"""
    db_path = "trademaster_web.db"
    
    try:
        # 连接数据库
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        print("Check database connection...")
        print(f"   Database file: {db_path}")
        
        # 检查用户表是否存在
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='users'
        """)
        table_exists = cursor.fetchone() is not None
        print(f"   Users table exists: {'Yes' if table_exists else 'No'}")
        
        if not table_exists:
            print("ERROR: Users table does not exist. Please run backend service to initialize database.")
            return
        
        # 检查现有用户
        cursor.execute("SELECT username, email, role, is_active FROM users")
        existing_users = cursor.fetchall()
        print(f"Existing users count: {len(existing_users)}")
        
        for user in existing_users:
            username, email, role, is_active = user
            status = "Active" if is_active else "Inactive"
            print(f"   - {username} ({email}) - {role} - {status}")
        
        # 如果没有用户，创建默认用户
        if len(existing_users) == 0:
            print("\nCreating default users...")
            
            # 创建管理员用户
            admin_data = (
                str(uuid_module.uuid4()),  # uuid
                "admin",  # username
                "admin@trademaster.com",  # email
                get_password_hash("admin123"),  # hashed_password
                "系统管理员",  # full_name
                True,  # is_active
                False,  # is_superuser
                True,  # is_verified
                "admin",  # role
                datetime.now().isoformat(),  # created_at
                None,  # last_login_at
                0,  # login_count
                "{}",  # settings (JSON)
                None,  # avatar_url
            )
            
            cursor.execute("""
                INSERT INTO users (
                    uuid, username, email, hashed_password, full_name,
                    is_active, is_superuser, is_verified, role, created_at,
                    last_login_at, login_count, settings, avatar_url
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, admin_data)
            
            # 创建演示用户
            demo_data = (
                str(uuid_module.uuid4()),  # uuid
                "demo",  # username
                "demo@trademaster.com",  # email
                get_password_hash("demo123"),  # hashed_password
                "演示用户",  # full_name
                True,  # is_active
                False,  # is_superuser
                True,  # is_verified
                "user",  # role
                datetime.now().isoformat(),  # created_at
                None,  # last_login_at
                0,  # login_count
                "{}",  # settings (JSON)
                None,  # avatar_url
            )
            
            cursor.execute("""
                INSERT INTO users (
                    uuid, username, email, hashed_password, full_name,
                    is_active, is_superuser, is_verified, role, created_at,
                    last_login_at, login_count, settings, avatar_url
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, demo_data)
            
            conn.commit()
            print("   Success: Admin user created - admin / admin123")
            print("   Success: Demo user created - demo / demo123")
        else:
            print("\nWarning: Users already exist, no need to create")
        
        print("\nDatabase check completed!")
        print("="*50)
        print("Available login credentials:")
        print("   Admin - Username: admin, Password: admin123")
        print("   Demo User - Username: demo, Password: demo123")
        print("WARNING: Please change default passwords in production!")
        
    except sqlite3.Error as e:
        print(f"Database error: {e}")
    except Exception as e:
        print(f"Unknown error: {e}")
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    print("TradeMaster Database Check Tool")
    print("="*50)
    check_and_create_users()