import random
import datetime
from sqlalchemy.orm import Session
from backend import models

def run(db: Session):
    """
    Generate realistic attendance records for the past 30 days for each user.
    """
    users = db.query(models.User).all()
    if not users:
        print("No users found – ensure seed_users runs first.")
        return

    today = datetime.date.today()
    start_date = today - datetime.timedelta(days=30)

    attendance_statuses = [
        ("Present", 0.70),
        ("Late", 0.10),
        ("Absent", 0.05),
        ("On Leave", 0.10),
        ("Overtime", 0.05),
    ]

    for user in users:
        for day_offset in range(31):
            att_date = start_date + datetime.timedelta(days=day_offset)
            # Choose status based on weighted probabilities
            rnd = random.random()
            cumulative = 0.0
            status = "Present"
            for s, prob in attendance_statuses:
                cumulative += prob
                if rnd <= cumulative:
                    status = s
                    break

            time_in = None
            time_out = None
            hours_worked = None

            if status in ("Present", "Late", "Overtime"):
                # Assume work day starts between 8:30 and 9:30
                in_hour = random.randint(8, 9)
                in_minute = random.randint(0, 59)
                time_in_dt = datetime.datetime.combine(att_date, datetime.time(in_hour, in_minute))
                # Work duration 8-9 hours
                work_hours = random.uniform(8, 9)
                time_out_dt = time_in_dt + datetime.timedelta(hours=work_hours)
                time_in = time_in_dt
                time_out = time_out_dt
                hours_worked = round(work_hours, 2)

                if status == "Late":
                    # Push time_in by 30-60 minutes
                    time_in += datetime.timedelta(minutes=random.randint(30, 60))
                if status == "Overtime":
                    # Add extra 1-3 hours
                    extra = random.uniform(1, 3)
                    time_out += datetime.timedelta(hours=extra)
                    hours_worked = round(work_hours + extra, 2)

            attendance = models.Attendance(
                user_id=user.user_id,
                date=att_date,
                time_in=time_in,
                time_out=time_out,
                hours_worked=hours_worked,
                status=status,
            )
            db.add(attendance)

    db.commit()
    print("Attendance records seeded.")