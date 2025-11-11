"""
Dashboard Router

Provides API endpoints for dashboard KPI data and analytics.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Dict, Any
from datetime import datetime

from backend.database import get_db
from backend.models import User, LeaveRequest, OvertimeRequest
from backend.middleware.rbac import get_current_user, PermissionChecker
from backend.services.dashboard_service import DashboardService
from pydantic import BaseModel

router = APIRouter(prefix="/dashboard", tags=["dashboard"])

# Pydantic models for request/response
class AttendanceOverview(BaseModel):
 name: str
 value: int
 present: int
 late: int
 absent: int

class TodayAttendance(BaseModel):
    attendance_id: int
    user_id: int
    name: str
    email: str
    date: str
    time_in: str | None = None
    time_out: str | None = None
    hours_worked: float | None = None
    status: str

class PayrollSummary(BaseModel):
    total_payrolls: int
    total_basic_pay: float
    total_overtime_pay: float
    total_deductions: float
    total_net_pay: float

class LeaveStats(BaseModel):
    pending: int
    approved: int
    rejected: int
    cancelled: int

class OvertimeStats(BaseModel):
    pending: int
    approved: int
    rejected: int

class KPIResponse(BaseModel):
    employees_present_today: int
    late_absent_today: Dict[str, int]
    pending_leave_requests: int
    pending_overtime_requests: int
    attendance_overview: List[AttendanceOverview]
    today_attendance: List[TodayAttendance]
    payroll_summary: PayrollSummary
    leave_stats: LeaveStats
    overtime_stats: OvertimeStats

@router.get("/kpi", response_model=KPIResponse)
def get_dashboard_kpi(
    user_db_tuple: tuple[User, Session] = Depends(PermissionChecker.require_permission_with_db("employee_access"))
):
    # Unpack the tuple
    current_user, db = user_db_tuple
    """
    Get all dashboard KPI data.
    
    Requires employee_access permission.
    """
    try:
        # Get all KPI data
        employees_present = DashboardService.get_employees_present_today(db)
        late_absent = DashboardService.get_late_absent_today(db)
        pending_leave = DashboardService.get_pending_leave_requests(db)
        pending_overtime = DashboardService.get_pending_overtime_requests(db)
        attendance_overview = DashboardService.get_attendance_overview(db)
        today_attendance = DashboardService.get_today_attendance_table(db)
        payroll_summary = DashboardService.get_payroll_summary(db)
        leave_stats = DashboardService.get_leave_request_stats(db)
        overtime_stats = DashboardService.get_overtime_request_stats(db)
        
        return KPIResponse(
            employees_present_today=employees_present,
            late_absent_today=late_absent,
            pending_leave_requests=pending_leave,
            pending_overtime_requests=pending_overtime,
            attendance_overview=[
                AttendanceOverview(**item) for item in attendance_overview
            ],
            today_attendance=[
                TodayAttendance(**item) for item in today_attendance
            ],
            payroll_summary=PayrollSummary(**payroll_summary),
            leave_stats=LeaveStats(**leave_stats),
            overtime_stats=OvertimeStats(**overtime_stats)
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching dashboard data: {str(e)}"
        )

@router.get("/kpi/employees-present")
def get_employees_present_today(
    user_db_tuple: tuple[User, Session] = Depends(PermissionChecker.require_permission_with_db("employee_access"))
):
    # Unpack the tuple
    current_user, db = user_db_tuple
    """
    Get count of employees present today.
    
    Requires employee_access permission.
    """
    try:
        count = DashboardService.get_employees_present_today(db)
        return {"employees_present_today": count}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching employees present: {str(e)}"
        )

@router.get("/kpi/late-absent")
def get_late_absent_today(
    user_db_tuple: tuple[User, Session] = Depends(PermissionChecker.require_permission_with_db("employee_access"))
):
    # Unpack the tuple
    current_user, db = user_db_tuple
    """
    Get count of late and absent employees today.
    
    Requires employee_access permission.
    """
    try:
        data = DashboardService.get_late_absent_today(db)
        return data
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching late/absent data: {str(e)}"
        )

@router.get("/kpi/pending-leave")
def get_pending_leave_requests(
    user_db_tuple: tuple[User, Session] = Depends(PermissionChecker.require_permission_with_db("employee_access"))
):
    # Unpack the tuple
    current_user, db = user_db_tuple
    """
    Get count of pending leave requests.
    
    Requires employee_access permission.
    """
    try:
        count = DashboardService.get_pending_leave_requests(db)
        return {"pending_leave_requests": count}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching pending leave requests: {str(e)}"
        )

@router.get("/kpi/pending-overtime")
def get_pending_overtime_requests(
    user_db_tuple: tuple[User, Session] = Depends(PermissionChecker.require_permission_with_db("employee_access"))
):
    # Unpack the tuple
    current_user, db = user_db_tuple
    """
    Get count of pending overtime requests.
    
    Requires employee_access permission.
    """
    try:
        count = DashboardService.get_pending_overtime_requests(db)
        return {"pending_overtime_requests": count}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching pending overtime requests: {str(e)}"
        )

@router.get("/kpi/attendance-overview")
def get_attendance_overview(
    user_db_tuple: tuple[User, Session] = Depends(PermissionChecker.require_permission_with_db("employee_access"))
):
    # Unpack the tuple
    current_user, db = user_db_tuple
    """
    Get attendance overview data for the last 7 days.
    
    Requires employee_access permission.
    """
    try:
        data = DashboardService.get_attendance_overview(db)
        return {"attendance_overview": data}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching attendance overview: {str(e)}"
        )

@router.get("/kpi/today-attendance")
def get_today_attendance(
    user_db_tuple: tuple[User, Session] = Depends(PermissionChecker.require_permission_with_db("employee_access"))
):
    # Unpack the tuple
    current_user, db = user_db_tuple
    """
    Get today's attendance table data.
    
    Requires employee_access permission.
    """
    try:
        data = DashboardService.get_today_attendance_table(db)
        return {"today_attendance": data}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching today's attendance: {str(e)}"
        )

@router.get("/kpi/payroll-summary")
def get_payroll_summary(
    user_db_tuple: tuple[User, Session] = Depends(PermissionChecker.require_permission_with_db("employee_access"))
):
    # Unpack the tuple
    current_user, db = user_db_tuple
    """
    Get payroll summary data.
    
    Requires employee_access permission.
    """
    try:
        data = DashboardService.get_payroll_summary(db)
        return {"payroll_summary": data}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching payroll summary: {str(e)}"
        )

@router.get("/kpi/leave-stats")
def get_leave_stats(
    user_db_tuple: tuple[User, Session] = Depends(PermissionChecker.require_permission_with_db("employee_access"))
):
    # Unpack the tuple
    current_user, db = user_db_tuple
    """
    Get leave request statistics.
    
    Requires employee_access permission.
    """
    try:
        data = DashboardService.get_leave_request_stats(db)
        return {"leave_stats": data}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching leave stats: {str(e)}"
        )

@router.get("/kpi/overtime-stats")
def get_overtime_stats(
    user_db_tuple: tuple[User, Session] = Depends(PermissionChecker.require_permission_with_db("employee_access"))
):
    # Unpack the tuple
    current_user, db = user_db_tuple
    """
    Get overtime request statistics.
    
    Requires employee_access permission.
    """
    try:
        data = DashboardService.get_overtime_request_stats(db)
        return {"overtime_stats": data}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching overtime stats: {str(e)}"
        )

# New admin‑only endpoints for top‑employee statistics
@router.get("/kpi/top-sick-leave")
def get_top_sick_leave(
    user_db_tuple: tuple[User, Session] = Depends(PermissionChecker.require_permission_with_db("admin_access"))
):
    # Unpack the tuple
    current_user, db = user_db_tuple
    """
    Return the top N employees with the most approved sick‑leave requests
    in the past 3 months (default N=10).
    """
    try:
        data = DashboardService.get_top_sick_leave(db)
        return {"top_sick_leave": data}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching top sick‑leave data: {str(e)}"
        )

@router.get("/kpi/top-absent")
def get_top_absent(
    user_db_tuple: tuple[User, Session] = Depends(PermissionChecker.require_permission_with_db("admin_access"))
):
    # Unpack the tuple
    current_user, db = user_db_tuple
    """
    Return the top N employees with the most absent days
    in the past 3 months (default N=10).
    """
    try:
        data = DashboardService.get_top_absent(db)
        return {"top_absent": data}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching top absent data: {str(e)}"
        )

@router.get("/kpi/top-tardy")
def get_top_tardy(
    user_db_tuple: tuple[User, Session] = Depends(PermissionChecker.require_permission_with_db("admin_access"))
):
    # Unpack the tuple
    current_user, db = user_db_tuple
    """
    Return the top N employees with the most late arrivals
    in the past 3 months (default N=10).
    """
    try:
        data = DashboardService.get_top_tardy(db)
        return {"top_tardy": data}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching top tardy data: {str(e)}"
        )

# Leave request management endpoints


@router.post("/leaves/{leave_id}/approve")
def approve_leave_request(
    leave_id: int,
    user_db_tuple: tuple[User, Session] = Depends(PermissionChecker.require_permission_with_db("admin_access"))
):
    # Unpack the tuple
    current_user, db = user_db_tuple
    """
    Approve a leave request.
    
    Requires admin_access permission.
    """
    try:
        leave_request = db.query(LeaveRequest).filter(
            LeaveRequest.leave_id == leave_id
        ).first()
        
        if not leave_request:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Leave request not found"
            )
        
        if leave_request.status != "Pending":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Leave request is not pending"
            )
        
        leave_request.status = "Approved"
        leave_request.approver_id = current_user.user_id
        leave_request.approved_at = datetime.utcnow()
        
        db.commit()
        
        return {"message": "Leave request approved successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error approving leave request: {str(e)}"
        )

@router.post("/leaves/{leave_id}/reject")
def reject_leave_request(
    leave_id: int,
    user_db_tuple: tuple[User, Session] = Depends(PermissionChecker.require_permission_with_db("admin_access"))
):
    # Unpack the tuple
    current_user, db = user_db_tuple
    """
    Reject a leave request.
    
    Requires admin_access permission.
    """
    try:
        leave_request = db.query(LeaveRequest).filter(
            LeaveRequest.leave_id == leave_id
        ).first()
        
        if not leave_request:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Leave request not found"
            )
        
        if leave_request.status != "Pending":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Leave request is not pending"
            )
        
        leave_request.status = "Rejected"
        leave_request.approver_id = current_user.user_id
        leave_request.approved_at = datetime.utcnow()
        
        db.commit()
        
        return {"message": "Leave request rejected successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error rejecting leave request: {str(e)}"
        )

# Overtime request management endpoints
@router.post("/overtime/{ot_id}/approve")
def approve_overtime_request(
    ot_id: int,
    user_db_tuple: tuple[User, Session] = Depends(PermissionChecker.require_permission_with_db("admin_access"))
):
    # Unpack the tuple
    current_user, db = user_db_tuple
    """
    Approve an overtime request.
    
    Requires admin_access permission.
    """
    try:
        overtime_request = db.query(OvertimeRequest).filter(
            OvertimeRequest.ot_id == ot_id
        ).first()
        
        if not overtime_request:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Overtime request not found"
            )
        
        if overtime_request.status != "Pending":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Overtime request is not pending"
            )
        
        overtime_request.status = "Approved"
        overtime_request.approver_id = current_user.user_id
        overtime_request.approved_at = datetime.utcnow()
        
        db.commit()
        
        return {"message": "Overtime request approved successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error approving overtime request: {str(e)}"
        )

@router.post("/overtime/{ot_id}/reject")
def reject_overtime_request(
    ot_id: int,
    user_db_tuple: tuple[User, Session] = Depends(PermissionChecker.require_permission_with_db("admin_access"))
):
    # Unpack the tuple
    current_user, db = user_db_tuple
    """
    Reject an overtime request.
    
    Requires admin_access permission.
    """
    try:
        overtime_request = db.query(OvertimeRequest).filter(
            OvertimeRequest.ot_id == ot_id
        ).first()
        
        if not overtime_request:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Overtime request not found"
            )
        
        if overtime_request.status != "Pending":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Overtime request is not pending"
            )
        
        overtime_request.status = "Rejected"
        overtime_request.approver_id = current_user.user_id
        overtime_request.approved_at = datetime.utcnow()
        
        db.commit()
        
        return {"message": "Overtime request rejected successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error rejecting overtime request: {str(e)}"
        )
@router.get("/kpi/top-leave")
def get_top_leave(
    user_db_tuple: tuple[User, Session] = Depends(PermissionChecker.require_permission_with_db("employee_access"))
):
    """
    Return the top N employees with the most approved leave requests
    in the past `months` months (default N=10).
    """
    try:
        # Unpack the tuple
        current_user, db = user_db_tuple
        data = DashboardService.get_top_leave(db)
        return {"top_leave": data}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching top leave data: {str(e)}"
        )