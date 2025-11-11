"""
Overtime Router

Provides API endpoints for overtime management functionality.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
from datetime import datetime, date

from backend.database import get_db
from backend.models import User, OvertimeRequest, OvertimeStatus
from backend.middleware.rbac import get_current_user, PermissionChecker
from pydantic import BaseModel

router = APIRouter(prefix="/overtime", tags=["overtime"])

# Pydantic models for request/response
class OvertimeRequestResponse(BaseModel):
    ot_id: int
    user_id: int
    date: str
    hours_requested: float
    reason: str
    status: str
    approver_id: Optional[int]
    approved_at: Optional[str]

class OvertimeRequestForm(BaseModel):
    date: str
    hours_requested: float
    reason: Optional[str] = None

class OvertimeStats(BaseModel):
    pending: int
    approved: int
    rejected: int

class OvertimeFilter(BaseModel):
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    status: Optional[str] = None
    user_id: Optional[int] = None

class OvertimeUpdateForm(BaseModel):
    status: str

# Get all overtime requests
@router.get("/", response_model=List[OvertimeRequestResponse])
def get_overtime_requests(
    filter_params: OvertimeFilter = Depends(),
    user_db_tuple: tuple[User, Session] = Depends(PermissionChecker.require_permission_with_db("admin_access"))
):
    """
    Get all overtime requests with optional filtering.
    
    Requires admin_access permission.
    """
    # Unpack the tuple
    current_user, db = user_db_tuple
    
    try:
        query = db.query(OvertimeRequest)
        
        # Apply filters
        if filter_params.start_date:
            start_date = datetime.strptime(filter_params.start_date, "%Y-%m-%d").date()
            query = query.filter(OvertimeRequest.date >= start_date)
        
        if filter_params.end_date:
            end_date = datetime.strptime(filter_params.end_date, "%Y-%m-%d").date()
            query = query.filter(OvertimeRequest.date <= end_date)
        
        if filter_params.status:
            query = query.filter(OvertimeRequest.status == filter_params.status)
        
        if filter_params.user_id:
            query = query.filter(OvertimeRequest.user_id == filter_params.user_id)
        
        overtime_requests = query.all()
        
        # Format response
        result = []
        for request in overtime_requests:
            result.append(OvertimeRequestResponse(
                ot_id=request.ot_id,
                user_id=request.user_id,
                date=request.date.strftime("%Y-%m-%d"),
                hours_requested=request.hours_requested,
                reason=request.reason or "",
                status=request.status,
                approver_id=request.approver_id,
                approved_at=request.approved_at.isoformat() if request.approved_at else None
            ))
        
        return result
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching overtime requests: {str(e)}"
        )

# Get overtime request by ID
@router.get("/{ot_id}", response_model=OvertimeRequestResponse)
def get_overtime_request(
    ot_id: int,
    user_db_tuple: tuple[User, Session] = Depends(PermissionChecker.require_permission_with_db("admin_access"))
):
    """
    Get a specific overtime request by ID.
    
    Requires admin_access permission.
    """
    # Unpack the tuple
    current_user, db = user_db_tuple
    
    try:
        overtime_request = db.query(OvertimeRequest).filter(
            OvertimeRequest.ot_id == ot_id
        ).first()
        
        if not overtime_request:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Overtime request not found"
            )
        
        return OvertimeRequestResponse(
            ot_id=overtime_request.ot_id,
            user_id=overtime_request.user_id,
            date=overtime_request.date.strftime("%Y-%m-%d"),
            hours_requested=overtime_request.hours_requested,
            reason=overtime_request.reason or "",
            status=overtime_request.status,
            approver_id=overtime_request.approver_id,
            approved_at=overtime_request.approved_at.isoformat() if overtime_request.approved_at else None
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching overtime request: {str(e)}"
        )

# Create new overtime request
@router.post("/", response_model=Dict[str, str])
def create_overtime_request(
    overtime_request: OvertimeRequestForm,
    user_db_tuple: tuple[User, Session] = Depends(PermissionChecker.require_permission_with_db("employee_access"))
):
    """
    Create a new overtime request.
    
    Requires employee_access permission.
    """
    # Unpack the tuple
    current_user, db = user_db_tuple
    
    try:
        # Create new overtime request
        new_overtime_request = OvertimeRequest(
            user_id=current_user.user_id,
            date=datetime.strptime(overtime_request.date, "%Y-%m-%d").date(),
            hours_requested=overtime_request.hours_requested,
            reason=overtime_request.reason or "",
            status=OvertimeStatus.Pending.value
        )
        
        db.add(new_overtime_request)
        db.commit()
        db.refresh(new_overtime_request)
        
        return {"message": "Overtime request created successfully", "ot_id": new_overtime_request.ot_id}
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid date format: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating overtime request: {str(e)}"
        )

# Update overtime request
@router.put("/{ot_id}", response_model=OvertimeRequestResponse)
def update_overtime_request(
    ot_id: int,
    overtime_request: OvertimeUpdateForm,
    user_db_tuple: tuple[User, Session] = Depends(PermissionChecker.require_permission_with_db("employee_access"))
):
    """
    Update an existing overtime request.
    
    Requires employee_access permission.
    """
    # Unpack the tuple
    current_user, db = user_db_tuple
    
    try:
        existing_request = db.query(OvertimeRequest).filter(
            OvertimeRequest.ot_id == ot_id
        ).first()
        
        if not existing_request:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Overtime request not found"
            )
        
        # Check if user owns the request
        if existing_request.user_id != current_user.user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only update your own overtime requests"
            )
        
        # Check if request is still pending
        if existing_request.status != OvertimeStatus.Pending.value:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Only pending requests can be updated"
            )
        
        # Update request
        existing_request.hours_requested = overtime_request.hours_requested
        existing_request.reason = overtime_request.reason or existing_request.reason
        
        db.commit()
        
        return OvertimeRequestResponse(
            ot_id=existing_request.ot_id,
            user_id=existing_request.user_id,
            date=existing_request.date.strftime("%Y-%m-%d"),
            hours_requested=existing_request.hours_requested,
            reason=existing_request.reason or "",
            status=existing_request.status,
            approver_id=existing_request.approver_id,
            approved_at=existing_request.approved_at.isoformat() if existing_request.approved_at else None
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating overtime request: {str(e)}"
        )

# Delete overtime request
@router.delete("/{ot_id}")
def delete_overtime_request(
    ot_id: int,
    user_db_tuple: tuple[User, Session] = Depends(PermissionChecker.require_permission_with_db("employee_access"))
):
    """
    Delete an overtime request.
    
    Requires employee_access permission.
    """
    # Unpack the tuple
    current_user, db = user_db_tuple
    
    try:
        existing_request = db.query(OvertimeRequest).filter(
            OvertimeRequest.ot_id == ot_id
        ).first()
        
        if not existing_request:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Overtime request not found"
            )
        
        # Check if user owns the request
        if existing_request.user_id != current_user.user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only delete your own overtime requests"
            )
        
        # Check if request is still pending
        if existing_request.status != OvertimeStatus.Pending.value:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Only pending requests can be deleted"
            )
        
        # Delete request
        db.delete(existing_request)
        db.commit()
        
        return {"message": "Overtime request deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error deleting overtime request: {str(e)}"
        )

# Approve overtime request
@router.post("/{ot_id}/approve")
def approve_overtime_request(
    ot_id: int,
    user_db_tuple: tuple[User, Session] = Depends(PermissionChecker.require_permission_with_db("admin_access"))
):
    """
    Approve an overtime request.
    
    Requires admin_access permission.
    """
    # Unpack the tuple
    current_user, db = user_db_tuple
    
    try:
        overtime_request = db.query(OvertimeRequest).filter(
            OvertimeRequest.ot_id == ot_id
        ).first()
        
        if not overtime_request:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Overtime request not found"
            )
        
        if overtime_request.status != OvertimeStatus.Pending.value:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Overtime request is not pending"
            )
        
        overtime_request.status = OvertimeStatus.Approved.value
        overtime_request.approver_id = current_user.user_id
        overtime_request.approved_at = datetime.utcnow()
        
        db.commit()
        
        return {"message": "Overtime request approved successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error approving overtime request: {str(e)}"
        )

# Reject overtime request
@router.post("/{ot_id}/reject")
def reject_overtime_request(
    ot_id: int,
    user_db_tuple: tuple[User, Session] = Depends(PermissionChecker.require_permission_with_db("admin_access"))
):
    """
    Reject an overtime request.
    
    Requires admin_access permission.
    """
    # Unpack the tuple
    current_user, db = user_db_tuple
    
    try:
        overtime_request = db.query(OvertimeRequest).filter(
            OvertimeRequest.ot_id == ot_id
        ).first()
        
        if not overtime_request:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Overtime request not found"
            )
        
        if overtime_request.status != OvertimeStatus.Pending.value:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Overtime request is not pending"
            )
        
        overtime_request.status = OvertimeStatus.Rejected.value
        overtime_request.approver_id = current_user.user_id
        overtime_request.approved_at = datetime.utcnow()
        
        db.commit()
        
        return {"message": "Overtime request rejected successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error rejecting overtime request: {str(e)}"
        )

# Get overtime statistics
@router.get("/stats/summary", response_model=OvertimeStats)
def get_overtime_stats_summary(
    user_db_tuple: tuple[User, Session] = Depends(PermissionChecker.require_permission_with_db("admin_access"))
):
    """
    Get overtime request statistics summary.
    
    Requires admin_access permission.
    """
    # Unpack the tuple
    current_user, db = user_db_tuple
    
    try:
        # Get counts by status
        pending_count = db.query(OvertimeRequest).filter(
            OvertimeRequest.status == OvertimeStatus.Pending.value
        ).count()
        
        approved_count = db.query(OvertimeRequest).filter(
            OvertimeRequest.status == OvertimeStatus.Approved.value
        ).count()
        
        rejected_count = db.query(OvertimeRequest).filter(
            OvertimeRequest.status == OvertimeStatus.Rejected.value
        ).count()
        
        return OvertimeStats(
            pending=pending_count,
            approved=approved_count,
            rejected=rejected_count
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching overtime stats: {str(e)}"
        )

# Get user's overtime requests
@router.get("/user/{user_id}", response_model=List[OvertimeRequestResponse])
def get_user_overtime_requests(
    user_id: int,
    user_db_tuple: tuple[User, Session] = Depends(PermissionChecker.require_permission_with_db("employee_access"))
):
    """
    Get overtime requests for a specific user.
    
    Requires employee_access permission. Users can only view their own requests.
    """
    # Unpack the tuple
    current_user, db = user_db_tuple
    
    try:
        # Check if user is accessing their own requests
        if current_user.user_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only view your own overtime requests"
            )
        
        overtime_requests = db.query(OvertimeRequest).filter(
            OvertimeRequest.user_id == user_id
        ).all()
        
        # Format response
        result = []
        for request in overtime_requests:
            result.append(OvertimeRequestResponse(
                ot_id=request.ot_id,
                user_id=request.user_id,
                date=request.date.strftime("%Y-%m-%d"),
                hours_requested=request.hours_requested,
                reason=request.reason or "",
                status=request.status,
                approver_id=request.approver_id,
                approved_at=request.approved_at.isoformat() if request.approved_at else None
            ))
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching user overtime requests: {str(e)}"
        )