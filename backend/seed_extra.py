from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from backend.models import Attendance, AttendanceStatus, OvertimeRequest, OvertimeStatus, LeaveRequest, LeaveStatus, User
import random

def seed_late_arrivals(db: Session):
    """Seed late arrival records for yesterday and today."""
    today = datetime.utcnow().date()
    yesterday = today - timedelta(days=1)

    # Ensure there are users
    users = db.query(User).limit(20).all()
    if not users:
        return

    for user in users:
        # Yesterday late
        db.add(Attendance(
            user_id=user.user_id,
            date=yesterday,
            status=AttendanceStatus.Late.value,
            time_in=datetime.combine(yesterday, datetime.min.time()) + timedelta(hours=9, minutes=random.randint(1, 30))
        ))
        # Today late
        db.add(Attendance(
            user_id=user.user_id,
            date=today,
            status=AttendanceStatus.Late.value,
            time_in=datetime.combine(today, datetime.min.time()) + timedelta(hours=9, minutes=random.randint(1, 30))
        ))
    db.commit()

def seed_sick_leave(db: Session):
    """Seed sick leave requests for yesterday and today."""
    today = datetime.utcnow().date()
    yesterday = today - timedelta(days=1)

    users = db.query(User).limit(20).all()
    if not users:
        return

    for user in users:
        # Yesterday sick leave (approved)
        db.add(LeaveRequest(
            user_id=user.user_id,
            leave_type_id=1,  # assume leave_type_id 1 is Sick Leave
            date_from=yesterday,
            date_to=yesterday,
            status=LeaveStatus.Approved.value,
            approved_at=datetime.utcnow()
        ))
        # Today sick leave (pending)
        db.add(LeaveRequest(
            user_id=user.user_id,
            leave_type_id=1,
            date_from=today,
            date_to=today,
            status=LeaveStatus.Pending.value
        ))
    db.commit()

def seed_overtime_stats(db: Session):
    """Seed overtime request records for the last 30 days."""
    today = datetime.utcnow().date()
    for i in range(30):
        day = today - timedelta(days=i)
        users = db.query(User).limit(5).all()
        for user in users:
            db.add(OvertimeRequest(
                user_id=user.user_id,
                date=day,
                hours_requested=round(random.uniform(1, 4), 2),
                status=random.choice([OvertimeStatus.Pending.value,
                                      OvertimeStatus.Approved.value,
                                      OvertimeStatus.Rejected.value])
            ))
    db.commit()

def seed_top_employee_stats(db: Session):
    """Create dummy approved leave requests for top‑leave chart."""
    # Ensure we have at least 5 users
    users = db.query(User).limit(5).all()
    if not users:
        return

    # Use leave_type_id 1 (Sick Leave) – assume it exists
    for i, user in enumerate(users, start=1):
        # Create a varying number of approved leaves per user
        for _ in range(i * 2):  # user 1 -> 2 leaves, user 2 -> 4, etc.
            db.add(
                LeaveRequest(
                    user_id=user.user_id,
                    leave_type_id=1,
                    date_from=datetime.utcnow().date() - timedelta(days=30),
                    date_to=datetime.utcnow().date() - timedelta(days=30),
                    status=LeaveStatus.Approved.value,
                )
            )
    db.commit()