"""
Invitations Router

REST API endpoints for managing user invitations in the AlphaHR system.
Provides endpoints for creating, listing, accepting, resending, and revoking invitations.
"""

import logging
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models import User
from backend.middleware.rbac import get_current_user
from backend.utils.rbac import RBACUtils
from backend.schemas.invitation import (
    InvitationCreate, InvitationOut, InvitationList, InvitationAccept,
    InvitationResend, InvitationRevoke, InvitationTokenValidate,
    InvitationAcceptResponse, InvitationStatistics
)
from backend.services.invitation_service import (
    InvitationService, get_invitation_service
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/invitations", tags=["invitations"])


@router.post("/", response_model=InvitationOut, status_code=status.HTTP_201_CREATED)
async def create_invitation(
    invitation_data: InvitationCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    invitation_service: InvitationService = Depends(get_invitation_service)
):
    """
    Create a new user invitation.
    
    Requires 'create_employee' or 'manage_users' permission.
    """
    # Check permissions
    if not RBACUtils.user_has_permission(current_user, "manage_users", db):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to create invitations"
        )
    
    try:
        invitation = invitation_service.create_invitation(
            invitation_data=invitation_data,
            invited_by_user_id=current_user.user_id
        )
        logger.info(f"User {current_user.username} created invitation for {invitation_data.email}")
        # Convert to InvitationOut schema to ensure proper response format
        return InvitationOut.from_orm(invitation)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to create invitation: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create invitation"
        )


@router.get("/", response_model=InvitationList)
async def list_invitations(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of records to return"),
    status_filter: Optional[str] = Query(None, description="Filter by invitation status"),
    invited_by_filter: Optional[int] = Query(None, description="Filter by user who sent invitation"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    invitation_service: InvitationService = Depends(get_invitation_service)
):
    """
    List invitations with optional filters.
    
    Requires 'read_employee' or 'manage_users' permission.
    """
    # Check permissions
    if not RBACUtils.user_has_permission(current_user, "read_employee", db):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view invitations"
        )
    
    try:
        invitations = invitation_service.list_invitations(
            skip=skip,
            limit=limit,
            status_filter=status_filter,
            invited_by_filter=invited_by_filter
        )
        
        # Convert each UserInvitation to InvitationOut schema
        invitation_outs = [InvitationOut.from_orm(inv) for inv in invitations]
        
        # Get total count for pagination
        total = len(invitations)  # In production, you'd want to use a count query
        
        return InvitationList(
            invitations=invitation_outs,
            total=total,
            page=skip // limit + 1,
            per_page=limit,
            pages=(total + limit - 1) // limit
        )
        
    except Exception as e:
        logger.error(f"Failed to list invitations: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve invitations"
        )


@router.get("/{invitation_id}", response_model=InvitationOut)
async def get_invitation(
    invitation_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    invitation_service: InvitationService = Depends(get_invitation_service)
):
    """
    Get a specific invitation by ID.
    
    Requires 'read_employee' or 'manage_users' permission.
    """
    # Check permissions
    if not RBACUtils.user_has_permission(current_user, "read_employee", db):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view invitations"
        )
    
    invitation = invitation_service.get_invitation_by_id(invitation_id)
    
    if not invitation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invitation not found"
        )
    
    return InvitationOut.from_orm(invitation)


@router.post("/validate", response_model=InvitationTokenValidate)
async def validate_invitation_token(
    token: str = Query(..., description="Invitation token to validate"),
    invitation_service: InvitationService = Depends(get_invitation_service)
):
    """
    Validate an invitation token.
    
    This endpoint is public (no authentication required) as it's used
    by the invitation acceptance page to validate tokens before showing the form.
    """
    try:
        validation_result = invitation_service.validate_invitation_token(token)
        return validation_result
        
    except Exception as e:
        logger.error(f"Failed to validate invitation token: {str(e)}")
        return InvitationTokenValidate(
            token=token,
            is_valid=False,
            error_message="Failed to validate invitation token"
        )


@router.post("/accept", response_model=InvitationAcceptResponse)
async def accept_invitation(
    accept_data: InvitationAccept,
    invitation_service: InvitationService = Depends(get_invitation_service)
):
    """
    Accept an invitation and create user account.
    
    This endpoint is public (no authentication required) as it's used
    by new users to accept invitations and create their accounts.
    """
    try:
        result = invitation_service.accept_invitation(accept_data)
        return result
        
    except Exception as e:
        logger.error(f"Failed to accept invitation: {str(e)}")
        return InvitationAcceptResponse(
            success=False,
            message="Failed to process invitation acceptance"
        )


@router.post("/resend", response_model=InvitationOut)
async def resend_invitation(
    resend_data: InvitationResend,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    invitation_service: InvitationService = Depends(get_invitation_service)
):
    """
    Resend an existing invitation with new expiration.
    
    Requires 'manage_users' permission.
    """
    # Check permissions
    if not RBACUtils.user_has_permission(current_user, "manage_users", db):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to resend invitations"
        )
    
    try:
        invitation = invitation_service.resend_invitation(
            invitation_id=resend_data.invitation_id,
            expires_days=resend_data.expires_days,
            requested_by_user_id=current_user.user_id
        )
        
        logger.info(f"User {current_user.username} resent invitation {resend_data.invitation_id}")
        return InvitationOut.from_orm(invitation)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to resend invitation: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to resend invitation"
        )


@router.post("/revoke", response_model=InvitationOut)
async def revoke_invitation(
    revoke_data: InvitationRevoke,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    invitation_service: InvitationService = Depends(get_invitation_service)
):
    """
    Revoke an invitation.
    
    Requires 'manage_users' permission.
    """
    # Check permissions
    if not RBACUtils.user_has_permission(current_user, "manage_users", db):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to revoke invitations"
        )
    
    try:
        invitation = invitation_service.revoke_invitation(
            invitation_id=revoke_data.invitation_id,
            reason=revoke_data.reason,
            requested_by_user_id=current_user.user_id
        )
        
        logger.info(f"User {current_user.username} revoked invitation {revoke_data.invitation_id}")
        return InvitationOut.from_orm(invitation)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to revoke invitation: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to revoke invitation"
        )


@router.get("/statistics", response_model=InvitationStatistics)
async def get_invitation_statistics(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    invitation_service: InvitationService = Depends(get_invitation_service)
):
    """
    Get invitation statistics.
    
    Requires 'manage_users' permission.
    """
    # Check permissions
    if not RBACUtils.user_has_permission(current_user, "manage_users", db):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view invitation statistics"
        )
    
    try:
        statistics = invitation_service.get_invitation_statistics()
        return statistics
        
    except Exception as e:
        logger.error(f"Failed to get invitation statistics: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve invitation statistics"
        )


@router.post("/cleanup-expired")
async def cleanup_expired_invitations(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    invitation_service: InvitationService = Depends(get_invitation_service)
):
    """
    Clean up expired invitations by marking them as expired.
    
    Requires 'manage_users' permission.
    """
    # Check permissions
    if not RBACUtils.user_has_permission(current_user, "manage_users", db):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to clean up invitations"
        )
    
    try:
        count = invitation_service.cleanup_expired_invitations()
        logger.info(f"User {current_user.username} cleaned up {count} expired invitations")
        return {"message": f"Marked {count} invitations as expired", "count": count}
        
    except Exception as e:
        logger.error(f"Failed to cleanup expired invitations: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to cleanup expired invitations"
        )


@router.get("/my-invitations", response_model=InvitationList)
async def get_my_invitations(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of records to return"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    invitation_service: InvitationService = Depends(get_invitation_service)
):
    """
    Get invitations sent by the current user.
    
    Users can view their own sent invitations without special permissions.
    """
    try:
        invitations = invitation_service.list_invitations(
            skip=skip,
            limit=limit,
            invited_by_filter=current_user.user_id
        )
        
        # Convert each UserInvitation to InvitationOut schema
        invitation_outs = [InvitationOut.from_orm(inv) for inv in invitations]
        
        total = len(invitations)  # In production, you'd want to use a count query
        
        return InvitationList(
            invitations=invitation_outs,
            total=total,
            page=skip // limit + 1,
            per_page=limit,
            pages=(total + limit - 1) // limit
        )
        
    except Exception as e:
        logger.error(f"Failed to get user invitations: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve invitations"
        )