"""
Dashboard Service

Provides business logic for dashboard KPI calculations and analytics.
"""

from sqlalchemy import func, and_, or_
from sqlalchemy.orm import Session
from datetime import datetime, date, timedelta
from typing import List, Dict, Any, Optional
from ..models import (
    User, Attendance, LeaveRequest, OvertimeRequest, Payroll, 
    AttendanceStatus, LeaveStatus, OvertimeStatus
)


class DashboardService:
    """
    Service class for dashboard operations and KPI calculations.
    """
    
    @staticmethod
    def get_employees_present_today(db: Session) -> int:
        """
        Get count of employees present today.
        
        Args:
            db: Database session
            
        Returns:
            int: Number of employees present today
        """
        today = datetime.utcnow().date()
        
        # Get employees marked as Present or On Leave today
        present_count = db.query(Attendance).filter(
            and_(
                Attendance.date == today,
                Attendance.status.in_([AttendanceStatus.Present.value, AttendanceStatus.Overtime.value])
            )
        ).count()
        
        # Add employees on leave today
        on_leave_count = db.query(LeaveRequest).filter(
            and_(
                LeaveRequest.date_from <= today,
                LeaveRequest.date_to >= today,
                LeaveRequest.status == LeaveStatus.Approved.value
            )
        ).count()
        
        return present_count + on_leave_count
    
    @staticmethod
    def get_late_absent_today(db: Session) -> Dict[str, int]:
        """
        Get count of late and absent employees today.
        
        Args:
            db: Database session
            
        Returns:
            Dict[str, int]: Dictionary with 'late' and 'absent' counts
        """
        today = datetime.utcnow().date()
        
        late_count = db.query(Attendance).filter(
            and_(
                Attendance.date == today,
                Attendance.status == AttendanceStatus.Late.value
            )
        ).count()
        
        absent_count = db.query(Attendance).filter(
            and_(
                Attendance.date == today,
                Attendance.status == AttendanceStatus.Absent.value
            )
        ).count()
        
        return {
            "late": late_count,
            "absent": absent_count
        }
    
    @staticmethod
    def get_pending_leave_requests(db: Session) -> int:
        """
        Get count of pending leave requests.
        
        Args:
            db: Database session
            
        Returns:
            int: Number of pending leave requests
        """
        return db.query(LeaveRequest).filter(
            LeaveRequest.status == LeaveStatus.Pending.value
        ).count()
    
    @staticmethod
    def get_pending_overtime_requests(db: Session) -> int:
        """
        Get count of pending overtime requests.
        
        Args:
            db: Database session
            
        Returns:
            int: Number of pending overtime requests
        """
        return db.query(OvertimeRequest).filter(
            OvertimeRequest.status == OvertimeStatus.Pending.value
        ).count()
    
    @staticmethod
    def get_attendance_overview(db: Session) -> List[Dict[str, Any]]:
        """
        Get attendance data for the last 7 days for bar chart.
        
        Args:
            db: Database session
            
        Returns:
            List[Dict[str, Any]]: List of attendance data for each day
        """
        today = datetime.utcnow().date()
        seven_days_ago = today - timedelta(days=6)
        
        # Query attendance data for the last 7 days (simplified approach)
        attendance_data = []
        for single_date in [seven_days_ago + timedelta(days=i) for i in range(7)]:
            # Get total count for this date
            total_count = db.query(Attendance).filter(
                Attendance.date == single_date
            ).count()
            
            # Get present count for this date
            present_count = db.query(Attendance).filter(
                and_(
                    Attendance.date == single_date,
                    Attendance.status == 'Present'
                )
            ).count()
            
            # Get late count for this date
            late_count = db.query(Attendance).filter(
                and_(
                    Attendance.date == single_date,
                    Attendance.status == 'Late'
                )
            ).count()
            
            # Get absent count for this date
            absent_count = db.query(Attendance).filter(
                and_(
                    Attendance.date == single_date,
                    Attendance.status == 'Absent'
                )
            ).count()
            
            if total_count > 0:
                attendance_data.append({
                    'date': single_date,
                    'total': total_count,
                    'present': present_count,
                    'late': late_count,
                    'absent': absent_count
                })
        
        # Format data for chart
        result = []
        for data in attendance_data:
            result.append({
                "date": data['date'].strftime("%Y-%m-%d"),
                "total": int(data['total']),
                "present": int(data['present']),
                "late": int(data['late']),
                "absent": int(data['absent'])
            })
        
        return result
    
    @staticmethod
    def get_today_attendance_table(db: Session) -> List[Dict[str, Any]]:
        """
        Get today's attendance table data.
        
        Args:
            db: Database session
            
        Returns:
            List[Dict[str, Any]]: List of attendance records for today
        """
        today = datetime.utcnow().date()
        
        attendance_records = db.query(
            Attendance,
            User.first_name,
            User.last_name,
            User.email
        ).join(
            User, Attendance.user_id == User.user_id
        ).filter(
            Attendance.date == today
        ).order_by(Attendance.time_in).all()
        
        # Format data for table
        result = []
        for record in attendance_records:
            # The record is a tuple-like object where:
            # record[0] = Attendance object
            # record[1] = User.first_name
            # record[2] = User.last_name
            # record[3] = User.email
            attendance_obj = record[0]
            result.append({
                "attendance_id": attendance_obj.attendance_id,
                "user_id": attendance_obj.user_id,
                "name": f"{record[1]} {record[2]}",
                "email": record[3],
                "date": attendance_obj.date.strftime("%Y-%m-%d"),
                "time_in": attendance_obj.time_in.strftime("%H:%M:%S") if attendance_obj.time_in else None,
                "time_out": attendance_obj.time_out.strftime("%H:%M:%S") if attendance_obj.time_out else None,
                "hours_worked": float(attendance_obj.hours_worked) if attendance_obj.hours_worked else None,
                "status": attendance_obj.status
            })
        
        return result
    
    @staticmethod
    def get_payroll_summary(db: Session) -> Dict[str, Any]:
        """
        Get payroll summary data.
        
        Args:
            db: Database session
            
        Returns:
            Dict[str, Any]: Payroll summary statistics
        """
        # Get current month's payroll data
        today = datetime.utcnow().date()
        first_day_of_month = today.replace(day=1)
        
        payroll_data = db.query(
            func.count(Payroll.payroll_id).label('total_payrolls'),
            func.sum(Payroll.basic_pay).label('total_basic_pay'),
            func.sum(Payroll.overtime_pay).label('total_overtime_pay'),
            func.sum(Payroll.deductions).label('total_deductions'),
            func.sum(Payroll.net_pay).label('total_net_pay')
        ).filter(
            Payroll.cutoff_start >= first_day_of_month
        ).first()
        
        return {
            "total_payrolls": int(payroll_data.total_payrolls) if payroll_data.total_payrolls else 0,
            "total_basic_pay": float(payroll_data.total_basic_pay) if payroll_data.total_basic_pay else 0,
            "total_overtime_pay": float(payroll_data.total_overtime_pay) if payroll_data.total_overtime_pay else 0,
            "total_deductions": float(payroll_data.total_deductions) if payroll_data.total_deductions else 0,
            "total_net_pay": float(payroll_data.total_net_pay) if payroll_data.total_net_pay else 0
        }
    
    @staticmethod
    def get_leave_request_stats(db: Session) -> Dict[str, int]:
        """
        Get leave request statistics.
        
        Args:
            db: Database session
            
        Returns:
            Dict[str, int]: Dictionary with leave request counts by status
        """
        stats = {}
        
        for status in LeaveStatus:
            count = db.query(LeaveRequest).filter(
                LeaveRequest.status == status.value
            ).count()
            stats[status.value.lower()] = count
        
        return stats
    
    @staticmethod
    def get_overtime_request_stats(db: Session) -> Dict[str, int]:
        """
        Get overtime request statistics.
        
        Args:
            db: Database session
            
        Returns:
            Dict[str, int]: Dictionary with overtime request counts by status
        """
        stats = {}
        
        for status in OvertimeStatus:
            count = db.query(OvertimeRequest).filter(
                OvertimeRequest.status == status.value
            ).count()
            stats[status.value.lower()] = count
        
        return stats