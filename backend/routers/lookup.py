from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from backend.database import get_db
from backend.models import Department, Role, Office, User, Position, EmploymentStatus, LeaveType
from backend.schemas import DepartmentSchema, RoleSchema, OfficeSchema, UserSchema, PositionSchema, EmploymentStatusSchema
from backend.middleware.rbac import PermissionChecker

router = APIRouter(prefix="/lookup", tags=["lookup"])

@router.get("/departments", response_model=list[DepartmentSchema])
def get_departments(
    db: Session = Depends(get_db),
    user = Depends(PermissionChecker.require_permission("view_departments"))
):
    return db.query(Department).all()

@router.get("/roles", response_model=list[RoleSchema])
def get_roles(
    db: Session = Depends(get_db),
    user = Depends(PermissionChecker.require_permission("view_roles"))
):
    return db.query(Role).all()

@router.get("/offices", response_model=list[OfficeSchema])
def get_offices(
    db: Session = Depends(get_db),
    user = Depends(PermissionChecker.require_permission("view_departments"))
):
    return db.query(Office).all()

@router.get("/line-managers", response_model=list[UserSchema])
def get_line_managers(
    db: Session = Depends(get_db),
    user = Depends(PermissionChecker.require_permission("read_employee"))
):
    # Line managers can be any user in the system
    # Return all active users that can be selected as line managers
    return db.query(User).filter(User.status == "active").all()

@router.get("/positions", response_model=list[PositionSchema])
def get_positions(
    db: Session = Depends(get_db),
    user = Depends(PermissionChecker.require_permission("view_departments"))
):
    return db.query(Position).all()

@router.get("/employment-statuses", response_model=list[EmploymentStatusSchema])
def get_employment_statuses(
    db: Session = Depends(get_db),
    user = Depends(PermissionChecker.require_permission("view_departments"))
):
    return db.query(EmploymentStatus).all()

@router.get("/leave-types", response_model=list[dict])
def get_leave_types(
    db: Session = Depends(get_db),
    user = Depends(PermissionChecker.require_permission("view_departments"))
):
    leave_types = db.query(LeaveType).all()
    return [{"leave_type_id": lt.leave_type_id, "leave_name": lt.leave_name} for lt in leave_types]