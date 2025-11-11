from backend.database import SessionLocal
from backend import models

db = SessionLocal()
print("Users:", db.query(models.User).count())
print("Attendance records:", db.query(models.Attendance).count())
print("Leave requests:", db.query(models.LeaveRequest).count())
print("Overtime requests:", db.query(models.OvertimeRequest).count())
print("Payroll entries:", db.query(models.Payroll).count())
db.close()