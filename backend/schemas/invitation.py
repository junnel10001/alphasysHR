"""
Pydantic schemas for UserInvitation model and related operations.
"""

from datetime import datetime, date
from typing import Optional, List, Any
from pydantic import BaseModel, EmailStr, Field, validator
from enum import Enum


class InvitationStatusEnum(str, Enum):
    pending = "pending"
    accepted = "accepted"
    expired = "expired"
    revoked = "revoked"


class InvitationBase(BaseModel):
    """Base schema for UserInvitation with common fields."""
    email: EmailStr = Field(..., description="Email address of the person being invited")
    role_id: int = Field(..., description="Role ID for the invited user")
    department_id: Optional[int] = Field(None, description="Department ID for the invited user")
    employee_profile_id: Optional[int] = Field(None, description="Employee profile ID if linking to existing employee record")


class InvitationCreate(InvitationBase):
    """Schema for creating a new invitation."""
    expires_days: int = Field(7, ge=1, le=30, description="Number of days until invitation expires")
    
    @validator('email')
    def validate_email_not_taken(cls, v, values):
        """This validator will be used in the service layer to check if email is already taken."""
        return v


class InvitationAccept(BaseModel):
    """Schema for accepting an invitation."""
    token: str = Field(..., description="Invitation token")
    username: str = Field(..., min_length=3, max_length=50, description="Username for the new user")
    password: str = Field(..., min_length=8, description="Password for the new user")
    first_name: str = Field(..., min_length=1, max_length=100, description="First name")
    last_name: str = Field(..., min_length=1, max_length=100, description="Last name")
    phone_number: Optional[str] = Field(None, max_length=20, description="Phone number")
    
    @validator('password')
    def validate_password_strength(cls, v):
        """Basic password validation."""
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        return v


class InvitationUpdate(BaseModel):
    """Schema for updating an invitation (status changes, etc.)."""
    status: Optional[InvitationStatusEnum] = None
    expires_at: Optional[datetime] = None
    revoked_at: Optional[datetime] = None


class InvitationOut(BaseModel):
    """Schema for returning invitation data."""
    invitation_id: int
    email: str
    token: str
    invited_by: int
    role_id: int
    department_id: Optional[int] = None
    employee_profile_id: Optional[int] = None
    status: str
    expires_at: datetime
    accepted_at: Optional[datetime] = None
    revoked_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    
    # Optional nested objects - properly typed for SQLAlchemy models
    invited_by_user: Optional[Any] = None
    role: Optional[Any] = None
    department: Optional[Any] = None
    employee_profile: Optional[Any] = None
    
    class Config:
        from_attributes = True
        # Enable JSON serialization of SQLAlchemy objects
        arbitrary_types_allowed = True
        
    @classmethod
    def from_orm(cls, obj):
        """Create InvitationOut from ORM object with proper serialization"""
        if obj is None:
            return None
            
        data = {
            "invitation_id": obj.invitation_id,
            "email": obj.email,
            "token": obj.token,
            "invited_by": obj.invited_by,
            "role_id": obj.role_id,
            "department_id": obj.department_id,
            "employee_profile_id": obj.employee_profile_id,
            "status": obj.status,
            "expires_at": obj.expires_at,
            "accepted_at": obj.accepted_at,
            "revoked_at": obj.revoked_at,
            "created_at": obj.created_at,
            "updated_at": obj.updated_at,
        }
        
        # Handle nested objects
        if hasattr(obj, 'invited_by_user') and obj.invited_by_user:
            data["invited_by_user"] = {
                "user_id": obj.invited_by_user.user_id,
                "username": obj.invited_by_user.username,
                "first_name": obj.invited_by_user.first_name,
                "last_name": obj.invited_by_user.last_name,
                "email": obj.invited_by_user.email,
            }
        
        if hasattr(obj, 'role') and obj.role:
            data["role"] = {
                "role_id": obj.role.role_id,
                "role_name": obj.role.role_name,
                "description": obj.role.description,
            }
        
        if hasattr(obj, 'department') and obj.department:
            data["department"] = {
                "department_id": obj.department.department_id,
                "department_name": obj.department.department_name,
            }
        
        if hasattr(obj, 'employee_profile') and obj.employee_profile:
            data["employee_profile"] = {
                "employee_id": obj.employee_profile.employee_id,
                "first_name": obj.employee_profile.first_name,
                "last_name": obj.employee_profile.last_name,
                "company_id": obj.employee_profile.company_id,
            }
            
        return cls(**data)


class InvitationList(BaseModel):
    """Schema for returning a list of invitations."""
    invitations: List[InvitationOut]
    total: int
    page: int
    per_page: int
    pages: int


class InvitationResend(BaseModel):
    """Schema for resending an invitation."""
    invitation_id: int = Field(..., description="ID of the invitation to resend")
    expires_days: int = Field(7, ge=1, le=30, description="New expiration period in days")


class InvitationRevoke(BaseModel):
    """Schema for revoking an invitation."""
    invitation_id: int = Field(..., description="ID of the invitation to revoke")
    reason: Optional[str] = Field(None, description="Reason for revocation")


class InvitationTokenValidate(BaseModel):
    """Schema for validating an invitation token."""
    token: str = Field(..., description="Invitation token to validate")
    is_valid: bool
    invitation_data: Optional[dict] = None
    error_message: Optional[str] = None


class InvitationAcceptResponse(BaseModel):
    """Schema for response when accepting an invitation."""
    success: bool
    message: str
    user_id: Optional[int] = None
    access_token: Optional[str] = None


class UserCreationFromInvitation(BaseModel):
    """Schema for creating a user from an accepted invitation."""
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr = Field(...)
    password: str = Field(..., min_length=8)
    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: str = Field(..., min_length=1, max_length=100)
    phone_number: Optional[str] = Field(None, max_length=20)
    role_id: int = Field(...)
    department_id: Optional[int] = None
    hourly_rate: float = Field(..., gt=0)
    date_hired: date = Field(default_factory=date.today)


class InvitationStatistics(BaseModel):
    """Schema for invitation statistics."""
    total_invitations: int
    pending_invitations: int
    accepted_invitations: int
    expired_invitations: int
    revoked_invitations: int
    invitations_this_month: int
    acceptance_rate: float


class InvitationEmailContent(BaseModel):
    """Schema for email content sent with invitation."""
    to_email: str
    subject: str
    body: str
    invitation_link: str
    expires_at: datetime
    invited_by_name: str
    role_name: str
    department_name: Optional[str] = None