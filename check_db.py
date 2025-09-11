import sqlite3
import os

# Check if database file exists
if os.path.exists("users.db"):
    print("Database file exists")
    
    # Connect to database
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()
    
    # Get table names
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    
    print("Tables in database:")
    for table in tables:
        print(f"  - {table[0]}")
    
    # Check if users table has data
    if "users" in [table[0] for table in tables]:
        cursor.execute("SELECT COUNT(*) FROM users")
        user_count = cursor.fetchone()[0]
        print(f"Users table has {user_count} records")
        
        cursor.execute("SELECT user_id, username FROM users LIMIT 5")
        users = cursor.fetchall()
        print("Sample users:")
        for user in users:
            print(f"  - ID: {user[0]}, Username: {user[1]}")
    
    # Check if leave_types table has data
    if "leave_types" in [table[0] for table in tables]:
        cursor.execute("SELECT COUNT(*) FROM leave_types")
        leave_type_count = cursor.fetchone()[0]
        print(f"Leave types table has {leave_type_count} records")
        
        cursor.execute("SELECT leave_type_id, leave_name FROM leave_types LIMIT 5")
        leave_types = cursor.fetchall()
        print("Sample leave types:")
        for leave_type in leave_types:
            print(f"  - ID: {leave_type[0]}, Name: {leave_type[1]}")
    
    conn.close()
else:
    print("Database file does not exist")