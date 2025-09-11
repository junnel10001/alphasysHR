from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel, EmailStr, Field
from typing import List
import bcrypt
import jwt
import os
from datetime import datetime, timedelta

from sqlalchemy.orm import Session
from .database import get_db
from .models import User

app = FastAPI()

# Include routers
from .routers import employees, attendance, leave, payroll, permissions, roles, dashboard, employee_dashboard, overtime, activity, export
app.include_router(employees.router)
app.include_router(attendance.router)
app.include_router(leave.router)
app.include_router(payroll.router)
app.include_router(permissions.router)
app.include_router(roles.router)
app.include_router(dashboard.router)
app.include_router(employee_dashboard.router)
app.include_router(overtime.router)
app.include_router(activity.router)
app.include_router(export.router)


# JWT configuration
SECRET_KEY = os.getenv("JWT_SECRET", "supersecretkey")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

# ------------------------------
# Pydantic Schemas
# ------------------------------
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

def get_user_by_username(db: Session, username: str):
    user = db.query(User).filter(User.username == username).first()
    if user:
        return UserInDB(
            user_id=user.user_id,
            username=user.username,
            hashed_password=user.password_hash,
            role=user.role_name
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
        status="active"
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user.user_id

# ------------------------------
# API Endpoints
# ------------------------------
@app.post("/token", response_model=Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = get_user_by_username(db, form_data.username)
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    access_token = create_access_token(data={"sub": user.username, "role": user.role})
    return {"access_token": access_token, "token_type": "bearer"}

@app.post("/users/", status_code=201)
def register_user(user: UserCreate, db: Session = Depends(get_db)):
    existing = get_user_by_username(db, user.username)
    if existing:
        raise HTTPException(status_code=400, detail="Username already exists")
    user_id = create_user(db, user)
    return {"user_id": user_id, "username": user.username, "role": user.role}

@app.get("/me/")
def read_current_user():
    return {"msg": "Protected endpoint – token validation to be added"}

def seed_admin():
    # Only seed admin if TESTING environment variable is not set
    if os.getenv("TESTING") == "true":
        return
    
    db = next(get_db())
    admin_email = "junnel@alphasys.com.au"
    admin_password = "password"
    if not get_user_by_username(db, admin_email):
        admin = UserCreate(username=admin_email, password=admin_password, role="admin")
        create_user(db, admin)
        print("Admin user created.")
    else:
        print("Admin user already exists.")

def seed_rbac():
    """Seed default RBAC roles and permissions."""
    # Only seed RBAC if TESTING environment variable is not set
    if os.getenv("TESTING") == "true":
        return
        
    from .utils.rbac import RBACUtils
    db = next(get_db())
    
    # Seed default permissions and roles
    RBACUtils.seed_default_permissions(db)
    RBACUtils.seed_default_roles(db)
    print("Default RBAC data seeded.")

# Import RBAC middleware
from .middleware.rbac import get_current_user

@app.get("/me/permissions")
def get_current_user_permissions(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """
    Get the current user's permissions.
    
    This endpoint requires authentication.
    """
    from .utils.rbac import RBACUtils
    permissions = RBACUtils.get_user_permission_names(current_user, db)
    
    return {
        "user_id": current_user.user_id,
        "username": current_user.username,
        "role": current_user.role_name,
        "permissions": permissions
    }

if __name__ == "__main__":
    # Set environment variable to avoid seeding during tests
    os.environ["TESTING"] = "false"
    seed_admin()
    seed_rbac()