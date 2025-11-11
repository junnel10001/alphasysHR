import os
import psycopg2
import bcrypt
import re
from typing import Optional

def get_connection():
    """Get database connection with validation"""
    db_name = os.getenv("POSTGRES_DB")
    db_user = os.getenv("POSTGRES_USER")
    db_password = os.getenv("POSTGRES_PASSWORD")
    db_host = os.getenv("POSTGRES_HOST")
    db_port = os.getenv("POSTGRES_PORT", "5432")
    
    if not all([db_name, db_user, db_password]):
        raise RuntimeError("Database environment variables not set")
    
    return psycopg2.connect(
        dbname=db_name,
        user=db_user,
        password=db_password,
        host=db_host,
        port=db_port
    )

def validate_email(email: str) -> bool:
    """Validate email format"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def validate_password(password: str) -> bool:
    """Validate password strength"""
    if len(password) < 8:
        return False
    if not re.search(r'[A-Z]', password):
        return False
    if not re.search(r'[a-z]', password):
        return False
    if not re.search(r'\d', password):
        return False
    return True

def get_admin_email() -> str:
    """Get and validate admin email from environment"""
    email = os.getenv("ADMIN_EMAIL")
    if not email:
        raise RuntimeError("ADMIN_EMAIL environment variable not set")
    if not validate_email(email):
        raise ValueError(f"Invalid admin email format: {email}")
    return email

def get_admin_password() -> str:
    """Get and validate admin password from environment"""
    password = os.getenv("ADMIN_PASSWORD")
    if not password:
        raise RuntimeError("ADMIN_PASSWORD environment variable not set")
    if not validate_password(password):
        raise ValueError("Admin password must be at least 8 characters with uppercase, lowercase, and number")
    return password

def admin_exists(conn, email: str) -> bool:
    """Check if admin user already exists"""
    with conn.cursor() as cur:
        cur.execute("SELECT 1 FROM users WHERE email = %s", (email,))
        return cur.fetchone() is not None

def create_admin(conn, email: str, password: str):
    """Create admin user with validation"""
    # Hash password with salt
    hashed = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
    
    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO users (username, password_hash, role, first_name, last_name, email, hourly_rate, date_hired, status)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (
                email.split('@')[0],  # Use part of email as username
                hashed,
                "admin",
                "System",
                "Admin",
                email,
                0.0,
                "2025-01-01",
                "active"
            )
        )
        conn.commit()
        print(f"Admin user {email} created successfully.")

def main():
    """Main seeding function with error handling"""
    try:
        # Validate environment variables
        admin_email = get_admin_email()
        admin_password = get_admin_password()
        
        # Get database connection
        conn = get_connection()
        
        # Check if admin already exists
        if admin_exists(conn, admin_email):
            print(f"Admin user {admin_email} already exists.")
        else:
            # Create admin user
            create_admin(conn, admin_email, admin_password)
            print(f"Admin user {admin_email} created successfully.")
            
    except Exception as e:
        print(f"Error during admin seeding: {str(e)}")
        raise
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    main()