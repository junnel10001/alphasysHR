"""
Script to update permissions for existing users
This script re-runs the RBAC seeding to ensure all users have the latest permissions
"""

from sqlalchemy.orm import Session
from database import get_db, engine
from models import Base, Permission
from utils.rbac import RBACUtils

def update_permissions():
    """Update permissions for all existing users"""
    print("Updating permissions for existing users...")
    
    # Create all tables
    Base.metadata.create_all(bind=engine)
    
    # Get database session
    db = next(get_db())
    
    try:
        # Seed default permissions (this will add any new permissions)
        permissions = RBACUtils.seed_default_permissions(db)
        print(f"✅ Default permissions seeded: {len(permissions)} permissions")
        
        # Re-seed default roles with updated permissions
        roles = RBACUtils.seed_default_roles(db)
        print(f"✅ Default roles re-seeded with updated permissions: {len(roles)} roles")
        
        # Check if new permissions were added
        view_roles_perm = db.query(Permission).filter(Permission.permission_name == "view_roles").first()
        view_depts_perm = db.query(Permission).filter(Permission.permission_name == "view_departments").first()
        
        if view_roles_perm:
            print("✅ view_roles permission exists")
        else:
            print("❌ view_roles permission missing")
            
        if view_depts_perm:
            print("✅ view_departments permission exists")
        else:
            print("❌ view_departments permission missing")
        
        print("✅ Permission update completed successfully!")
        
    except Exception as e:
        print(f"❌ Error updating permissions: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    update_permissions()