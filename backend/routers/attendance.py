"""
Attendance Router

Provides CRUD endpoints for attendance records.
All endpoints are documented via docstrings, which FastAPI uses to generate
OpenAPI documentation.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from backend.models import Attendance, User
from backend.database import get_db
from pydantic import BaseModel, Field
from datetime import date, datetime
from backend.middleware.rbac import PermissionChecker, has_permission, has_role

router = APIRouter(prefix="/attendance", tags=["attendance"])

class AttendanceCreate(BaseModel):
    """Payload for creating an attendance record."""
    user_id: int = Field(..., description="ID of the employee")
    attendance_date: date = Field(..., alias="date", description="Date of the attendance")
    time_in: datetime | None = Field(None, description="Clock‑in timestamp")
    time_out: datetime | None = Field(None, description="Clock‑out timestamp")
    status: str = Field(..., description="Attendance status (Present, Late, etc.)")

class AttendanceOut(BaseModel):
    """Response model for attendance records."""
    attendance_id: int
    user_id: int
    date: str
    time_in: datetime | None
    time_out: datetime | None
    hours_worked: float | None
    status: str

    @classmethod
    def from_orm(cls, obj):
        """Custom serialization to handle date conversion"""
        data = {
            **obj.__dict__,
            "date": obj.date.isoformat() if obj.date else None
        }
        return cls(**data)

@router.post("/", response_model=AttendanceOut, status_code=status.HTTP_201_CREATED)
@has_permission("create_attendance")
def create_attendance(
    att: AttendanceCreate,
    db: Session = Depends(get_db),
    user: User = Depends(PermissionChecker.require_permission("create_attendance"))
):
    """
    Create a new attendance entry.

    - **user_id**: Must reference an existing employee.
    - **date**: Attendance date.
    - **status**: One of the allowed status values.
    """
    # Verify user exists
    user = db.query(User).filter(User.user_id == att.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    db_att = Attendance(
        user_id=att.user_id,
        date=att.attendance_date,
        time_in=att.time_in,
        time_out=att.time_out,
        status=att.status
    )
    db.add(db_att)
    db.commit()
    db.refresh(db_att)
    return AttendanceOut.from_orm(db_att)

@router.get("/", response_model=List[AttendanceOut])
@has_permission("read_attendance")
def list_attendance(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    user: User = Depends(PermissionChecker.require_permission("read_attendance"))
):
    """
    Retrieve a paginated list of attendance records.
    """
    records = db.query(Attendance).offset(skip).limit(limit).all()
    return [AttendanceOut.from_orm(record) for record in records]

@router.get("/{attendance_id}", response_model=AttendanceOut)
@has_permission("read_attendance")
def get_attendance(
    attendance_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(PermissionChecker.require_permission("read_attendance"))
):
    """
    Get a single attendance record by its ID.
    """
    att = db.query(Attendance).filter(Attendance.attendance_id == attendance_id).first()
    if not att:
        raise HTTPException(status_code=404, detail="Attendance record not found")
    return AttendanceOut.from_orm(att)

@router.put("/{attendance_id}", response_model=AttendanceOut)
@has_permission("update_attendance")
def update_attendance(
    attendance_id: int,
    att: AttendanceCreate,
    db: Session = Depends(get_db),
    user: User = Depends(PermissionChecker.require_permission("update_attendance"))
):
    """
    Update an existing attendance record.
    """
    db_att = db.query(Attendance).filter(Attendance.attendance_id == attendance_id).first()
    if not db_att:
        raise HTTPException(status_code=404, detail="Attendance record not found")
    for field, value in att.model_dump(by_alias=True).items():
        setattr(db_att, field, value)
    db.commit()
    db.refresh(db_att)
    return AttendanceOut.from_orm(db_att)

@router.delete("/{attendance_id}", status_code=status.HTTP_204_NO_CONTENT)
@has_permission("delete_attendance")
def delete_attendance(
    attendance_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(PermissionChecker.require_permission("delete_attendance"))
):
    """
    Delete an attendance record.
    """
    db_att = db.query(Attendance).filter(Attendance.attendance_id == attendance_id).first()
    if not db_att:
        raise HTTPException(status_code=404, detail="Attendance record not found")
    db.delete(db_att)
    db.commit()
    return