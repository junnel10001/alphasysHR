from sqlalchemy.orm import Session
from backend import models

def run(db: Session):
    # Roles (avoid duplicates)
    admin_role = db.query(models.Role).filter_by(role_name="admin").first()
    if not admin_role:
        admin_role = models.Role(role_name="admin", description="Administrator")
        db.add(admin_role)
        db.flush()

    employee_role = db.query(models.Role).filter_by(role_name="employee").first()
    if not employee_role:
        employee_role = models.Role(role_name="employee", description="Regular employee")
        db.add(employee_role)
        db.flush()

    # Permissions (avoid duplicates)
    permission_names = [
        "view_dashboard",
        "manage_users",
        "manage_attendance",
        "manage_leave",
        "manage_overtime",
        "view_reports",
    ]
    permission_objs = []
    for name in permission_names:
        perm = db.query(models.Permission).filter_by(permission_name=name).first()
        if not perm:
            perm = models.Permission(
                permission_name=name,
                description=f"Permission to {name.replace('_', ' ')}",
            )
            db.add(perm)
            db.flush()
        permission_objs.append(perm)

    # Role-Permissions (avoid duplicate entries)
    for role in (admin_role, employee_role):
        for perm in permission_objs:
            exists = (
                db.query(models.RolePermission)
                .filter_by(role_id=role.role_id, permission_id=perm.permission_id)
                .first()
            )
            if not exists:
                rp = models.RolePermission(
                    role_id=role.role_id, permission_id=perm.permission_id
                )
                db.add(rp)

    # Departments (avoid duplicates)
    department_names = [
        "Human Resources",
        "Finance",
        "Engineering",
        "Sales",
        "Marketing",
    ]
    for name in department_names:
        dept = db.query(models.Department).filter_by(department_name=name).first()
        if not dept:
            dept = models.Department(department_name=name)
            db.add(dept)

    db.commit()
    print("Roles, permissions, and departments seeded.")