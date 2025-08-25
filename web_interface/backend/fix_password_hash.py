"""
修复密码哈希兼容性的脚本
使用bcrypt来生成与后端兼容的密码哈希
"""
import sqlite3
import bcrypt
import uuid as uuid_module
from datetime import datetime

def get_bcrypt_hash(password: str) -> str:
    """使用bcrypt生成密码哈希"""
    # 生成salt并哈希密码
    salt = bcrypt.gensalt(rounds=12)
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed.decode('utf-8')

def fix_user_passwords():
    """修复用户密码哈希格式"""
    db_path = "trademaster_web.db"
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        print("TradeMaster Password Hash Fix Tool")
        print("="*50)
        
        # 检查现有用户
        cursor.execute("SELECT id, username, hashed_password FROM users")
        users = cursor.fetchall()
        
        if not users:
            print("No users found in database.")
            return
            
        print(f"Found {len(users)} users to fix:")
        
        for user_id, username, current_hash in users:
            print(f"  Fixing user: {username}")
            
            # 根据用户名确定密码
            if username == "admin":
                new_password = "admin123"
            elif username == "demo":
                new_password = "demo123"
            else:
                continue  # 跳过其他用户
            
            # 生成bcrypt哈希
            new_hash = get_bcrypt_hash(new_password)
            
            # 更新数据库
            cursor.execute(
                "UPDATE users SET hashed_password = ? WHERE id = ?",
                (new_hash, user_id)
            )
            
            print(f"    Updated password hash for {username}")
        
        conn.commit()
        print("\nPassword hash fix completed!")
        print("="*50)
        print("Test credentials:")
        print("  Admin - Username: admin, Password: admin123")
        print("  Demo - Username: demo, Password: demo123")
        
    except Exception as e:
        print(f"Error: {e}")
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    fix_user_passwords()