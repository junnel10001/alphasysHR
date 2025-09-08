import os
import psycopg2
import bcrypt

def get_connection():
    return psycopg2.connect(
        dbname=os.getenv("POSTGRES_DB", "alphasys"),
        user=os.getenv("POSTGRES_USER", "postgres"),
        password=os.getenv("POSTGRES_PASSWORD", "postgres"),
        host=os.getenv("POSTGRES_HOST", "db"),
        port=os.getenv("POSTGRES_PORT", "5432")
    )

def admin_exists(conn):
    with conn.cursor() as cur:
        cur.execute("SELECT 1 FROM users WHERE email = %s", (os.getenv("ADMIN_EMAIL"),))
        return cur.fetchone() is not None

def create_admin(conn):
    email = os.getenv("ADMIN_EMAIL")
    password = os.getenv("ADMIN_PASSWORD")
    hashed = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO users (username, password_hash, role, first_name, last_name, email, hourly_rate, date_hired, status)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (
                email,
                hashed,
                "admin",
                "Junnel",
                "Gallemaso",
                email,
                0.0,
                "2025-01-01",
                "active"
            )
        )
        conn.commit()
        print(f"Admin user {email} created.")

def main():
    conn = get_connection()
    if not admin_exists(conn):
        create_admin(conn)
    else:
        print("Admin user already exists.")
    conn.close()

if __name__ == "__main__":
    main()