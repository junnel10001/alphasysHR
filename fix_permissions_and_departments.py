#!/usr/bin/env python3
"""
Script to fix permission and department issues in AlphaHR application.
This script ensures:
1. All required permissions are created
2. Permissions are properly assigned to roles
3. Departments are properly seeded
"""

import sys
from pathlib import Path

# Add the project root to the Python path
sys.path.append(str(Path(__file__).resolve().parent))

from backend.database import SessionLocal, engine
from backend.models import Base, Role, Permission, RolePermission, Department, User
from backend.utils.rbac import RBACUtils

def fix_permissions():
    """Ensure all required permissions exist and are properly assigned."""
    db = SessionLocal()
    try:
        print("🔧 Fixing permissions...")
        
        # Seed all default permissions
        permissions = RBACUtils.seed_default_permissions(db)
        print(f"✅ Created {len(permissions)} new permissions")
        
        # Seed all default roles with permissions
        roles = RBACUtils.seed_default_roles(db)
        print(f"✅ Created {len(roles)} new roles")
        
        # Verify admin user has proper role assignment
        admin_user = db.query(User).filter(User.email == "junnel@alphasys.com.au").first()
        if admin_user:
            admin_role = db.query(Role).filter(Role.role_name == "admin").first()
            if admin_role:
                admin_user.role_id = admin_role.role_id
                admin_user.role_name = admin_role.role_name
                db.commit()
                print(f"✅ Admin user {admin_user.email} assigned to admin role")
            else:
                print("❌ Admin role not found!")
        else:
            print("❌ Admin user not found!")
            
        # Verify view_roles permission exists
        view_roles_perm = db.query(Permission).filter(Permission.permission_name == "view_roles").first()
        if view_roles_perm:
            print("✅ view_roles permission exists")
        else:
            print("❌ view_roles permission missing!")
            
        # Verify view_departments permission exists
        view_depts_perm = db.query(Permission).filter(Permission.permission_name == "view_departments").first()
        if view_depts_perm:
            print("✅ view_departments permission exists")
        else:
            print("❌ view_departments permission missing!")
            
    except Exception as e:
        print(f"❌ Error fixing permissions: {e}")
        db.rollback()
    finally:
        db.close()

def fix_departments():
    """Ensure departments are properly seeded."""
    db = SessionLocal()
    try:
        print("🔧 Fixing departments...")
        
        # Check existing departments
        existing_depts = db.query(Department).all()
        print(f"📊 Found {len(existing_depts)} existing departments")
        
        # Seed departments if needed
        department_names = [
            "Human Resources",
            "Finance", 
            "Engineering",
            "Sales",
            "Marketing",
            "Operations",
            "IT",
            "Customer Service"
        ]
        
        created_count = 0
        for name in department_names:
            existing = db.query(Department).filter(Department.department_name == name).first()
            if not existing:
                dept = Department(department_name=name)
                db.add(dept)
                created_count += 1
                
        if created_count > 0:
            db.commit()
            print(f"✅ Created {created_count} new departments")
        else:
            print("✅ All departments already exist")
            
        # List all departments
        all_depts = db.query(Department).all()
        print("📋 All departments:")
        for dept in all_depts:
            print(f"  - {dept.department_name} (ID: {dept.department_id})")
            
    except Exception as e:
        print(f"❌ Error fixing departments: {e}")
        db.rollback()
    finally:
        db.close()

def verify_user_permissions():
    """Verify that admin user has all required permissions."""
    db = SessionLocal()
    try:
        print("🔍 Verifying admin user permissions...")
        
        admin_user = db.query(User).filter(User.email == "junnel@alphasys.com.au").first()
        if not admin_user:
            print("❌ Admin user not found!")
            return
            
        permissions = RBACUtils.get_user_permission_names(admin_user, db)
        print(f"📊 Admin user has {len(permissions)} permissions:")
        
        required_permissions = [
            "view_roles",
            "view_departments", 
            "manage_departments",
            "read_employee",
            "admin_access"
        ]
        
        missing_perms = []
        for perm in required_permissions:
            if perm in permissions:
                print(f"  ✅ {perm}")
            else:
                print(f"  ❌ {perm} - MISSING")
                missing_perms.append(perm)
                
        if missing_perms:
            print(f"⚠️  Admin user is missing {len(missing_perms)} permissions")
        else:
            print("✅ Admin user has all required permissions")
            
    except Exception as e:
        print(f"❌ Error verifying permissions: {e}")
    finally:
        db.close()

def main():
    """Main function to run all fixes."""
    print("🚀 Starting AlphaHR Permission and Department Fix")
    print("=" * 50)
    
    # Create tables if they don't exist
    Base.metadata.create_all(bind=engine)
    
    # Fix permissions
    fix_permissions()
    print()
    
    # Fix departments
    fix_departments()
    print()
    
    # Verify permissions
    verify_user_permissions()
    print()
    
    print("🎉 Fix completed!")
    print("Please restart the application to ensure all changes take effect.")

if __name__ == "__main__":
    main()