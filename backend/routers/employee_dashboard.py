"""
Employee Dashboard Router

Provides API endpoints for employee-specific dashboard data and personal metrics.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
from datetime import datetime

from backend.database import get_db
from backend.models import User, LeaveRequest, OvertimeRequest
from backend.middleware.rbac import get_current_user, PermissionChecker
from backend.services.employee_dashboard_service import EmployeeDashboardService
from pydantic import BaseModel

router = APIRouter(prefix="/employee-dashboard", tags=["employee-dashboard"])

# Pydantic models for request/response
class LeaveBalance(BaseModel):
    leave_type: str
    remaining_balance: int

class PersonalKPIResponse(BaseModel):
    days_worked_this_month: int
    remaining_leave_balance: List[Dict[str, int]]
    total_overtime_hours_this_month: float
    latest_payslip: Optional[Dict[str, Any]]

class AttendanceSummary(BaseModel):
    date: str
    hours_worked: float
    status: str

class PersonalAttendanceLog(BaseModel):
    attendance_id: int
    date: str
    time_in: Optional[str]
    time_out: Optional[str]
    hours_worked: Optional[float]
    status: str

class PersonalLeaveRequest(BaseModel):
    leave_id: int
    leave_type: str
    date_from: str
    date_to: str
    days_requested: int
    reason: str
    status: str
    approver: str
    approved_at: Optional[str]

class PersonalOvertimeRequest(BaseModel):
    ot_id: int
    date: str
    hours_requested: float
    reason: str
    status: str
    approver: str
    approved_at: Optional[str]

class PersonalPayrollRecord(BaseModel):
    payroll_id: int
    cutoff_start: str
    cutoff_end: str
    basic_pay: float
    overtime_pay: float
    deductions: float
    net_pay: float
    generated_at: str

class LeaveRequestForm(BaseModel):
    leave_type_id: int
    date_from: str
    date_to: str
    reason: Optional[str] = None

class OvertimeRequestForm(BaseModel):
    date: str
    hours_requested: float
    reason: Optional[str] = None

# Personal KPI metrics endpoint
@router.get("/kpi", response_model=PersonalKPIResponse)
def get_personal_kpi(
    user_db_tuple: tuple[User, Session] = Depends(PermissionChecker.require_permission_with_db("employee_access"))
):
    """
    Get employee-specific KPI metrics.
    
    Requires employee_access permission.
    """
    # Unpack the tuple
    current_user, db = user_db_tuple
    
    try:
        # Get personal KPI data
        days_worked = EmployeeDashboardService.get_days_worked_this_month(db, current_user.user_id)
        remaining_leave = EmployeeDashboardService.get_remaining_leave_balance(db, current_user.user_id)
        overtime_hours = EmployeeDashboardService.get_total_overtime_hours_this_month(db, current_user.user_id)
        latest_payslip = EmployeeDashboardService.get_latest_payslip(db, current_user.user_id)
        
        # Format leave balance for response
        leave_balance_list = []
        for leave_type, balance in remaining_leave.items():
            leave_balance_list.append({
                "leave_type": leave_type,
                "remaining_balance": balance
            })
        
        return PersonalKPIResponse(
            days_worked_this_month=days_worked,
            remaining_leave_balance=leave_balance_list,
            total_overtime_hours_this_month=overtime_hours,
            latest_payslip=latest_payslip
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching personal KPI data: {str(e)}"
        )

# Attendance summary endpoint
@router.get("/attendance-summary", response_model=List[AttendanceSummary])
def get_attendance_summary_current_month(
    user_db_tuple: tuple[User, Session] = Depends(PermissionChecker.require_permission_with_db("employee_access"))
):
    """
    Get attendance summary for current month.
    
    Requires employee_access permission.
    """
    # Unpack the tuple
    current_user, db = user_db_tuple
    
    try:
        data = EmployeeDashboardService.get_attendance_summary_current_month(db, current_user.user_id)
        return [AttendanceSummary(**item) for item in data]
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching attendance summary: {str(e)}"
        )

# Personal attendance log endpoint
@router.get("/attendance-log", response_model=List[PersonalAttendanceLog])
def get_personal_attendance_log(
    user_db_tuple: tuple[User, Session] = Depends(PermissionChecker.require_permission_with_db("employee_access"))
):
    """
    Get personal attendance log.
    
    Requires employee_access permission.
    """
    # Unpack the tuple
    current_user, db = user_db_tuple
    
    try:
        data = EmployeeDashboardService.get_personal_attendance_log(db, current_user.user_id)
        return [PersonalAttendanceLog(**item) for item in data]
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching personal attendance log: {str(e)}"
        )

# Personal leave request history endpoint
@router.get("/leave-history", response_model=List[PersonalLeaveRequest])
def get_personal_leave_request_history(
    user_db_tuple: tuple[User, Session] = Depends(PermissionChecker.require_permission_with_db("employee_access"))
):
    """
    Get personal leave request history.
    
    Requires employee_access permission.
    """
    # Unpack the tuple
    current_user, db = user_db_tuple
    
    try:
        data = EmployeeDashboardService.get_personal_leave_request_history(db, current_user.user_id)
        return [PersonalLeaveRequest(**item) for item in data]
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching personal leave history: {str(e)}"
        )

# Personal overtime request history endpoint
@router.get("/overtime-history", response_model=List[PersonalOvertimeRequest])
def get_personal_overtime_request_history(
    user_db_tuple: tuple[User, Session] = Depends(PermissionChecker.require_permission_with_db("employee_access"))
):
    """
    Get personal overtime request history.
    
    Requires employee_access permission.
    """
    # Unpack the tuple
    current_user, db = user_db_tuple
    
    try:
        data = EmployeeDashboardService.get_personal_overtime_request_history(db, current_user.user_id)
        return [PersonalOvertimeRequest(**item) for item in data]
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching personal overtime history: {str(e)}"
        )

# Personal payroll history endpoint
@router.get("/payroll-history", response_model=List[PersonalPayrollRecord])
def get_personal_payroll_history(
    user_db_tuple: tuple[User, Session] = Depends(PermissionChecker.require_permission_with_db("employee_access"))
):
    """
    Get personal payroll history.
    
    Requires employee_access permission.
    """
    # Unpack the tuple
    current_user, db = user_db_tuple
    
    try:
        data = EmployeeDashboardService.get_personal_payroll_history(db, current_user.user_id)
        return [PersonalPayrollRecord(**item) for item in data]
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching personal payroll history: {str(e)}"
        )

# File leave request endpoint
@router.post("/leave-requests", response_model=Dict[str, str])
def create_leave_request(
    leave_request: LeaveRequestForm,
    user_db_tuple: tuple[User, Session] = Depends(PermissionChecker.require_permission_with_db("employee_access"))
):
    """
    Create a new leave request.
    
    Requires employee_access permission.
    """
    # Unpack the tuple
    current_user, db = user_db_tuple
    
    try:
        # Create new leave request
        new_leave_request = LeaveRequest(
            user_id=current_user.user_id,
            leave_type_id=leave_request.leave_type_id,
            date_from=datetime.strptime(leave_request.date_from, "%Y-%m-%d").date(),
            date_to=datetime.strptime(leave_request.date_to, "%Y-%m-%d").date(),
            reason=leave_request.reason or "",
            status=LeaveStatus.Pending.value
        )
        
        db.add(new_leave_request)
        db.commit()
        db.refresh(new_leave_request)
        
        return {"message": "Leave request created successfully", "leave_id": new_leave_request.leave_id}
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid date format: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating leave request: {str(e)}"
        )

# File overtime request endpoint
@router.post("/overtime-requests", response_model=Dict[str, str])
def create_overtime_request(
    overtime_request: OvertimeRequestForm,
    user_db_tuple: tuple[User, Session] = Depends(PermissionChecker.require_permission_with_db("employee_access"))
):
    """
    Create a new overtime request.
    
    Requires employee_access permission.
    """
    # Unpack the tuple
    current_user, db = user_db_tuple
    
    try:
        # Create new overtime request
        new_overtime_request = OvertimeRequest(
            user_id=current_user.user_id,
            date=datetime.strptime(overtime_request.date, "%Y-%m-%d").date(),
            hours_requested=overtime_request.hours_requested,
            reason=overtime_request.reason or "",
            status=OvertimeStatus.Pending.value
        )
        
        db.add(new_overtime_request)
        db.commit()
        db.refresh(new_overtime_request)
        
        return {"message": "Overtime request created successfully", "ot_id": new_overtime_request.ot_id}
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid date format: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating overtime request: {str(e)}"
        )