import os
import re
import psycopg2
import bcrypt
import configparser
import sys

ADMIN_EMAIL = "junnel@alphasys.com.au"
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "admin123")

def get_connection():
    config = configparser.ConfigParser()
    # Assuming alembic.ini is located one directory up from this script
    alembic_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "alembic.ini"))
    config.read(alembic_path)
    url = config.get("alembic", "sqlalchemy.url")
    # Expected format: postgresql+psycopg2://user:pass@host:port/dbname
    match = re.match(r"postgresql\\+psycopg2://([^:]+):([^@]+)@([^:]+):(\\d+)/(.*)", url)
    if not match:
        raise ValueError(f"Unable to parse DATABASE URL from alembic.ini: {url}")
    user, password, host, port, dbname = match.groups()
    return psycopg2.connect(
        dbname=dbname,
        user=user,
        password=password,
        host=host,
        port=port,
    )

def admin_exists(conn):
    with conn.cursor() as cur:
        cur.execute("SELECT 1 FROM users WHERE email = %s", (ADMIN_EMAIL,))
        return cur.fetchone() is not None

def create_admin(conn):
    hashed = bcrypt.hashpw(ADMIN_PASSWORD.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO users (username, password_hash, role, first_name, last_name, email, hourly_rate, date_hired, status)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (
                ADMIN_EMAIL,
                hashed,
                "admin",
                "Junnel",
                "Gallemaso",
                ADMIN_EMAIL,
                0.0,
                "2025-01-01",
                "active",
            ),
        )
        conn.commit()
        print(f"Admin user {ADMIN_EMAIL} created.")

def main():
    try:
        conn = get_connection()
        if not admin_exists(conn):
            create_admin(conn)
        else:
            print("Admin user already exists.")
    except Exception as e:
        print(f"Error during seeding: {e}", file=sys.stderr)
        sys.exit(1)
    finally:
        if 'conn' in locals() and conn:
            conn.close()

if __name__ == "__main__":
    main()