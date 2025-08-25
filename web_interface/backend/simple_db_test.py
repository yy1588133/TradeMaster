"""
Simple database connection diagnostics
Test async database operations
"""
import asyncio
import sys
import time
from pathlib import Path

# Add project root to Python path
sys.path.append(str(Path(__file__).parent))

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, text

from app.core.database import engine, get_db_session
from app.core.config import settings
from app.models.database import User
from app.crud.user import user_crud

async def test_basic_connection():
    """Test basic database connection"""
    print("1. Testing basic database connection...")
    try:
        start_time = time.time()
        async with get_db_session() as session:
            result = await session.execute(text("SELECT 1"))
            value = result.scalar()
            end_time = time.time()
            
            print(f"   SUCCESS: Basic connection works: {value}, Time: {end_time - start_time:.3f}s")
            return True
    except Exception as e:
        print(f"   ERROR: Basic connection failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_user_table_access():
    """Test user table access"""
    print("2. Testing user table access...")
    try:
        start_time = time.time()
        async with get_db_session() as session:
            result = await session.execute(select(User).limit(1))
            users = result.scalars().all()
            end_time = time.time()
            
            print(f"   SUCCESS: User table access works, Found {len(users)} users, Time: {end_time - start_time:.3f}s")
            return True
    except Exception as e:
        print(f"   ERROR: User table access failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_user_authentication():
    """Test user authentication operation"""
    print("3. Testing user authentication...")
    try:
        start_time = time.time()
        async with get_db_session() as session:
            # Try to authenticate admin user
            user = await user_crud.authenticate(session, username="admin", password="admin123")
            end_time = time.time()
            
            if user:
                print(f"   SUCCESS: User authentication works: {user.username}, Time: {end_time - start_time:.3f}s")
            else:
                print(f"   WARNING: User authentication returned None, Time: {end_time - start_time:.3f}s")
            return True
    except Exception as e:
        print(f"   ERROR: User authentication failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_concurrent_operations():
    """Test concurrent database operations"""
    print("4. Testing concurrent database operations...")
    try:
        start_time = time.time()
        
        # Create multiple concurrent database queries
        async def single_query():
            async with get_db_session() as session:
                result = await session.execute(select(User).limit(1))
                return result.scalars().first()
        
        # Execute 5 queries concurrently
        tasks = [single_query() for _ in range(5)]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        end_time = time.time()
        
        success_count = sum(1 for r in results if not isinstance(r, Exception))
        error_count = len(results) - success_count
        
        print(f"   Concurrent operations result: {success_count} success, {error_count} failed, Time: {end_time - start_time:.3f}s")
        
        if error_count > 0:
            print("   Error details:")
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    print(f"     Task {i+1}: {result}")
        
        return error_count == 0
    except Exception as e:
        print(f"   ERROR: Concurrent test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_timeout_behavior():
    """Test database timeout behavior"""
    print("5. Testing database timeout behavior...")
    try:
        start_time = time.time()
        
        # Test if operations timeout after a reasonable time
        async with get_db_session() as session:
            # This should complete quickly
            result = await asyncio.wait_for(
                session.execute(select(User).limit(1)),
                timeout=5.0  # 5 second timeout
            )
            users = result.scalars().all()
            
        end_time = time.time()
        print(f"   SUCCESS: Timeout test passed, Time: {end_time - start_time:.3f}s")
        return True
    except asyncio.TimeoutError:
        end_time = time.time()
        print(f"   ERROR: Operation timed out after {end_time - start_time:.3f}s")
        return False
    except Exception as e:
        print(f"   ERROR: Timeout test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """Main test function"""
    print("TradeMaster Database Diagnostics")
    print("="*50)
    print(f"Database URL: {settings.get_database_url()}")
    print(f"Debug mode: {settings.DEBUG}")
    print()
    
    tests = [
        test_basic_connection,
        test_user_table_access,
        test_user_authentication,
        test_concurrent_operations,
        test_timeout_behavior,
    ]
    
    passed = 0
    total = len(tests)
    
    for test_func in tests:
        try:
            success = await test_func()
            if success:
                passed += 1
            print()
        except Exception as e:
            print(f"   ERROR: Test exception: {e}")
            print()
    
    print("="*50)
    print(f"Test Summary: {passed}/{total} passed")
    
    if passed < total:
        print("\nRecommended fixes:")
        print("1. Check SQLite database file permissions")
        print("2. Consider switching to PostgreSQL for better async support")
        print("3. Check if other processes are locking the database file")
        print("4. Verify aiosqlite driver version compatibility")
    else:
        print("\nAll database operation tests passed!")
    
    # Cleanup connections
    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(main())