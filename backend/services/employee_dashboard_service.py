"""
Employee Dashboard Service

Provides business logic for employee-specific dashboard data and personal metrics.
"""

from sqlalchemy import func, and_, or_, extract
from sqlalchemy.orm import Session
from datetime import datetime, date, timedelta
from typing import List, Dict, Any, Optional
from backend.models import (
    User, Attendance, LeaveRequest, OvertimeRequest, Payroll,
    AttendanceStatus, LeaveStatus, OvertimeStatus, Payslip, LeaveType
)


class EmployeeDashboardService:
    """
    Service class for employee-specific dashboard operations and personal metrics calculations.
    """
    
    @staticmethod
    def get_days_worked_this_month(db: Session, user_id: int) -> int:
        """
        Get the number of days worked by the employee this month.
        
        Args:
            db: Database session
            user_id: ID of the employee
            
        Returns:
            int: Number of days worked this month
        """
        today = datetime.utcnow().date()
        first_day_of_month = today.replace(day=1)
        
        # Count days marked as Present or Overtime this month
        days_worked = db.query(Attendance).filter(
            and_(
                Attendance.user_id == user_id,
                Attendance.date >= first_day_of_month,
                Attendance.date <= today,
                Attendance.status.in_([AttendanceStatus.Present.value, AttendanceStatus.Overtime.value])
            )
        ).count()
        
        return days_worked
    
    @staticmethod
    def get_remaining_leave_balance(db: Session, user_id: int) -> Dict[str, int]:
        """
        Get remaining leave balance by leave type for the employee.
        
        Args:
            db: Database session
            user_id: ID of the employee
            
        Returns:
            Dict[str, int]: Dictionary with leave type names and remaining balances
        """
        # Get employee's leave requests for the current year
        today = datetime.utcnow().date()
        first_day_of_year = today.replace(month=1, day=1)
        
        # Get all approved leave requests for this year
        approved_leaves = db.query(LeaveRequest).filter(
            and_(
                LeaveRequest.user_id == user_id,
                LeaveRequest.date_from >= first_day_of_year,
                LeaveRequest.status == LeaveStatus.Approved.value
            )
        ).all()
        
        # Calculate days taken for each leave type
        leave_balances = {}
        for leave in approved_leaves:
            leave_type_name = leave.leave_type.leave_name
            days_taken = (leave.date_to - leave.date_from).days + 1  # Include both start and end dates
            
            if leave_type_name in leave_balances:
                leave_balances[leave_type_name] += days_taken
            else:
                leave_balances[leave_type_name] = days_taken
        
        # Get default allocations and subtract used days
        leave_types = db.query(LeaveType).all()
        for leave_type in leave_types:
            type_name = leave_type.leave_name
            default_allocation = leave_type.default_allocation
            used_days = leave_balances.get(type_name, 0)
            remaining = max(0, default_allocation - used_days)
            
            leave_balances[type_name] = remaining
        
        return leave_balances
    
    @staticmethod
    def get_total_overtime_hours_this_month(db: Session, user_id: int) -> float:
        """
        Get total overtime hours worked by the employee this month.
        
        Args:
            db: Database session
            user_id: ID of the employee
            
        Returns:
            float: Total overtime hours this month
        """
        today = datetime.utcnow().date()
        first_day_of_month = today.replace(day=1)
        
        # Get overtime hours from attendance records
        overtime_attendance = db.query(Attendance).filter(
            and_(
                Attendance.user_id == user_id,
                Attendance.date >= first_day_of_month,
                Attendance.date <= today,
                Attendance.status == AttendanceStatus.Overtime.value
            )
        ).all()
        
        total_overtime = 0.0
        for record in overtime_attendance:
            if record.hours_worked:
                total_overtime += float(record.hours_worked)
        
        # Also get approved overtime requests
        approved_overtime_requests = db.query(OvertimeRequest).filter(
            and_(
                OvertimeRequest.user_id == user_id,
                OvertimeRequest.date >= first_day_of_month,
                OvertimeRequest.date <= today,
                OvertimeRequest.status == OvertimeStatus.Approved.value
            )
        ).all()
        
        for request in approved_overtime_requests:
            total_overtime += float(request.hours_requested)
        
        return round(total_overtime, 2)
    
    @staticmethod
    def get_latest_payslip(db: Session, user_id: int) -> Optional[Dict[str, Any]]:
        """
        Get the latest payslip information for the employee.
        
        Args:
            db: Database session
            user_id: ID of the employee
            
        Returns:
            Optional[Dict[str, Any]]: Latest payslip information or None
        """
        # Get the most recent payroll record
        latest_payroll = db.query(Payroll).filter(
            Payroll.user_id == user_id
        ).order_by(Payroll.cutoff_end.desc()).first()
        
        if not latest_payroll:
            return None
        
        # Get associated payslip if exists
        payslip = db.query(Payslip).filter(
            Payslip.payroll_id == latest_payroll.payroll_id
        ).first()
        
        return {
            "payroll_id": latest_payroll.payroll_id,
            "cutoff_start": latest_payroll.cutoff_start.strftime("%Y-%m-%d"),
            "cutoff_end": latest_payroll.cutoff_end.strftime("%Y-%m-%d"),
            "basic_pay": float(latest_payroll.basic_pay),
            "overtime_pay": float(latest_payroll.overtime_pay),
            "deductions": float(latest_payroll.deductions),
            "net_pay": float(latest_payroll.net_pay),
            "generated_at": latest_payroll.generated_at.strftime("%Y-%m-%d %H:%M:%S"),
            "payslip_id": payslip.payslip_id if payslip else None,
            "file_path": payslip.file_path if payslip else None
        }
    
    @staticmethod
    def get_attendance_summary_current_month(db: Session, user_id: int) -> List[Dict[str, Any]]:
        """
        Get attendance summary for the current month (hours worked per day).
        
        Args:
            db: Database session
            user_id: ID of the employee
            
        Returns:
            List[Dict[str, Any]]: List of daily attendance records
        """
        today = datetime.utcnow().date()
        first_day_of_month = today.replace(day=1)
        
        # Get attendance records for the current month
        attendance_records = db.query(Attendance).filter(
            and_(
                Attendance.user_id == user_id,
                Attendance.date >= first_day_of_month,
                Attendance.date <= today
            )
        ).order_by(Attendance.date.desc()).all()
        
        # Format data for chart
        result = []
        for record in attendance_records:
            result.append({
                "date": record.date.strftime("%Y-%m-%d"),
                "hours_worked": float(record.hours_worked) if record.hours_worked else 0,
                "status": record.status
            })
        
        return result
    
    @staticmethod
    def get_personal_attendance_log(db: Session, user_id: int, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get personal attendance log (recent records).
        
        Args:
            db: Database session
            user_id: ID of the employee
            limit: Maximum number of records to return
            
        Returns:
            List[Dict[str, Any]]: List of recent attendance records
        """
        # Get recent attendance records
        attendance_records = db.query(Attendance).filter(
            Attendance.user_id == user_id
        ).order_by(Attendance.date.desc()).limit(limit).all()
        
        # Format data for table
        result = []
        for record in attendance_records:
            result.append({
                "attendance_id": record.attendance_id,
                "date": record.date.strftime("%Y-%m-%d"),
                "time_in": record.time_in.strftime("%H:%M:%S") if record.time_in else None,
                "time_out": record.time_out.strftime("%H:%M:%S") if record.time_out else None,
                "hours_worked": float(record.hours_worked) if record.hours_worked else None,
                "status": record.status
            })
        
        return result
    
    @staticmethod
    def get_personal_leave_request_history(db: Session, user_id: int, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get personal leave request history.
        
        Args:
            db: Database session
            user_id: ID of the employee
            limit: Maximum number of records to return
            
        Returns:
            List[Dict[str, Any]]: List of leave request history
        """
        # Get recent leave requests
        leave_requests = db.query(LeaveRequest).filter(
            LeaveRequest.user_id == user_id
        ).order_by(LeaveRequest.date_from.desc()).limit(limit).all()
        
        # Format data for table
        result = []
        for request in leave_requests:
            # Get approver name if exists
            approver_name = "Not Assigned"
            if request.approver:
                approver_name = f"{request.approver.first_name} {request.approver.last_name}"
            
            result.append({
                "leave_id": request.leave_id,
                "leave_type": request.leave_type.leave_name,
                "date_from": request.date_from.strftime("%Y-%m-%d"),
                "date_to": request.date_to.strftime("%Y-%m-%d"),
                "days_requested": (request.date_to - request.date_from).days + 1,
                "reason": request.reason[:100] + "..." if len(request.reason) > 100 else request.reason,
                "status": request.status,
                "approver": approver_name,
                "approved_at": request.approved_at.strftime("%Y-%m-%d %H:%M:%S") if request.approved_at else None
            })
        
        return result
    
    @staticmethod
    def get_personal_overtime_request_history(db: Session, user_id: int, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get personal overtime request history.
        
        Args:
            db: Database session
            user_id: ID of the employee
            limit: Maximum number of records to return
            
        Returns:
            List[Dict[str, Any]]: List of overtime request history
        """
        # Get recent overtime requests
        overtime_requests = db.query(OvertimeRequest).filter(
            OvertimeRequest.user_id == user_id
        ).order_by(OvertimeRequest.date.desc()).limit(limit).all()
        
        # Format data for table
        result = []
        for request in overtime_requests:
            # Get approver name if exists
            approver_name = "Not Assigned"
            if request.approver:
                approver_name = f"{request.approver.first_name} {request.approver.last_name}"
            
            result.append({
                "ot_id": request.ot_id,
                "date": request.date.strftime("%Y-%m-%d"),
                "hours_requested": float(request.hours_requested),
                "reason": request.reason[:100] + "..." if len(request.reason) > 100 else request.reason,
                "status": request.status,
                "approver": approver_name,
                "approved_at": request.approved_at.strftime("%Y-%m-%d %H:%M:%S") if request.approved_at else None
            })
        
        return result
    
    @staticmethod
    def get_personal_payroll_history(db: Session, user_id: int, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get personal payroll history.
        
        Args:
            db: Database session
            user_id: ID of the employee
            limit: Maximum number of records to return
            
        Returns:
            List[Dict[str, Any]]: List of payroll history
        """
        # Get recent payroll records
        payroll_records = db.query(Payroll).filter(
            Payroll.user_id == user_id
        ).order_by(Payroll.cutoff_end.desc()).limit(limit).all()
        
        # Format data for table
        result = []
        for record in payroll_records:
            result.append({
                "payroll_id": record.payroll_id,
                "cutoff_start": record.cutoff_start.strftime("%Y-%m-%d"),
                "cutoff_end": record.cutoff_end.strftime("%Y-%m-%d"),
                "basic_pay": float(record.basic_pay),
                "overtime_pay": float(record.overtime_pay),
                "deductions": float(record.deductions),
                "net_pay": float(record.net_pay),
                "generated_at": record.generated_at.strftime("%Y-%m-%d %H:%M:%S")
            })
        
        return result