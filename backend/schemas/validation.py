"""
Minimal Pydantic validation schemas for the AlphaSys HR API.
Only the fields required by the current codebase are defined.
Additional fields can be added later without breaking imports.
"""

from datetime import date
from typing import Optional

from pydantic import BaseModel, EmailStr, validator


class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str
    first_name: str
    last_name: str
    hourly_rate: float
    date_hired: date
    department_id: Optional[int] = None
    role_id: Optional[int] = None

    @validator("hourly_rate")
    def rate_non_negative(cls, v):
        if v < 0:
            raise ValueError("hourly_rate must be non‑negative")
        return v


class AttendanceCreate(BaseModel):
    user_id: int
    date: date
    time_in: Optional[str] = None
    time_out: Optional[str] = None
    status: Optional[str] = None


class PayrollCreate(BaseModel):
    user_id: int
    cutoff_start: date
    cutoff_end: date
    basic_pay: float
    overtime_pay: float = 0.0
    deductions: float = 0.0

    @validator("basic_pay", "overtime_pay", "deductions")
    def non_negative(cls, v):
        if v < 0:
            raise ValueError("Monetary values must be non‑negative")
        return v


class LeaveRequestCreate(BaseModel):
    user_id: int
    leave_type_id: int
    date_from: date
    date_to: date
    reason: Optional[str] = None


class OvertimeRequestCreate(BaseModel):
    user_id: int
    date: date
    hours_requested: float
    reason: Optional[str] = None

    @validator("hours_requested")
    def positive_hours(cls, v):
        if v <= 0:
            raise ValueError("hours_requested must be positive")
        return v