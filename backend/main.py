from fastapi import FastAPI, Depends, HTTPException, status
# ------------------------------------------------------------------
# JWT configuration
# ------------------------------------------------------------------
from backend.config import JWT_SECRET, JWT_ALGORITHM
ACCESS_TOKEN_EXPIRE_MINUTES = 30
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from pydantic import BaseModel
from typing import List
import jwt
import os
from datetime import datetime, timedelta
from backend.utils.auth import verify_password, get_password_hash, create_access_token

from sqlalchemy.orm import Session
from backend.database import get_db, engine
from backend.models import Base, User

# Ensure database tables are created at import time (useful for tests that bypass FastAPI startup)
Base.metadata.create_all(bind=engine)
from backend.middleware.rbac import get_current_user

# ------------------------------------------------------------------
# Application initialization
# ------------------------------------------------------------------
# Removed duplicate FastAPI instance; will use the one with lifespan defined later.
# The router will be included after the lifespan‑configured app is created.

# ------------------------------------------------------------------
# Lifespan event: create tables and seed data on startup
# ------------------------------------------------------------------
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Ensure all tables exist for the current engine (real DB or test DB)
    Base.metadata.create_all(bind=engine)

    # Seed admin users and RBAC data (functions are idempotent)
    seed_admin()
    seed_rbac()
    # Seed offices for the dropdown
    from backend.seed_office import seed_offices
    seed_offices()
    yield

app = FastAPI(lifespan=lifespan)

# ------------------------------------------------------------------
# CORS configuration (allow any origin for development)
# ------------------------------------------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Updated to allow any origin for CORS
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ------------------------------------------------------------------
# Include routers (after the FastAPI app with lifespan is instantiated)
# ------------------------------------------------------------------
from backend.routers import (
    employees,
    attendance,
    leave,
    payroll,
    permissions,
    roles,
    dashboard,
    employee_dashboard,
    overtime,
    export,
    lookup,
    departments,
    invitations,
)

# Include all routers, including dashboard, after the app is defined.
app.include_router(employees.router)
app.include_router(attendance.router)
app.include_router(leave.router)
app.include_router(payroll.router)
app.include_router(permissions.router)
app.include_router(roles.router)
app.include_router(dashboard.router)
app.include_router(employee_dashboard.router)
app.include_router(overtime.router)
app.include_router(export.router)
app.include_router(lookup.router)
app.include_router(departments.router)
app.include_router(invitations.router)

# ------------------------------------------------------------------
# Pydantic Schemas
# ------------------------------------------------------------------
class Token(BaseModel):
    access_token: str
    token_type: str


class UserCreate(BaseModel):
    username: str
    password: str
    role: str = "employee"

class UserInDB(BaseModel):
    user_id: int
    username: str
    hashed_password: str
    role: str


# ------------------------------------------------------------------
# Note: Utility functions verify_password, get_password_hash, and create_access_token
# are now imported from backend.utils.auth
# ------------------------------------------------------------------


# Note: create_access_token function is now imported from backend.utils.auth


def get_user_by_username(db: Session, username: str):
    # Try to find user by username first, then by email as fallback
    user = db.query(User).filter(User.username == username).first()
    if not user:
        # Fallback: try to find by email
        user = db.query(User).filter(User.email == username).first()
    
    if user:
        return UserInDB(
            user_id=user.user_id,
            username=user.username,
            hashed_password=user.password_hash,
            role=user.role_name,
        )
    return None


def create_user(db: Session, user: UserCreate):
    hashed = get_password_hash(user.password)
    db_user = User(
        username=user.username,
        password_hash=hashed,
        role_name=user.role,
        first_name="Admin",
        last_name="User",
        email=user.username,
        hourly_rate=0.0,
        date_hired=datetime.utcnow().date(),
        status="active",
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user.user_id


# ------------------------------------------------------------------
# API Endpoints
# ------------------------------------------------------------------
@app.post("/token", response_model=Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    # DEBUG: Log incoming credentials (remove in production)
    print(f"[DEBUG] /token called with username={form_data.username}")

    user = get_user_by_username(db, form_data.username)
    if not user:
        print("[DEBUG] User not found")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    password_valid = verify_password(form_data.password, user.hashed_password)
    print(f"[DEBUG] Password verification result: {password_valid}")

    if not password_valid:
        print("[DEBUG] Invalid password")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    token_data = {"sub": user.username, "role": user.role}
    print(f"[DEBUG] Token payload: {token_data}")

    access_token = create_access_token(
        data=token_data,
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    print(f"[DEBUG] Generated access token: {access_token}")

    return {"access_token": access_token, "token_type": "bearer"}


@app.post("/register", status_code=201)
def register_user(user: UserCreate, db: Session = Depends(get_db)):
    existing = get_user_by_username(db, user.username)
    if existing:
        raise HTTPException(status_code=400, detail="Username already exists")
    user_id = create_user(db, user)
    return {"user_id": user_id, "username": user.username, "role": user.role}


@app.post("/users/", status_code=201)
def create_user_endpoint(user: UserCreate, db: Session = Depends(get_db)):
    existing = get_user_by_username(db, user.username)
    if existing:
        raise HTTPException(status_code=400, detail="Username already exists")
    user_id = create_user(db, user)
    return {"user_id": user_id, "username": user.username, "role": user.role}


@app.get("/users/me")
def read_current_user(current_user: User = Depends(get_current_user)):
    return {
        "id": current_user.user_id,
        "username": current_user.username,
        "email": current_user.email,
        "full_name": f"{current_user.first_name} {current_user.last_name}",
        "role": current_user.role_name,
        "permissions": [],  # Populated by RBAC middleware
    }


def seed_admin():
    db = next(get_db())
    try:
        primary_admin_email = "junnel@alphasys.com.au"
        test_admin_email = "admin@test.com"
        admin_password = "password"

        if not get_user_by_username(db, primary_admin_email):
            primary_admin = UserCreate(username=primary_admin_email, password=admin_password, role="admin")
            create_user(db, primary_admin)
            print("Primary admin user created.")

        if not get_user_by_username(db, test_admin_email):
            test_admin = UserCreate(username=test_admin_email, password=admin_password, role="admin")
            create_user(db, test_admin)
            print("Test admin user created.")

        for email in (primary_admin_email, test_admin_email):
            created_user = get_user_by_username(db, email)
            if created_user:
                print(f"DEBUG: Admin user verified - Username: {created_user.username}, Role: {created_user.role}")
            else:
                print(f"DEBUG: Admin user creation failed for {email}!")
    finally:
        db.close()


def seed_rbac():
    from backend.utils.rbac import RBACUtils, ensure_admin_employee_access
    db = next(get_db())
    try:
        RBACUtils.seed_default_permissions(db)
        RBACUtils.seed_default_roles(db)
        # Ensure admin role has employee_access permission
        ensure_admin_employee_access(db)
        print("Default RBAC data seeded.")
    finally:
        db.close()


@app.get("/me/permissions")
def get_current_user_permissions(
    current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    from backend.utils.rbac import RBACUtils
    permissions = RBACUtils.get_user_permission_names(current_user, db)
    return {
        "user_id": current_user.user_id,
        "username": current_user.username,
        "role": current_user.role_name,
        "permissions": permissions,
    }


if __name__ == "__main__":
    os.environ["TESTING"] = "false"
    seed_admin()
    seed_rbac()