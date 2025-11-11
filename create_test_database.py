import pymysql
import os
from sqlalchemy import create_engine, text

# MySQL connection parameters
MYSQL_HOST = os.getenv("MYSQL_HOST", "127.0.0.1")
MYSQL_USER = os.getenv("MYSQL_USER", "root")
MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD", "")
MYSQL_DATABASE = os.getenv("MYSQL_DATABASE", "alpha_hr")
TEST_DATABASE = "alpha_hr_test"

def create_test_database():
    """Create the MySQL test database if it doesn't exist"""
    try:
        # Connect to MySQL server (without specifying database)
        connection = pymysql.connect(
            host=MYSQL_HOST,
            user=MYSQL_USER,
            password=MYSQL_PASSWORD,
            charset='utf8mb4'
        )
        
        with connection.cursor() as cursor:
            # Create test database if it doesn't exist
            cursor.execute(f"CREATE DATABASE IF NOT EXISTS {TEST_DATABASE} CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
            print(f"Test database '{TEST_DATABASE}' created successfully or already exists")
        
        connection.close()
        return True
        
    except Exception as e:
        print(f"Error creating test database: {e}")
        return False

if __name__ == "__main__":
    print("Setting up MySQL test database for AlphaHR...")
    
    if create_test_database():
        print("✓ Test database setup completed")
    else:
        print("✗ Test database setup failed")