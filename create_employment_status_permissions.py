from backend.database import get_db
from backend.models import Permission, Role, RolePermission

db = next(get_db())

print('=== Creating Employment Status Permissions ===')

# Check if permissions exist
manage_perm = db.query(Permission).filter(Permission.permission_name == 'manage_employment_statuses').first()
view_perm = db.query(Permission).filter(Permission.permission_name == 'view_employment_statuses').first()

print(f'manage_employment_statuses: {manage_perm.permission_id if manage_perm else "NOT FOUND"}')
print(f'view_employment_statuses: {view_perm.permission_id if view_perm else "NOT FOUND"}')

# Create view permission if needed
if not view_perm:
    view_perm = Permission(
        permission_name='view_employment_statuses',
        description='View employment statuses'
    )
    db.add(view_perm)
    db.commit()
    db.refresh(view_perm)
    print(f'✅ Created view_employment_statuses permission: {view_perm.permission_id}')

# Create manage permission if needed
if not manage_perm:
    manage_perm = Permission(
        permission_name='manage_employment_statuses',
        description='Manage employment statuses'
    )
    db.add(manage_perm)
    db.commit()
    db.refresh(manage_perm)
    print(f'✅ Created manage_employment_statuses permission: {manage_perm.permission_id}')

# Get super_admin role
super_admin_role = db.query(Role).filter(Role.role_name == 'super_admin').first()
if not super_admin_role:
    print('ERROR: super_admin role not found')
else:
    print(f'Found super_admin role: {super_admin_role.role_id}')
    
    # Assign permissions to super_admin
    for perm in [view_perm, manage_perm]:
        if perm:  # Make sure permission exists
            existing = db.query(RolePermission).filter(
                RolePermission.role_id == super_admin_role.role_id,
                RolePermission.permission_id == perm.permission_id
            ).first()
            
            if not existing:
                new_assignment = RolePermission(
                    role_id=super_admin_role.role_id,
                    permission_id=perm.permission_id
                )
                db.add(new_assignment)
                print(f'✅ Assigned {perm.permission_name} to super_admin')
            else:
                print(f'{perm.permission_name} already assigned to super_admin')

db.commit()
print('All employment status permissions are now properly set up!')

db.close()