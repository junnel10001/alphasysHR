import random
import datetime
from sqlalchemy.orm import Session
from backend import models

def run(db: Session):
    """
    Generate leave request records for each user.
    Creates a mix of statuses: Pending, Approved, Rejected, Cancelled.
    """
    users = db.query(models.User).all()
    leave_types = db.query(models.LeaveType).all()
    if not users or not leave_types:
        print("No users or leave types found – ensure seed_users and seed_leave_types run first.")
        return

    status_choices = [
        ("Pending", 0.4),
        ("Approved", 0.3),
        ("Rejected", 0.2),
        ("Cancelled", 0.1),
    ]

    for user in users:
        # each user gets 2-4 leave requests
        for _ in range(random.randint(2, 4)):
            # pick a leave type
            lt = random.choice(leave_types)
            # random start date within last 60 days
            start_date = datetime.date.today() - datetime.timedelta(days=random.randint(0, 60))
            # duration 1-5 days
            duration = datetime.timedelta(days=random.randint(1, 5))
            end_date = start_date + duration

            # choose status based on weighted probabilities
            rnd = random.random()
            cumulative = 0.0
            status = "Pending"
            for s, prob in status_choices:
                cumulative += prob
                if rnd <= cumulative:
                    status = s
                    break

            leave_req = models.LeaveRequest(
                user_id=user.user_id,
                leave_type_id=lt.leave_type_id,
                date_from=start_date,
                date_to=end_date,
                reason="Automated dummy leave request",
                status=status,
                approver_id=None,
                approved_at=None,
            )
            db.add(leave_req)

    db.commit()
    print("Leave request records seeded.")