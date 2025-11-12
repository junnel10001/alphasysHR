"""
Direct test of the invitation service fix
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from backend.models import Base, User, Employee, UserInvitation, Role, Department
from backend.services.invitation_service import InvitationService
from backend.schemas.invitation import InvitationAccept
from backend.database import get_db, engine
import os
from datetime import datetime

# Use the same database configuration as the application
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def test_invitation_fix():
    """Test that user_id is properly populated in employee record when accepting invitation."""
    
    db = SessionLocal()
    service = InvitationService(db)
    
    try:
        # Step 1: Create a test employee without user_id
        print("\n1. Creating test employee...")
        test_employee = Employee(
            company_id="TEST123",
            first_name="John",
            last_name="Doe",
            personal_email="john.doe.test@example.com"
        )
        db.add(test_employee)
        db.commit()
        db.refresh(test_employee)
        print(f"✓ Created employee ID: {test_employee.employee_id}")
        
        # Step 2: Create an invitation for this employee
        print("\n2. Creating invitation...")
        from backend.models import InvitationStatus
        
        # Get or create a test role and department
        role = db.query(Role).first()
        if not role:
            role = Role(role_name="employee", description="Test role")
            db.add(role)
            db.commit()
            db.refresh(role)
        
        test_invitation = UserInvitation(
            email="john.doe.test@example.com",
            token="test_token_123456789",
            invited_by=1,  # Assuming admin user exists
            role_id=role.role_id,
            employee_profile_id=test_employee.employee_id,
            status=InvitationStatus.pending.value,
            expires_at=datetime(2025, 12, 31)
        )
        db.add(test_invitation)
        db.commit()
        db.refresh(test_invitation)
        print(f"✓ Created invitation ID: {test_invitation.invitation_id}")
        
        # Step 3: Accept the invitation
        print("\n3. Accepting invitation...")
        accept_data = InvitationAccept(
            token="test_token_123456789",
            username="johndoe",
            password="password123",
            first_name="John",
            last_name="Doe",
            phone_number="1234567890"
        )
        
        result = service.accept_invitation(accept_data)
        
        if result.success:
            print(f"✓ Invitation accepted successfully")
            print(f"   User ID: {result.user_id}")
        else:
            print(f"❌ Invitation acceptance failed: {result.message}")
            return False
        
        # Step 4: Verify the employee now has a user_id
        print("\n4. Verifying employee has user_id...")
        db.refresh(test_employee)
        
        if test_employee.user_id:
            print(f"✅ SUCCESS: Employee {test_employee.employee_id} now has user_id: {test_employee.user_id}")
            return True
        else:
            print(f"❌ FAILURE: Employee {test_employee.employee_id} still has no user_id")
            return False
            
    except Exception as e:
        print(f"❌ Test failed with error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        # Clean up test data
        print("\n5. Cleaning up test data...")
        try:
            # Delete in correct order to avoid foreign key constraints
            db.query(UserInvitation).filter(UserInvitation.email == "john.doe.test@example.com").delete()
            db.query(User).filter(User.email == "john.doe.test@example.com").delete()
            db.query(Employee).filter(Employee.employee_id == test_employee.employee_id).delete()
            db.commit()
            print("✓ Test data cleaned up")
        except:
            pass
        db.close()

if __name__ == "__main__":
    print("Testing invitation user_id population fix (direct service test)...")
    success = test_invitation_fix()
    
    if success:
        print("\n🎉 Test passed! The user_id is properly populated when an employee accepts an invitation.")
    else:
        print("\n💥 Test failed! The issue still exists.")