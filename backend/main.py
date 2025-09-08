from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel
from typing import List
import bcrypt
import jwt
import os
import psycopg2
from datetime import datetime, timedelta

app = FastAPI()

# JWT configuration
SECRET_KEY = os.getenv("JWT_SECRET", "supersecretkey")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

# Database connection (replace with your actual credentials)
def get_db():
    conn = psycopg2.connect(
        dbname=os.getenv("POSTGRES_DB", "alphasys"),
        user=os.getenv("POSTGRES_USER", "postgres"),
        password=os.getenv("POSTGRES_PASSWORD", "postgres"),
        host=os.getenv("POSTGRES_HOST", "localhost"),
        port=os.getenv("POSTGRES_PORT", "5432")
    )
    return conn

# ------------------------------
# Pydantic Schemas
# ------------------------------
class Token(BaseModel):
    access_token: str
    token_type: str

class UserInDB(BaseModel):
    user_id: int
    username: str
    hashed_password: str
    role: str

class UserCreate(BaseModel):
    username: str
    password: str
    role: str = "employee"

# ------------------------------
# Utility Functions
# ------------------------------
def verify_password(plain_password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))

def get_password_hash(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def get_user_by_username(conn, username: str):
    with conn.cursor() as cur:
        cur.execute("SELECT user_id, username, password_hash, role FROM users WHERE username = %s", (username,))
        row = cur.fetchone()
        if row:
            return UserInDB(user_id=row[0], username=row[1], hashed_password=row[2], role=row[3])
    return None

def create_user(conn, user: UserCreate):
    hashed = get_password_hash(user.password)
    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO users (username, password_hash, role, first_name, last_name, email, hourly_rate, date_hired, status)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING user_id
            """,
            (
                user.username,
                hashed,
                user.role,
                "Admin",               # first_name placeholder
                "User",                # last_name placeholder
                user.username,         # email same as username for demo
                0.0,                   # hourly_rate placeholder
                datetime.utcnow().date(),
                "active"
            )
        )
        user_id = cur.fetchone()[0]
        conn.commit()
        return user_id

# ------------------------------
# API Endpoints
# ------------------------------
@app.post("/token", response_model=Token)
def login(form_data: OAuth2PasswordRequestForm = Depends()):
    conn = get_db()
    user = get_user_by_username(conn, form_data.username)
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    access_token = create_access_token(data={"sub": user.username, "role": user.role})
    return {"access_token": access_token, "token_type": "bearer"}

@app.post("/users/", status_code=201)
def register_user(user: UserCreate):
    conn = get_db()
    existing = get_user_by_username(conn, user.username)
    if existing:
        raise HTTPException(status_code=400, detail="Username already exists")
    user_id = create_user(conn, user)
    return {"user_id": user_id, "username": user.username, "role": user.role}

# Example protected route
@app.get("/me/")
def read_current_user(token: str = Depends(OAuth2PasswordRequestForm)):
    # In a real implementation, decode JWT and fetch user info
    return {"msg": "Protected endpoint – token validation to be added"}

# Seed admin user (run once)
def seed_admin():
    conn = get_db()
    admin_email = "junnel@alphasys.com.au"
    if not get_user_by_username(conn, admin_email):
        admin = UserCreate(username=admin_email, password="ChangeMe!", role="admin")
        create_user(conn, admin)
        print("Admin user created.")
    else:
        print("Admin user already exists.")

if __name__ == "__main__":
    # Seed admin on startup (development only)
    seed_admin()