import random
import datetime
from sqlalchemy.orm import Session
from backend import models

def run(db: Session):
    """
    Generate overtime request records for each user.
    Creates a mix of statuses: Pending, Approved, Rejected.
    """
    users = db.query(models.User).all()
    if not users:
        print("No users found – ensure seed_users runs first.")
        return

    status_choices = [
        ("Pending", 0.5),
        ("Approved", 0.3),
        ("Rejected", 0.2),
    ]

    for user in users:
        # each user gets 1-3 overtime requests
        for _ in range(random.randint(1, 3)):
            # random date within last 60 days
            req_date = datetime.date.today() - datetime.timedelta(days=random.randint(0, 60))
            hours_requested = round(random.uniform(1, 5), 2)

            # choose status based on weighted probabilities
            rnd = random.random()
            cumulative = 0.0
            status = "Pending"
            for s, prob in status_choices:
                cumulative += prob
                if rnd <= cumulative:
                    status = s
                    break

            overtime_req = models.OvertimeRequest(
                user_id=user.user_id,
                date=req_date,
                hours_requested=hours_requested,
                reason="Automated dummy overtime request",
                status=status,
                approver_id=None,
                approved_at=None,
            )
            db.add(overtime_req)

    db.commit()
    print("Overtime request records seeded.")