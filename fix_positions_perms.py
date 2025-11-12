from backend.database import get_db
from backend.models import Permission, Role, RolePermission, User

db = next(get_db())

# Get current user (now super_admin)
current_user = db.query(User).filter(User.username == 'junnel@alphasys.com.au').first()
if current_user:
    print('Current user: ' + current_user.username + ', Role: ' + current_user.role_name + ', Role ID: ' + str(current_user.role_id))

# Get positions permissions
view_perm = db.query(Permission).filter(Permission.permission_name == 'view_positions').first()
manage_perm = db.query(Permission).filter(Permission.permission_name == 'manage_positions').first()

# Check if super_admin role has positions permissions
super_admin_role = db.query(Role).filter(Role.role_name == 'super_admin').first()
if super_admin_role:
    print('\nSuper admin role ID: ' + str(super_admin_role.role_id))
    
    super_admin_view_perm = db.query(RolePermission).filter(
        RolePermission.role_id == super_admin_role.role_id,
        RolePermission.permission_id == view_perm.permission_id
    ).first()
    
    super_admin_manage_perm = db.query(RolePermission).filter(
        RolePermission.role_id == super_admin_role.role_id,
        RolePermission.permission_id == manage_perm.permission_id
    ).first()
    
    print('Super admin role has view_positions permission: ' + ('Yes' if super_admin_view_perm else 'No'))
    print('Super admin role has manage_positions permission: ' + ('Yes' if super_admin_manage_perm else 'No'))

# If super_admin doesn't have positions permissions, assign them
if not super_admin_view_perm or not super_admin_manage_perm:
    print('\nAdding missing positions permissions to super_admin role...')
    
    if not super_admin_view_perm:
        new_perm = RolePermission(role_id=super_admin_role.role_id, permission_id=view_perm.permission_id)
        db.add(new_perm)
        print('Added view_positions permission')
        
    if not super_admin_manage_perm:
        new_perm = RolePermission(role_id=super_admin_role.role_id, permission_id=manage_perm.permission_id)
        db.add(new_perm)
        print('Added manage_positions permission')
    
    db.commit()
    print('Permissions assigned successfully!')

db.close()