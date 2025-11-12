#!/usr/bin/env python3
"""
Configure Super-Admin Role and Permissions

This script creates a super_admin role with all available permissions
and assigns it to specified users.
"""

from backend.database import SessionLocal
from backend.models import User, Role, Permission, RolePermission
from backend.utils.rbac import RBACUtils

def create_super_admin_role(db):
    """Create super_admin role if it doesn't exist."""
    existing_role = db.query(Role).filter(Role.role_name == 'super_admin').first()
    if existing_role:
        print(f"Super-admin role already exists (ID: {existing_role.role_id})")
        return existing_role
    
    super_admin_role = Role(
        role_name='super_admin',
        description='Super administrator with full system access and control'
    )
    db.add(super_admin_role)
    db.commit()
    db.refresh(super_admin_role)
    print(f"Created super_admin role (ID: {super_admin_role.role_id})")
    return super_admin_role

def assign_all_permissions_to_super_admin(db, super_admin_role):
    """Assign all available permissions to super_admin role."""
    # Get all permissions
    all_permissions = db.query(Permission).all()
    
    assigned_count = 0
    for permission in all_permissions:
        # Check if already assigned
        existing = db.query(RolePermission).filter(
            RolePermission.role_id == super_admin_role.role_id,
            RolePermission.permission_id == permission.permission_id
        ).first()
        
        if not existing:
            role_permission = RolePermission(
                role_id=super_admin_role.role_id,
                permission_id=permission.permission_id
            )
            db.add(role_permission)
            assigned_count += 1
    
    db.commit()
    print(f"Assigned {assigned_count} permissions to super_admin role")

def assign_super_admin_to_user(db, username):
    """Assign super_admin role to a specific user."""
    user = db.query(User).filter(User.username == username).first()
    if not user:
        # Try by email
        user = db.query(User).filter(User.email == username).first()
    
    if not user:
        print(f"User '{username}' not found")
        return False
    
    super_admin_role = db.query(Role).filter(Role.role_name == 'super_admin').first()
    if not super_admin_role:
        print("Super-admin role not found")
        return False
    
    # Update user to have super_admin role
    user.role_id = super_admin_role.role_id
    user.role_name = 'super_admin'
    db.commit()
    
    print(f"Assigned super_admin role to user '{username}' (User ID: {user.user_id})")
    return True

def main():
    """Main execution function."""
    db = SessionLocal()
    
    try:
        print("🔧 Configuring Super-Admin Role and Permissions...")
        
        # Step 1: Ensure all default permissions exist
        print("\n📋 Step 1: Seeding default permissions...")
        created_permissions = RBACUtils.seed_default_permissions(db)
        print(f"Created {len(created_permissions)} new permissions")
        
        # Step 2: Create super_admin role
        print("\n👑 Step 2: Creating super_admin role...")
        super_admin_role = create_super_admin_role(db)
        
        # Step 3: Assign all permissions to super_admin role
        print("\n🔐 Step 3: Assigning all permissions to super_admin role...")
        assign_all_permissions_to_super_admin(db, super_admin_role)
        
        # Step 4: Assign super_admin role to admin users
        print("\n👤 Step 4: Assigning super_admin role to existing admin users...")
        
        # Get users with admin role
        admin_users = db.query(User).filter(User.role_name == 'admin').all()
        updated_count = 0
        
        for admin_user in admin_users:
            if assign_super_admin_to_user(db, admin_user.username):
                updated_count += 1
            elif assign_super_admin_to_user(db, admin_user.email):
                updated_count += 1
        
        print(f"Updated {updated_count} admin users to super_admin role")
        
        # Step 5: Assign super_admin to specific admin emails
        print("\n🎯 Step 5: Ensuring key admin users have super_admin role...")
        key_admins = ["junnel@alphasys.com.au"]
        
        for admin_email in key_admins:
            assign_super_admin_to_user(db, admin_email)
        
        print("\n✅ Super-Admin configuration completed successfully!")
        print("\n📊 Current Role Summary:")
        
        # Display role summary
        roles = db.query(Role).all()
        for role in roles:
            permission_count = len(RBACUtils.get_role_permission_names(role, db))
            print(f"  - {role.role_name}: {permission_count} permissions")
        
    except Exception as e:
        print(f"❌ Error during configuration: {str(e)}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    main()