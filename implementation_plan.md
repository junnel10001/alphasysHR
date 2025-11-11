# Employee Invitation Feature Implementation Plan

## Database Migration Script

### Alembic Migration: Add User Invitation System

```python
# alembic/versions/add_user_invitation_system.py

"""Add user invitation system

Revision ID: add_user_invitation
Revises: 20250925_091600_add_office_and_employee_tables
Create Date: 2025-11-11 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision = 'add_user_invitation'
down_revision = '20250925_091600_add_office_and_employee_tables'
branch_labels = None
depends_on = None


def upgrade():
    # Create user_invitations table
    op.create_table(
        'user_invitations',
        sa.Column('invitation_id', sa.Integer(), nullable=False),
        sa.Column('employee_id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=True),
        sa.Column('invited_by_user_id', sa.Integer(), nullable=False),
        sa.Column('invitation_token', sa.String(length=255), nullable=False),
        sa.Column('username', sa.String(length=50), nullable=False),
        sa.Column('password_hash', sa.String(length=255), nullable=False),
        sa.Column('role_id', sa.Integer(), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=True),
        sa.Column('invited_at', sa.TIMESTAMP(), server_default=sa.text('now()'), nullable=True),
        sa.Column('expires_at', sa.TIMESTAMP(), nullable=False),
        sa.Column('accepted_at', sa.TIMESTAMP(), nullable=True),
        sa.ForeignKeyConstraint(['employee_id'], ['employees.employee_id'], ),
        sa.ForeignKeyConstraint(['invited_by_user_id'], ['users.user_id'], ),
        sa.ForeignKeyConstraint(['role_id'], ['roles.role_id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.user_id'], ),
        sa.PrimaryKeyConstraint('invitation_id'),
        sa.UniqueConstraint('invitation_token'),
        sa.UniqueConstraint('username')
    )
    op.create_index(op.f('ix_user_invitations_invitation_id'), 'user_invitations', ['invitation_id'], unique=False)

    # Add employee_id to users table
    op.add_column('users', sa.Column('employee_id', sa.Integer(), nullable=True))
    op.create_foreign_key('fk_users_employee_id', 'users', 'employees', ['employee_id'], ['employee_id'])
    op.create_index(op.f('ix_users_employee_id'), 'users', ['employee_id'], unique=False)


def downgrade():
    # Remove employee_id from users table
    op.drop_index(op.f('ix_users_employee_id'), table_name='users')
    op.drop_constraint('fk_users_employee_id', 'users', type_='foreignkey')
    op.drop_column('users', 'employee_id')
    
    # Drop user_invitations table
    op.drop_index(op.f('ix_user_invitations_invitation_id'), table_name='user_invitations')
    op.drop_table('user_invitations')
```

## Backend Implementation

### 1. Updated Models (backend/models.py)

```python
# Add to existing imports
import secrets
from datetime import datetime, timedelta

# Add to existing models
class UserInvitation(Base):
    __tablename__ = "user_invitations"

    invitation_id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(Integer, ForeignKey("employees.employee_id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.user_id"), nullable=True)
    invited_by_user_id = Column(Integer, ForeignKey("users.user_id"), nullable=False)
    invitation_token = Column(String(255), unique=True, nullable=False)
    username = Column(String(50), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    role_id = Column(Integer, ForeignKey("roles.role_id"), nullable=False)
    
    status = Column(String(20), default="pending")  # pending, accepted, expired, revoked
    invited_at = Column(TIMESTAMP, server_default=func.now())
    expires_at = Column(TIMESTAMP, nullable=False)
    accepted_at = Column(TIMESTAMP, nullable=True)
    
    # Relationships
    employee = relationship("Employee", back_populates="invitation")
    user = relationship("User", foreign_keys=[user_id])
    invited_by = relationship("User", foreign_keys=[invited_by_user_id])
    role = relationship("Role")

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if not self.invitation_token:
            self.invitation_token = secrets.token_urlsafe(32)
        if not self.expires_at:
            self.expires_at = datetime.utcnow() + timedelta(days=7)

# Update existing User model
User.employee_id = Column(Integer, ForeignKey("employees.employee_id"), nullable=True)
User.employee_profile = relationship("Employee", back_populates="user_account", foreign_keys=[employee_id])

# Update existing Employee model  
Employee.invitation = relationship("UserInvitation", back_populates="employee", uselist=False)
Employee.user_account = relationship("User", back_populates="employee_profile", foreign_keys=[User.employee_id])
```

### 2. Email Service (backend/services/email_service.py)

```python
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional
from backend.config import SMTP_HOST, SMTP_PORT, SMTP_USERNAME, SMTP_PASSWORD, EMAIL_FROM

class EmailService:
    def __init__(self):
        self.smtp_host = SMTP_HOST
        self.smtp_port = SMTP_PORT
        self.smtp_username = SMTP_USERNAME
        self.smtp_password = SMTP_PASSWORD
        self.from_email = EMAIL_FROM

    def _create_server(self):
        """Create SMTP server connection"""
        server = smtplib.SMTP(self.smtp_host, self.smtp_port)
        server.starttls()
        server.login(self.smtp_username, self.smtp_password)
        return server

    def send_invitation_email(self, to_email: str, employee_name: str, 
                           username: str, password: str, role_name: str) -> bool:
        """Send invitation email with login credentials"""
        try:
            server = self._create_server()
            
            subject = "Welcome to AlphaHR - Your Account Details"
            
            body = f"""
Dear {employee_name},

You have been invited to join the AlphaHR system as a {role_name}.

Your login credentials are:
Username: {username}
Password: {password}

Please login at: {os.getenv('FRONTEND_URL', 'http://localhost:3000')}/login

For security reasons, we recommend changing your password after your first login.

If you have any questions, please contact your HR administrator.

Best regards,
AlphaHR Team
            """
            
            msg = MIMEMultipart()
            msg['From'] = self.from_email
            msg['To'] = to_email
            msg['Subject'] = subject
            msg.attach(MIMEText(body, 'plain'))
            
            server.send_message(msg)
            server.quit()
            return True
            
        except Exception as e:
            print(f"Failed to send invitation email: {e}")
            return False

# Singleton instance
email_service = EmailService()
```

### 3. Invitation Schemas (backend/schemas/invitation.py)

```python
from pydantic import BaseModel, EmailStr, validator
from typing import Optional
from datetime import datetime

class InvitationCreate(BaseModel):
    employee_id: int
    username: str
    password: str
    role_id: int
    send_email: bool = True

    @validator('password')
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        return v

class InvitationOut(BaseModel):
    invitation_id: int
    employee_id: int
    username: str
    role_id: int
    status: str
    invited_at: datetime
    expires_at: datetime
    accepted_at: Optional[datetime] = None
    
    # Related objects
    employee: Optional[dict] = None
    role: Optional[dict] = None
    invited_by: Optional[dict] = None

    class Config:
        from_attributes = True

class InvitationAccept(BaseModel):
    token: str
```

### 4. Invitation Service (backend/services/invitation_service.py)

```python
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from typing import List, Optional
from datetime import datetime, timedelta
import secrets
import bcrypt

from backend.models import User, Employee, UserInvitation, Role
from backend.schemas.invitation import InvitationCreate
from backend.services.email_service import email_service
from backend.utils.auth import get_password_hash

class InvitationService:
    @staticmethod
    def create_invitation(db: Session, invitation_in: InvitationCreate, 
                        invited_by_user_id: int) -> UserInvitation:
        """Create a new user invitation"""
        
        # Validate employee exists and doesn't have user account
        employee = db.query(Employee).filter(Employee.employee_id == invitation_in.employee_id).first()
        if not employee:
            raise ValueError("Employee not found")
            
        # Check if employee already has user account
        existing_user = db.query(User).filter(User.employee_id == employee.employee_id).first()
        if existing_user:
            raise ValueError("Employee already has a user account")
            
        # Check if invitation already exists
        existing_invitation = db.query(UserInvitation).filter(
            and_(
                UserInvitation.employee_id == invitation_in.employee_id,
                UserInvitation.status.in_(["pending", "accepted"])
            )
        ).first()
        if existing_invitation:
            raise ValueError("Invitation already exists for this employee")
            
        # Check if username is available
        if db.query(User).filter(User.username == invitation_in.username).first():
            raise ValueError("Username already exists")
            
        # Validate role exists
        role = db.query(Role).filter(Role.role_id == invitation_in.role_id).first()
        if not role:
            raise ValueError("Role not found")
            
        # Create invitation
        invitation = UserInvitation(
            employee_id=invitation_in.employee_id,
            invited_by_user_id=invited_by_user_id,
            username=invitation_in.username,
            password_hash=get_password_hash(invitation_in.password),
            role_id=invitation_in.role_id,
            expires_at=datetime.utcnow() + timedelta(days=7)
        )
        
        db.add(invitation)
        db.commit()
        db.refresh(invitation)
        
        # Send email if requested
        if invitation_in.send_email:
            email_sent = email_service.send_invitation_email(
                to_email=employee.personal_email or f"{employee.first_name.lower()}.{employee.last_name.lower()}@company.com",
                employee_name=f"{employee.first_name} {employee.last_name}",
                username=invitation_in.username,
                password=invitation_in.password,
                role_name=role.role_name
            )
            if not email_sent:
                print(f"Warning: Failed to send invitation email to {employee.first_name} {employee.last_name}")
        
        return invitation

    @staticmethod
    def accept_invitation(db: Session, token: str) -> User:
        """Accept invitation and create user account"""
        
        invitation = db.query(UserInvitation).filter(
            and_(
                UserInvitation.invitation_token == token,
                UserInvitation.status == "pending",
                UserInvitation.expires_at > datetime.utcnow()
            )
        ).first()
            
        if not invitation:
            raise ValueError("Invalid or expired invitation")
            
        # Create user account
        user = User(
            username=invitation.username,
            password_hash=invitation.password_hash,
            first_name=invitation.employee.first_name,
            last_name=invitation.employee.last_name,
            email=invitation.employee.personal_email or f"{invitation.username}@company.com",
            role_id=invitation.role_id,
            role_name=invitation.role.role_name,
            employee_id=invitation.employee_id,
            hourly_rate=invitation.employee.basic_salary or 0.0,
            date_hired=invitation.employee.date_hired or datetime.utcnow().date(),
            status="active"
        )
        
        db.add(user)
        
        # Update invitation status
        invitation.status = "accepted"
        invitation.accepted_at = datetime.utcnow()
        invitation.user_id = user.user_id
        
        db.commit()
        db.refresh(user)
        
        return user

    @staticmethod
    def get_invitable_employees(db: Session) -> List[Employee]:
        """Get employees who don't have user accounts"""
        
        # Subquery to get employee_ids that have user accounts
        employee_ids_with_users = db.query(User.employee_id).filter(User.employee_id.isnot(None)).subquery()
        
        # Get employees without user accounts
        employees = db.query(Employee).filter(
            ~Employee.employee_id.in_(employee_ids_with_users)
        ).all()
        
        return employees

    @staticmethod
    def get_invitations(db: Session, skip: int = 0, limit: int = 100) -> List[UserInvitation]:
        """Get all invitations"""
        return db.query(UserInvitation).offset(skip).limit(limit).all()

    @staticmethod
    def resend_invitation(db: Session, invitation_id: int) -> UserInvitation:
        """Resend invitation email"""
        invitation = db.query(UserInvitation).filter(
            UserInvitation.invitation_id == invitation_id
        ).first()
        
        if not invitation:
            raise ValueError("Invitation not found")
            
        if invitation.status != "pending":
            raise ValueError("Cannot resend invitation that is not pending")
            
        # Extend expiration
        invitation.expires_at = datetime.utcnow() + timedelta(days=7)
        
        # Resend email
        email_sent = email_service.send_invitation_email(
            to_email=invitation.employee.personal_email,
            employee_name=f"{invitation.employee.first_name} {invitation.employee.last_name}",
            username=invitation.username,
            password="<same as original>",  # We don't store plain password
            role_name=invitation.role.role_name
        )
        
        if not email_sent:
            raise ValueError("Failed to resend invitation email")
            
        db.commit()
        db.refresh(invitation)
        
        return invitation

    @staticmethod
    def revoke_invitation(db: Session, invitation_id: int) -> UserInvitation:
        """Revoke invitation"""
        invitation = db.query(UserInvitation).filter(
            UserInvitation.invitation_id == invitation_id
        ).first()
        
        if not invitation:
            raise ValueError("Invitation not found")
            
        invitation.status = "revoked"
        db.commit()
        db.refresh(invitation)
        
        return invitation
```

### 5. Invitation Router (backend/routers/invitations.py)

```python
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload
from typing import List

from backend.database import get_db
from backend.models import User, UserInvitation, Employee
from backend.schemas.invitation import InvitationCreate, InvitationOut, InvitationAccept
from backend.services.invitation_service import InvitationService
from backend.utils.auth import get_current_user

router = APIRouter(prefix="/api/invitations", tags=["invitations"])

@router.post("/", response_model=InvitationOut, status_code=status.HTTP_201_CREATED)
def create_invitation(
    invitation_in: InvitationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new invitation (admin/manager only)"""
    # Check permissions - only admin/manager can create invitations
    if current_user.role_name not in ["admin", "manager", "hr"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to create invitations"
        )
    
    try:
        invitation = InvitationService.create_invitation(db, invitation_in, current_user.user_id)
        
        # Load related objects for response
        db.refresh(invitation)
        invitation = db.query(UserInvitation).options(
            joinedload(UserInvitation.employee),
            joinedload(UserInvitation.role),
            joinedload(UserInvitation.invited_by)
        ).filter(UserInvitation.invitation_id == invitation.invitation_id).first()
        
        return invitation
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create invitation"
        )

@router.post("/accept", response_model=dict)
def accept_invitation(
    invitation_data: InvitationAccept,
    db: Session = Depends(get_db)
):
    """Accept invitation and create user account"""
    try:
        user = InvitationService.accept_invitation(db, invitation_data.token)
        return {
            "message": "Invitation accepted successfully",
            "user_id": user.user_id,
            "username": user.username
        }
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to accept invitation"
        )

@router.get("/", response_model=List[InvitationOut])
def list_invitations(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List all invitations (admin only)"""
    if current_user.role_name not in ["admin", "manager", "hr"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view invitations"
        )
    
    invitations = db.query(UserInvitation).options(
        joinedload(UserInvitation.employee),
        joinedload(UserInvitation.role),
        joinedload(UserInvitation.invited_by)
    ).offset(skip).limit(limit).all()
    
    return invitations

@router.get("/invitable", response_model=List[dict])
def get_invitable_employees(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get employees who can be invited (don't have user accounts)"""
    if current_user.role_name not in ["admin", "manager", "hr"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view invitable employees"
        )
    
    employees = InvitationService.get_invitable_employees(db)
    
    # Format for frontend
    result = []
    for emp in employees:
        result.append({
            "employee_id": emp.employee_id,
            "first_name": emp.first_name,
            "last_name": emp.last_name,
            "personal_email": emp.personal_email,
            "department": emp.department.department_name if emp.department else None,
            "job_title": emp.job_title
        })
    
    return result

@router.put("/{invitation_id}/resend", response_model=InvitationOut)
def resend_invitation(
    invitation_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Resend invitation email"""
    if current_user.role_name not in ["admin", "manager", "hr"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to resend invitations"
        )
    
    try:
        invitation = InvitationService.resend_invitation(db, invitation_id)
        
        # Load related objects for response
        invitation = db.query(UserInvitation).options(
            joinedload(UserInvitation.employee),
            joinedload(UserInvitation.role),
            joinedload(UserInvitation.invited_by)
        ).filter(UserInvitation.invitation_id == invitation.invitation_id).first()
        
        return invitation
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to resend invitation"
        )

@router.delete("/{invitation_id}", status_code=status.HTTP_204_NO_CONTENT)
def revoke_invitation(
    invitation_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Revoke invitation"""
    if current_user.role_name not in ["admin", "manager", "hr"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to revoke invitations"
        )
    
    try:
        InvitationService.revoke_invitation(db, invitation_id)
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to revoke invitation"
        )
```

## Frontend Implementation

### 1. API Service Updates (frontend/src/lib/api.ts)

```typescript
// Add to existing exports
export const invitationService = {
  async getInvitableEmployees() {
    const response = await api.get('/api/invitations/invitable')
    return response.data
  },

  async createInvitation(data: any) {
    const response = await api.post('/api/invitations/', data)
    return response.data
  },

  async getInvitations(params?: any) {
    const response = await api.get('/api/invitations/', { params })
    return response.data
  },

  async resendInvitation(id: number) {
    const response = await api.put(`/api/invitations/${id}/resend`)
    return response.data
  },

  async revokeInvitation(id: number) {
    const response = await api.delete(`/api/invitations/${id}`)
    return response.data
  },

  async acceptInvitation(token: string) {
    const response = await api.post('/api/invitations/accept', { token })
    return response.data
  }
}
```

### 2. Updated Employee List Page (frontend/src/app/employees/page.tsx)

```typescript
// Add to existing imports
import { invitationService } from '@/lib/api'
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog'
import { UserPlus, Mail, CheckCircle, XCircle } from 'lucide-react'

// Add to component state
const [showInviteDialog, setShowInviteDialog] = useState(false)
const [selectedEmployee, setSelectedEmployee] = useState<any>(null)
const [inviteLoading, setInviteLoading] = useState(false)
const [invitableEmployees, setInvitableEmployees] = useState<any[]>([])

// Add to useEffect
useEffect(() => {
  const fetchInvitableEmployees = async () => {
    try {
      const data = await invitationService.getInvitableEmployees()
      setInvitableEmployees(data)
    } catch (err) {
      console.error('Failed to fetch invitable employees', err)
    }
  }
  fetchInvitableEmployees()
}, [])

// Add invitation dialog component
const InvitationDialog = ({ employee, onClose }: { employee: any, onClose: () => void }) => {
  const [formData, setFormData] = useState({
    username: '',
    password: '',
    confirmPassword: '',
    roleId: 1,
    sendEmail: true
  })
  const [errors, setErrors] = useState<any>({})

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setInviteLoading(true)
    setErrors({})

    try {
      await invitationService.createInvitation({
        employee_id: employee.employee_id,
        username: formData.username,
        password: formData.password,
        role_id: formData.roleId,
        send_email: formData.sendEmail
      })
      
      // Refresh employees list
      window.location.reload()
    } catch (err: any) {
      setErrors(err.response?.data?.detail || 'Failed to send invitation')
    } finally {
      setInviteLoading(false)
    }
  }

  return (
    <DialogContent className="sm:max-w-[425px]">
      <DialogHeader>
        <DialogTitle>Invite {employee.first_name} {employee.last_name}</DialogTitle>
      </DialogHeader>
      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label htmlFor="username">Username</label>
          <Input
            id="username"
            value={formData.username}
            onChange={(e) => setFormData({...formData, username: e.target.value})}
            required
          />
        </div>
        <div>
          <label htmlFor="password">Password</label>
          <Input
            id="password"
            type="password"
            value={formData.password}
            onChange={(e) => setFormData({...formData, password: e.target.value})}
            required
          />
        </div>
        <div>
          <label htmlFor="confirmPassword">Confirm Password</label>
          <Input
            id="confirmPassword"
            type="password"
            value={formData.confirmPassword}
            onChange={(e) => setFormData({...formData, confirmPassword: e.target.value})}
            required
          />
        </div>
        <div>
          <label htmlFor="roleId">Role</label>
          <Select value={formData.roleId} onValueChange={(value) => setFormData({...formData, roleId: parseInt(value)})}>
            <SelectTrigger>
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="1">Employee</SelectItem>
              <SelectItem value="2">Manager</SelectItem>
            </SelectContent>
          </Select>
        </div>
        <div className="flex items-center space-x-2">
          <input
            type="checkbox"
            id="sendEmail"
            checked={formData.sendEmail}
            onChange={(e) => setFormData({...formData, sendEmail: e.target.checked})}
          />
          <label htmlFor="sendEmail">Send invitation email</label>
        </div>
        {errors && <div className="text-red-600 text-sm">{errors}</div>}
        <div className="flex justify-end space-x-2">
          <Button type="button" variant="outline" onClick={onClose}>
            Cancel
          </Button>
          <Button type="submit" disabled={inviteLoading}>
            {inviteLoading ? 'Sending...' : 'Send Invitation'}
          </Button>
        </div>
      </form>
    </DialogContent>
  )
}

// Add to table actions (inside the dropdown menu)
{!filtered.find(emp => emp.employee_id === emp.employee_id && emp.user_account) && (
  <DropdownMenuItem 
    onClick={() => {
      setSelectedEmployee(emp)
      setShowInviteDialog(true)
    }}
  >
    <UserPlus className="mr-2 h-4 w-4" />
    Invite as User
  </DropdownMenuItem>
)}

// Add dialog at the end of component
<Dialog open={showInviteDialog} onOpenChange={setShowInviteDialog}>
  {selectedEmployee && (
    <InvitationDialog 
      employee={selectedEmployee} 
      onClose={() => setShowInviteDialog(false)} 
    />
  )}
</Dialog>
```

### 3. Invitation Status Indicator

```typescript
// Add to table header
<TableHead>User Status</TableHead>

// Add to table body
<TableCell>
  {emp.user_account ? (
    <div className="flex items-center text-green-600">
      <CheckCircle className="mr-1 h-4 w-4" />
      Active User
    </div>
  ) : invitableEmployees.find(inv => inv.employee_id === emp.employee_id) ? (
    <div className="flex items-center text-gray-600">
      <UserPlus className="mr-1 h-4 w-4" />
      Can be Invited
    </div>
  ) : (
    <div className="flex items-center text-red-600">
      <XCircle className="mr-1 h-4 w-4" />
      No User Account
    </div>
  )}
</TableCell>
```

## Configuration Updates

### Environment Variables (.env)

```bash
# Email Configuration
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@company.com
SMTP_PASSWORD=your-app-password
EMAIL_FROM=noreply@alphahr.com

# Frontend URL
FRONTEND_URL=http://localhost:3000
```

### Requirements Update (requirements.txt)

```txt
# Add email service dependencies
secure-smtplib==0.1.1
email-validator==2.0.0
```

This implementation plan provides a complete, secure, and scalable employee invitation system that integrates seamlessly with the existing AlphaHR architecture.