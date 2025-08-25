"""
Fix enum values in database
Update user role values to match enum definitions
"""
import sqlite3

def fix_enum_values():
    """Fix enum values in the database"""
    db_path = "trademaster_web.db"
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        print("TradeMaster Enum Fix Tool")
        print("="*50)
        
        # Check current role values
        cursor.execute("SELECT id, username, role FROM users")
        users = cursor.fetchall()
        
        print(f"Found {len(users)} users to check:")
        
        updates_made = 0
        for user_id, username, current_role in users:
            print(f"  User: {username}, Current role: '{current_role}'")
            
            # Map old values to new enum values
            role_mapping = {
                'admin': 'ADMIN',
                'user': 'USER', 
                'viewer': 'VIEWER',
                'analyst': 'ANALYST'
            }
            
            if current_role in role_mapping:
                new_role = role_mapping[current_role]
                if current_role != new_role:
                    cursor.execute(
                        "UPDATE users SET role = ? WHERE id = ?",
                        (new_role, user_id)
                    )
                    print(f"    Updated: {current_role} -> {new_role}")
                    updates_made += 1
                else:
                    print(f"    No change needed")
            else:
                # If role is already correct or unknown, check if it needs fixing
                if current_role not in ['ADMIN', 'USER', 'VIEWER', 'ANALYST']:
                    # Default to USER for unknown roles
                    cursor.execute(
                        "UPDATE users SET role = ? WHERE id = ?",
                        ('USER', user_id)
                    )
                    print(f"    Unknown role '{current_role}' -> USER")
                    updates_made += 1
        
        if updates_made > 0:
            conn.commit()
            print(f"\nSuccess: Updated {updates_made} user roles")
        else:
            print("\nNo updates needed")
        
        # Verify the fix
        print("\nVerifying fixes...")
        cursor.execute("SELECT username, role FROM users")
        users_after = cursor.fetchall()
        
        for username, role in users_after:
            print(f"  {username}: {role}")
        
        print("\nEnum fix completed!")
        
    except Exception as e:
        print(f"Error: {e}")
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    fix_enum_values()