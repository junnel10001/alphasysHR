from backend.database import get_db
from backend.models import Permission, Role, RolePermission, User

db = next(get_db())

# Get current user
current_user = db.query(User).filter(User.username == 'junnel@alphasys.com.au').first()
if current_user:
    print(f'Current user: {current_user.username}, Role: {current_user.role_name}, Role ID: {current_user.role_id}')

# Get positions permissions
view_perm = db.query(Permission).filter(Permission.permission_name == 'view_positions').first()
manage_perm = db.query(Permission).filter(Permission.permission_name == 'manage_positions').first()

# Check if admin role has positions permissions
admin_role = db.query(Role).filter(Role.role_name == 'admin').first()
if admin_role:
    print(f'\nAdmin role ID: {admin_role.role_id}')
    
    admin_view_perm = db.query(RolePermission).filter(
        RolePermission.role_id == admin_role.role_id,
        RolePermission.permission_id == view_perm.permission_id
    ).first()
    
    admin_manage_perm = db.query(RolePermission).filter(
        RolePermission.role_id == admin_role.role_id,
        RolePermission.permission_id == manage_perm.permission_id
    ).first()
    
    print(f'Admin role has view_positions permission: {"Yes" if admin_view_perm else "No"}')
    print(f'Admin role has manage_positions permission: {"Yes" if admin_manage_perm else "No"}')

# List all role permissions for admin role
admin_role_perms = db.query(RolePermission).filter(RolePermission.role_id == admin_role.role_id).all()
print('\nAll admin role permissions:')
for rp in admin_role_perms:
    perm = db.query(Permission).filter(Permission.permission_id == rp.permission_id).first()
    print(f'  Role {rp.role_id} -> Permission {rp.permission_id} ({perm.permission_name})')

db.close()