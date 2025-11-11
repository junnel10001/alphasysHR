import random
import datetime
from sqlalchemy.orm import Session
from backend import models

def run(db: Session):
    """
    Create payroll records for the last two pay periods for each user.
    Pay periods are defined as the first half and second half of the current month.
    """
    users = db.query(models.User).all()
    if not users:
        print("No users found – ensure seed_users runs first.")
        return

    today = datetime.date.today()
    # Define two cut‑off periods for the current month
    first_start = today.replace(day=1)
    first_end = first_start + datetime.timedelta(days=14)
    second_start = first_end + datetime.timedelta(days=1)
    second_end = (first_start + datetime.timedelta(days=31)).replace(day=1) - datetime.timedelta(days=1)

    periods = [(first_start, first_end), (second_start, second_end)]

    for user in users:
        for start, end in periods:
            # Basic pay: hourly_rate * random hours (80‑100 hrs per period)
            hours = random.uniform(80, 100)
            basic_pay = round(float(user.hourly_rate) * hours, 2)

            overtime_pay = round(random.uniform(0, 200), 2)
            deductions = round(random.uniform(0, 100), 2)
            net_pay = round(basic_pay + overtime_pay - deductions, 2)

            payroll = models.Payroll(
                user_id=user.user_id,
                cutoff_start=start,
                cutoff_end=end,
                basic_pay=basic_pay,
                overtime_pay=overtime_pay,
                deductions=deductions,
                net_pay=net_pay,
            )
            db.add(payroll)

    db.commit()
    print("Payroll records seeded.")