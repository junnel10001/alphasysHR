import sqlite3
import os

def seed_leave_types():
    """Seed the leave_types table with default values."""
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()
    
    # Default leave types
    leave_types = [
        (1, "Annual Leave", 20),
        (2, "Sick Leave", 10),
        (3, "Personal Leave", 5),
        (4, "Maternity Leave", 12),
        (5, "Paternity Leave", 5),
    ]
    
    # Insert leave types if they don't exist
    for leave_type in leave_types:
        cursor.execute(
            "INSERT OR IGNORE INTO leave_types (leave_type_id, leave_name, default_allocation) VALUES (?, ?, ?)",
            leave_type
        )
    
    conn.commit()
    print(f"Seeded {cursor.rowcount} leave types")
    
    # Verify insertion
    cursor.execute("SELECT * FROM leave_types")
    types = cursor.fetchall()
    print("Leave types in database:")
    for leave_type in types:
        print(f"  - ID: {leave_type[0]}, Name: {leave_type[1]}, Allocation: {leave_type[2]}")
    
    conn.close()

if __name__ == "__main__":
    seed_leave_types()