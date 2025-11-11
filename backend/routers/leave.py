from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from datetime import date, datetime

from backend.models import LeaveRequest, User, LeaveType
from backend.database import get_db
from pydantic import BaseModel, Field
from backend.middleware.rbac import PermissionChecker, has_permission, has_role

router = APIRouter(prefix="/leaves", tags=["leaves"])

class LeaveCreate(BaseModel):
    """Payload for creating a leave request."""
    user_id: int = Field(..., description="ID of the employee requesting leave")
    leave_type_id: int = Field(..., description="ID of the leave type")
    date_from: date = Field(..., description="Start date of leave")
    date_to: date = Field(..., description="End date of leave")
    reason: str | None = Field(None, description="Reason for the leave")
    status: str = Field(default="Pending", description="Leave status (Pending, Approved, Rejected, Cancelled)")
    approver_id: int | None = Field(None, description="ID of the manager who approves")
    approved_at: datetime | None = Field(None, description="Timestamp of approval")

class LeaveOut(BaseModel):
    """Response model for leave requests."""
    leave_id: int
    user_id: int
    leave_type_id: int
    date_from: date
    date_to: date
    reason: str | None
    status: str
    approver_id: int | None
    approved_at: datetime | None

    class Config:
        orm_mode = True

@router.post("/", response_model=LeaveOut, status_code=status.HTTP_201_CREATED)
@has_permission("create_leave")
def create_leave(leave: LeaveCreate, db: Session = Depends(get_db), user: User = Depends(PermissionChecker.require_permission("create_leave"))):
    """
    Create a new leave request.

    - **user_id** must reference an existing employee.
    - **leave_type_id** must reference a defined leave type.
    """
    user = db.query(User).filter(User.user_id == leave.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    lt = db.query(LeaveType).filter(LeaveType.leave_type_id == leave.leave_type_id).first()
    if not lt:
        raise HTTPException(status_code=404, detail="Leave type not found")
    db_leave = LeaveRequest(**leave.model_dump())
    db.add(db_leave)
    db.commit()
    db.refresh(db_leave)
    return db_leave

@router.get("/", response_model=List[LeaveOut])
@has_permission("read_leave")
def list_leaves(skip: int = 0, limit: int = 100, db: Session = Depends(get_db), user: User = Depends(PermissionChecker.require_permission("read_leave"))):
    """
    Retrieve a paginated list of leave requests.
    """
    return db.query(LeaveRequest).offset(skip).limit(limit).all()

@router.get("/{leave_id}", response_model=LeaveOut)
@has_permission("read_leave")
def get_leave(leave_id: int, db: Session = Depends(get_db), user: User = Depends(PermissionChecker.require_permission("read_leave"))):
    """
    Get a single leave request by its ID.
    """
    leave = db.query(LeaveRequest).filter(LeaveRequest.leave_id == leave_id).first()
    if not leave:
        raise HTTPException(status_code=404, detail="Leave request not found")
    return leave

@router.put("/{leave_id}", response_model=LeaveOut)
@has_permission("update_leave")
def update_leave(leave_id: int, leave: LeaveCreate, db: Session = Depends(get_db), user: User = Depends(PermissionChecker.require_permission("update_leave"))):
    """
    Update an existing leave request.
    """
    db_leave = db.query(LeaveRequest).filter(LeaveRequest.leave_id == leave_id).first()
    if not db_leave:
        raise HTTPException(status_code=404, detail="Leave request not found")
    for field, value in leave.dict().items():
        setattr(db_leave, field, value)
    db.commit()
    db.refresh(db_leave)
    return db_leave