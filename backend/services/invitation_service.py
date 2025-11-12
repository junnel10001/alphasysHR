"""
Invitation Service Layer

Provides business logic for managing user invitations in the AlphaHR system.
Handles creation, validation, acceptance, and expiration of invitations.
"""

import logging
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, or_

from backend.models import (
    User, UserInvitation, Role, Department, Employee, 
    InvitationStatus, UserStatus
)
from backend.schemas.invitation import (
    InvitationCreate, InvitationOut, InvitationAccept, 
    InvitationUpdate, InvitationList, InvitationStatistics,
    InvitationTokenValidate, InvitationAcceptResponse,
    UserCreationFromInvitation
)
from backend.services.email_service import EmailService, get_email_service
from backend.utils.auth import get_password_hash, create_access_token
from backend.database import get_db
from fastapi import HTTPException, status, Depends

logger = logging.getLogger(__name__)


class InvitationService:
    """Service class for managing user invitations."""
    
    def __init__(self, db: Session, email_service: EmailService = None):
        self.db = db
        self.email_service = email_service or get_email_service()
    
    def create_invitation(self, 
                        invitation_data: InvitationCreate, 
                        invited_by_user_id: int) -> UserInvitation:
        """
        Create a new user invitation.
        
        Args:
            invitation_data: Invitation creation data
            invited_by_user_id: ID of user creating the invitation
            
        Returns:
            UserInvitation: Created invitation
            
        Raises:
            HTTPException: If validation fails
        """
        # Validate email uniqueness
        if self._email_exists_in_users(invitation_data.email):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email is already registered in the system"
            )
        
        if self._has_pending_invitation(invitation_data.email):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already has a pending invitation"
            )
        
        # Validate role and department
        role = self.db.query(Role).filter(Role.role_id == invitation_data.role_id).first()
        if not role:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Role not found"
            )
        
        if invitation_data.department_id:
            department = self.db.query(Department).filter(
                Department.department_id == invitation_data.department_id
            ).first()
            if not department:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Department not found"
                )
        
        if invitation_data.employee_profile_id:
            employee = self.db.query(Employee).filter(
                Employee.employee_id == invitation_data.employee_profile_id
            ).first()
            if not employee:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Employee profile not found"
                )
        
        # Create invitation
        token = UserInvitation.generate_token()
        expires_at = datetime.utcnow() + timedelta(days=invitation_data.expires_days)
        
        db_invitation = UserInvitation(
            email=invitation_data.email,
            token=token,
            invited_by=invited_by_user_id,
            role_id=invitation_data.role_id,
            department_id=invitation_data.department_id,
            employee_profile_id=invitation_data.employee_profile_id,
            status=InvitationStatus.pending.value,
            expires_at=expires_at
        )
        
        self.db.add(db_invitation)
        self.db.commit()
        self.db.refresh(db_invitation)
        
        # Send invitation email
        invitation_link = f"http://localhost:3000/register?token={token}"
        logger.info(f"Invitation link: {invitation_link}")
        
        try:
            import asyncio
            # Only pass department_name if department_id is provided
            department_name = department.department_name if invitation_data.department_id and department else None
            
            # Check if we're already in an event loop
            try:
                loop = asyncio.get_running_loop()
                # If we're in a loop, create a task
                task = loop.create_task(
                    self.email_service.send_invitation_email(
                        to_email=invitation_data.email,
                        invited_by_name=self._get_user_name(invited_by_user_id),
                        role_name=role.role_name,
                        department_name=department_name,
                        invitation_link=invitation_link,
                        expires_at=expires_at
                    )
                )
                # We don't wait for the task to complete to avoid blocking
            except RuntimeError:
                # No running loop, we can run directly
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                loop.run_until_complete(
                    self.email_service.send_invitation_email(
                        to_email=invitation_data.email,
                        invited_by_name=self._get_user_name(invited_by_user_id),
                        role_name=role.role_name,
                        department_name=department_name,
                        invitation_link=invitation_link,
                        expires_at=expires_at
                    )
                )
                loop.close()
            
            logger.info(f"Invitation email queued for sending to {invitation_data.email}")
        except Exception as e:
            logger.error(f"Failed to send invitation email: {str(e)}")
            # Don't fail the invitation creation if email fails, but log the error
        
        logger.info(f"Created invitation for {invitation_data.email} by user {invited_by_user_id}")
        return db_invitation
    
    def list_invitations(self, 
                       skip: int = 0, 
                       limit: int = 100,
                       status_filter: Optional[str] = None,
                       invited_by_filter: Optional[int] = None) -> List[UserInvitation]:
        """
        List invitations with optional filters.
        
        Args:
            skip: Number of records to skip
            limit: Maximum number of records to return
            status_filter: Filter by invitation status
            invited_by_filter: Filter by user who sent invitation
            
        Returns:
            List[UserInvitation]: List of invitations
        """
        query = self.db.query(UserInvitation).options(
            joinedload(UserInvitation.invited_by_user),
            joinedload(UserInvitation.role),
            joinedload(UserInvitation.department),
            joinedload(UserInvitation.employee_profile)
        )
        
        if status_filter:
            query = query.filter(UserInvitation.status == status_filter)
        
        if invited_by_filter:
            query = query.filter(UserInvitation.invited_by == invited_by_filter)
        
        return query.offset(skip).limit(limit).all()
    
    def get_invitation_by_id(self, invitation_id: int) -> Optional[UserInvitation]:
        """
        Get invitation by ID.
        
        Args:
            invitation_id: ID of the invitation
            
        Returns:
            UserInvitation: Invitation if found, None otherwise
        """
        return self.db.query(UserInvitation).options(
            joinedload(UserInvitation.invited_by_user),
            joinedload(UserInvitation.role),
            joinedload(UserInvitation.department),
            joinedload(UserInvitation.employee_profile)
        ).filter(UserInvitation.invitation_id == invitation_id).first()
    
    def get_invitation_by_token(self, token: str) -> Optional[UserInvitation]:
        """
        Get invitation by token.
        
        Args:
            token: Invitation token
            
        Returns:
            UserInvitation: Invitation if found, None otherwise
        """
        return self.db.query(UserInvitation).options(
            joinedload(UserInvitation.invited_by_user),
            joinedload(UserInvitation.role),
            joinedload(UserInvitation.department),
            joinedload(UserInvitation.employee_profile)
        ).filter(UserInvitation.token == token).first()
    
    def validate_invitation_token(self, token: str) -> InvitationTokenValidate:
        """
        Validate an invitation token.
        
        Args:
            token: Invitation token to validate
            
        Returns:
            InvitationTokenValidate: Validation result
        """
        invitation = self.get_invitation_by_token(token)
        
        if not invitation:
            return InvitationTokenValidate(
                token=token,
                is_valid=False,
                error_message="Invalid invitation token"
            )
        
        if invitation.status != InvitationStatus.pending.value:
            return InvitationTokenValidate(
                token=token,
                is_valid=False,
                error_message=f"Invitation is {invitation.status}"
            )
        
        if invitation.expires_at < datetime.utcnow():
            # Auto-expire the invitation
            invitation.status = InvitationStatus.expired.value
            self.db.commit()
            
            return InvitationTokenValidate(
                token=token,
                is_valid=False,
                error_message="Invitation has expired"
            )
        
        # Check if email already exists
        if self._email_exists_in_users(invitation.email):
            return InvitationTokenValidate(
                token=token,
                is_valid=False,
                error_message="Email is already registered"
            )
        
        invitation_data = {
            "invitation_id": invitation.invitation_id,
            "email": invitation.email,
            "role_id": invitation.role_id,
            "role_name": invitation.role.role_name,
            "department_id": invitation.department_id,
            "department_name": invitation.department.department_name if invitation.department else None,
            "employee_profile_id": invitation.employee_profile_id,
            "employee_profile": {
                "first_name": invitation.employee_profile.first_name,
                "last_name": invitation.employee_profile.last_name,
                "employee_id": invitation.employee_profile.employee_id,
                "company_id": invitation.employee_profile.company_id
            } if invitation.employee_profile else None,
            "invited_by": invitation.invited_by,
            "invited_by_name": self._get_user_name(invitation.invited_by),
            "expires_at": invitation.expires_at.isoformat()
        }
        
        return InvitationTokenValidate(
            token=token,
            is_valid=True,
            invitation_data=invitation_data
        )
    
    def accept_invitation(self, accept_data: InvitationAccept) -> InvitationAcceptResponse:
        """
        Accept an invitation and create user account.
        
        Args:
            accept_data: Invitation acceptance data
            
        Returns:
            InvitationAcceptResponse: Result of acceptance
        """
        # Validate the token first
        validation = self.validate_invitation_token(accept_data.token)
        if not validation.is_valid:
            return InvitationAcceptResponse(
                success=False,
                message=validation.error_message
            )
        
        invitation = self.get_invitation_by_token(accept_data.token)
        
        # Check if username already exists
        if self.db.query(User).filter(User.username == accept_data.username).first():
            return InvitationAcceptResponse(
                success=False,
                message="Username already exists"
            )
        
        try:
            # Create user account
            hashed_password = get_password_hash(accept_data.password)
            new_user = User(
                username=accept_data.username,
                password_hash=hashed_password,
                first_name=accept_data.first_name,
                last_name=accept_data.last_name,
                email=invitation.email,
                phone_number=accept_data.phone_number,
                role_id=invitation.role_id,
                role_name=invitation.role.role_name,
                department_id=invitation.department_id,
                status=UserStatus.active.value
            )
            
            self.db.add(new_user)
            self.db.flush()  # Get the user_id
            
            # Update invitation status
            invitation.status = InvitationStatus.accepted.value
            invitation.accepted_at = datetime.utcnow()
            
            # If invitation is linked to an employee profile, update the user_id
            if invitation.employee_profile_id:
                employee = self.db.query(Employee).filter(
                    Employee.employee_id == invitation.employee_profile_id
                ).first()
                if employee:
                    employee.user_id = new_user.user_id
                    logger.info(f"Updated employee {employee.employee_id} with user_id {new_user.user_id}")
            
            self.db.commit()
            
            # Generate access token
            token_data = {"sub": new_user.username, "role": invitation.role.role_name}
            access_token = create_access_token(data=token_data)
            
            # Send welcome email
            try:
                import asyncio
                # Check if we're already in an event loop
                try:
                    loop = asyncio.get_running_loop()
                    # If we're in a loop, create a task
                    task = loop.create_task(
                        self.email_service.send_welcome_email(
                            to_email=new_user.email,
                            user_name=f"{new_user.first_name} {new_user.last_name}"
                        )
                    )
                    # We don't wait for the task to complete to avoid blocking
                except RuntimeError:
                    # No running loop, we can run directly
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    loop.run_until_complete(
                        self.email_service.send_welcome_email(
                            to_email=new_user.email,
                            user_name=f"{new_user.first_name} {new_user.last_name}"
                        )
                    )
                    loop.close()
                
                logger.info(f"Welcome email queued for sending to {new_user.email}")
            except Exception as e:
                logger.error(f"Failed to send welcome email: {str(e)}")
            
            logger.info(f"User {new_user.username} accepted invitation and created account")
            
            return InvitationAcceptResponse(
                success=True,
                message="Account created successfully",
                user_id=new_user.user_id,
                access_token=access_token
            )
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to accept invitation: {str(e)}")
            return InvitationAcceptResponse(
                success=False,
                message="Failed to create account. Please try again."
            )
    
    def resend_invitation(self, 
                        invitation_id: int, 
                        expires_days: int = 7,
                        requested_by_user_id: int = None) -> UserInvitation:
        """
        Resend an existing invitation with new expiration.
        
        Args:
            invitation_id: ID of invitation to resend
            expires_days: New expiration period in days
            requested_by_user_id: ID of user requesting resend
            
        Returns:
            UserInvitation: Updated invitation
            
        Raises:
            HTTPException: If invitation not found or invalid
        """
        invitation = self.get_invitation_by_id(invitation_id)
        
        if not invitation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Invitation not found"
            )
        
        if invitation.status not in [InvitationStatus.pending.value, InvitationStatus.expired.value]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Can only resend pending or expired invitations"
            )
        
        # Generate new token and update expiration
        invitation.token = UserInvitation.generate_token()
        invitation.expires_at = datetime.utcnow() + timedelta(days=expires_days)
        invitation.status = InvitationStatus.pending.value
        invitation.accepted_at = None
        invitation.revoked_at = None
        
        self.db.commit()
        
        # Send new invitation email
        invitation_link = f"http://localhost:3000/register?token={invitation.token}"
        try:
            import asyncio
            # Check if we're already in an event loop
            try:
                loop = asyncio.get_running_loop()
                # If we're in a loop, create a task
                task = loop.create_task(
                    self.email_service.send_invitation_email(
                        to_email=invitation.email,
                        invited_by_name=self._get_user_name(requested_by_user_id or invitation.invited_by),
                        role_name=invitation.role.role_name,
                        department_name=invitation.department.department_name if invitation.department else None,
                        invitation_link=invitation_link,
                        expires_at=invitation.expires_at
                    )
                )
                # We don't wait for the task to complete to avoid blocking
            except RuntimeError:
                # No running loop, we can run directly
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                loop.run_until_complete(
                    self.email_service.send_invitation_email(
                        to_email=invitation.email,
                        invited_by_name=self._get_user_name(requested_by_user_id or invitation.invited_by),
                        role_name=invitation.role.role_name,
                        department_name=invitation.department.department_name if invitation.department else None,
                        invitation_link=invitation_link,
                        expires_at=invitation.expires_at
                    )
                )
                loop.close()
            
            logger.info(f"Invitation email queued for resending to {invitation.email}")
        except Exception as e:
            logger.error(f"Failed to resend invitation email: {str(e)}")
        
        logger.info(f"Resent invitation for {invitation.email}")
        return invitation
    
    def revoke_invitation(self, 
                        invitation_id: int, 
                        reason: str = None,
                        requested_by_user_id: int = None) -> UserInvitation:
        """
        Revoke an invitation.
        
        Args:
            invitation_id: ID of invitation to revoke
            reason: Reason for revocation
            requested_by_user_id: ID of user requesting revocation
            
        Returns:
            UserInvitation: Updated invitation
            
        Raises:
            HTTPException: If invitation not found or already processed
        """
        invitation = self.get_invitation_by_id(invitation_id)
        
        if not invitation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Invitation not found"
            )
        
        if invitation.status in [InvitationStatus.accepted.value, InvitationStatus.revoked.value]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invitation is already accepted or revoked"
            )
        
        invitation.status = InvitationStatus.revoked.value
        invitation.revoked_at = datetime.utcnow()
        
        self.db.commit()
        
        logger.info(f"Revoked invitation {invitation_id} for {invitation.email}. Reason: {reason}")
        return invitation
    
    def get_invitation_statistics(self) -> InvitationStatistics:
        """
        Get invitation statistics.
        
        Returns:
            InvitationStatistics: Summary statistics
        """
        total = self.db.query(UserInvitation).count()
        pending = self.db.query(UserInvitation).filter(
            UserInvitation.status == InvitationStatus.pending.value
        ).count()
        accepted = self.db.query(UserInvitation).filter(
            UserInvitation.status == InvitationStatus.accepted.value
        ).count()
        expired = self.db.query(UserInvitation).filter(
            UserInvitation.status == InvitationStatus.expired.value
        ).count()
        revoked = self.db.query(UserInvitation).filter(
            UserInvitation.status == InvitationStatus.revoked.value
        ).count()
        
        # Invitations this month
        this_month = datetime.utcnow().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        invitations_this_month = self.db.query(UserInvitation).filter(
            UserInvitation.created_at >= this_month
        ).count()
        
        # Acceptance rate
        acceptance_rate = (accepted / total * 100) if total > 0 else 0
        
        return InvitationStatistics(
            total_invitations=total,
            pending_invitations=pending,
            accepted_invitations=accepted,
            expired_invitations=expired,
            revoked_invitations=revoked,
            invitations_this_month=invitations_this_month,
            acceptance_rate=round(acceptance_rate, 2)
        )
    
    def cleanup_expired_invitations(self) -> int:
        """
        Clean up expired invitations by marking them as expired.
        
        Returns:
            int: Number of invitations marked as expired
        """
        expired_invitations = self.db.query(UserInvitation).filter(
            and_(
                UserInvitation.status == InvitationStatus.pending.value,
                UserInvitation.expires_at < datetime.utcnow()
            )
        ).all()
        
        count = 0
        for invitation in expired_invitations:
            invitation.status = InvitationStatus.expired.value
            count += 1
        
        self.db.commit()
        
        if count > 0:
            logger.info(f"Marked {count} invitations as expired")
        
        return count
    
    def _email_exists_in_users(self, email: str) -> bool:
        """Check if email already exists in users table."""
        return self.db.query(User).filter(User.email == email).first() is not None
    
    def _has_pending_invitation(self, email: str) -> bool:
        """Check if email already has a pending invitation."""
        return self.db.query(UserInvitation).filter(
            and_(
                UserInvitation.email == email,
                UserInvitation.status == InvitationStatus.pending.value,
                UserInvitation.expires_at > datetime.utcnow()
            )
        ).first() is not None
    
    def _get_user_name(self, user_id: int) -> str:
        """Get user's full name by ID."""
        user = self.db.query(User).filter(User.user_id == user_id).first()
        if user:
            return f"{user.first_name} {user.last_name}"
        return "Unknown User"


# Dependency injection function
def get_invitation_service(db: Session = Depends(get_db)) -> InvitationService:
    """Get invitation service instance."""
    return InvitationService(db)