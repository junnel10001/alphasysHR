"""
Export Router

Provides API endpoints for exporting HR data in various formats.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Response
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
from datetime import datetime, date
import os
import tempfile

from backend.database import get_db
from backend.services.export_service import ExportService
from backend.models import User, Department, Payroll, OvertimeRequest, ActivityLog
from backend.middleware.rbac import PermissionChecker, get_current_user
from pydantic import BaseModel, Field

router = APIRouter(prefix="/export", tags=["export"])


class ExportRequest(BaseModel):
    """Request model for export operations"""
    data_type: str = Field(..., description="Type of data to export (employees, payroll, overtime, activities, all)")
    format_type: str = Field(..., description="Export format (csv, excel, pdf, zip)")
    start_date: Optional[date] = Field(None, description="Start date for filtering")
    end_date: Optional[date] = Field(None, description="End date for filtering")
    department_id: Optional[int] = Field(None, description="Department ID for filtering")
    user_id: Optional[int] = Field(None, description="User ID for filtering")


class ExportResponse(BaseModel):
    """Response model for export operations"""
    success: bool
    message: str
    file_path: Optional[str] = None
    file_name: Optional[str] = None
    file_size: Optional[int] = None
    error: Optional[str] = None


class ExportStats(BaseModel):
    """Export statistics response"""
    total_exports: int
    successful_exports: int
    failed_exports: int
    available_formats: List[str]
    available_data_types: List[str]


@router.get("/stats", response_model=ExportStats, summary="Get Export Statistics", description="Retrieve statistics about available exports including total exports, successful exports, failed exports, available formats, and available data types.")
def get_export_stats(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> ExportStats:
    """Get export statistics - requires authentication
    
    Args:
        current_user: The authenticated user from the JWT token
        db: Database session
        
    Returns:
        ExportStats: Statistics about export operations
        
    Raises:
        HTTPException: If there's an error retrieving statistics
    """
    try:
        export_service = ExportService(db)
        
        # Get supported formats and data types
        available_formats = export_service.get_export_formats()
        available_data_types = export_service.get_export_data_types()
        
        # This would be implemented in a real system with tracking
        total_exports = 0
        successful_exports = 0
        failed_exports = 0
        
        return ExportStats(
            total_exports=total_exports,
            successful_exports=successful_exports,
            failed_exports=failed_exports,
            available_formats=available_formats,
            available_data_types=available_data_types
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting export stats: {str(e)}"
        )


@router.post("/export", response_model=ExportResponse, summary="Export HR Data", description="Export HR data in various formats including CSV, Excel, PDF, JSON, and ZIP. Supports filtering by date range, department, and user.")
def export_data(
    request: ExportRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Export HR data - requires export permission
    
    Args:
        request: Export request containing data type, format type, and filters
        current_user: The authenticated user from the JWT token
        db: Database session
        
    Returns:
        ExportResponse: Response containing export operation result and file information
        
    Raises:
        HTTPException: If export parameters are invalid or export fails
    """
    # Check if user has export permission
    if not PermissionChecker.user_has_permission(current_user, "export_data", db):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Export permission required"
        )
    """Export HR data in specified format"""
    try:
        export_service = ExportService(db)
        
        # Validate request parameters
        if not export_service.validate_export_params(request.data_type, request.format_type):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid export parameters"
            )
        
        # Prepare filters
        filters = {}
        if request.start_date:
            filters['start_date'] = request.start_date
        if request.end_date:
            filters['end_date'] = request.end_date
        if request.department_id:
            filters['department_id'] = request.department_id
        if request.user_id:
            filters['user_id'] = request.user_id
        
        # Perform export
        if request.data_type == 'employees':
            file_path = export_service.export_employees(request.format_type, filters)
        elif request.data_type == 'payroll':
            file_path = export_service.export_payroll(request.format_type, filters)
        elif request.data_type == 'overtime':
            file_path = export_service.export_overtime(request.format_type, filters)
        elif request.data_type == 'activities':
            file_path = export_service.export_activities(request.format_type, filters)
        elif request.data_type == 'all':
            file_path = export_service.export_all_data(request.format_type, filters)
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid data type"
            )
        
        # Get file information
        file_name = os.path.basename(file_path)
        file_size = os.path.getsize(file_path) if os.path.exists(file_path) else 0
        
        return ExportResponse(
            success=True,
            message=f"Successfully exported {request.data_type} data as {request.format_type}",
            file_path=file_path,
            file_name=file_name,
            file_size=file_size
        )
        
    except HTTPException:
        raise
    except Exception as e:
        return ExportResponse(
            success=False,
            message=f"Export failed: {str(e)}",
            error=str(e)
        )


@router.get("/download/{file_path:path}", summary="Download Exported File", description="Download an exported file. The file can be in various formats including CSV, Excel, PDF, JSON, or ZIP.")
def download_file(
    file_path: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Download exported file - requires download permission
    
    Args:
        file_path: Path to the exported file
        current_user: The authenticated user from the JWT token
        db: Database session
        
    Returns:
        Response: File download response with appropriate content type
        
    Raises:
        HTTPException: If file not found or download permission missing
    """
    # Check if user has download permission
    if not PermissionChecker.user_has_permission(current_user, "download_files", db):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Download permission required"
        )
    """Download exported file"""
    try:
        export_service = ExportService(db)
        
        # Check if file exists
        full_path = os.path.join(os.getcwd(), file_path)
        if not os.path.exists(full_path):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="File not found"
            )
        
        # Read file content
        with open(full_path, 'rb') as file:
            file_content = file.read()
        
        # Determine content type based on file extension
        file_ext = os.path.splitext(file_path)[1].lower()
        
        if file_ext == '.csv':
            media_type = 'text/csv'
        elif file_ext == '.xlsx' or file_ext == '.xls':
            media_type = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        elif file_ext == '.pdf':
            media_type = 'application/pdf'
        elif file_ext == '.zip':
            media_type = 'application/zip'
        else:
            media_type = 'application/octet-stream'
        
        # Return file for download
        return Response(
            content=file_content,
            media_type=media_type,
            headers={
                "Content-Disposition": f"attachment; filename={os.path.basename(file_path)}",
                "Content-Type": media_type
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to download file: {str(e)}"
        )


@router.get("/view/{file_path:path}", summary="View Exported File", description="View an exported file in the browser. The file can be in various formats including CSV, Excel, PDF, JSON, or ZIP.")
def view_file(
    file_path: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """View exported file in browser - requires view permission
    
    Args:
        file_path: Path to the exported file
        current_user: The authenticated user from the JWT token
        db: Database session
        
    Returns:
        Response: File view response with appropriate content type
        
    Raises:
        HTTPException: If file not found or view permission missing
    """
    # Check if user has view permission
    if not PermissionChecker.user_has_permission(current_user, "view_files", db):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="View permission required"
        )
    """View exported file in browser"""
    try:
        export_service = ExportService(db)
        
        # Check if file exists
        full_path = os.path.join(os.getcwd(), file_path)
        if not os.path.exists(full_path):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="File not found"
            )
        
        # Read file content
        with open(full_path, 'rb') as file:
            file_content = file.read()
        
        # Determine content type based on file extension
        file_ext = os.path.splitext(file_path)[1].lower()
        
        if file_ext == '.csv':
            media_type = 'text/csv'
        elif file_ext == '.xlsx' or file_ext == '.xls':
            media_type = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        elif file_ext == '.pdf':
            media_type = 'application/pdf'
        elif file_ext == '.zip':
            media_type = 'application/zip'
        else:
            media_type = 'application/octet-stream'
        
        # Return file inline for viewing
        return Response(
            content=file_content,
            media_type=media_type,
            headers={
                "Content-Disposition": f"inline; filename={os.path.basename(file_path)}",
                "Content-Type": media_type
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to view file: {str(e)}"
        )


@router.get("/employees", summary="Get Employees for Export", description="Retrieve employee data for export with optional filtering by department, role, and status. Supports pagination.")
def get_employees_for_export(
    department_id: Optional[int] = None,
    role_id: Optional[int] = None,
    status: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> List[Dict[str, Any]]:
    """Get employee data for export - requires employee_export permission
    
    Args:
        department_id: Optional department ID to filter by
        role_id: Optional role ID to filter by
        status: Optional employee status to filter by
        skip: Number of records to skip for pagination
        limit: Maximum number of records to return
        current_user: The authenticated user from the JWT token
        db: Database session
        
    Returns:
        List[Dict[str, Any]]: List of employee records for export
        
    Raises:
        HTTPException: If employee export permission is missing
    """
    # Check if user has employee export permission
    if not PermissionChecker.user_has_permission(current_user, "employee_export", db):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Employee export permission required"
        )
    """Get employee data for export"""
    try:
        export_service = ExportService(db)
        
        # Apply filters
        filters = {}
        if department_id:
            filters['department_id'] = department_id
        if role_id:
            filters['role_id'] = role_id
        if status:
            filters['status'] = status
        
        # Get employee data using public method
        employees = export_service._get_employee_data(filters)
        
        # Apply pagination
        paginated_employees = employees[skip:skip + limit]
        
        return paginated_employees
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting employees for export: {str(e)}"
        )


@router.get("/payroll", summary="Get Payroll for Export", description="Retrieve payroll data for export with optional filtering by date range, department, and user. Supports pagination.")
def get_payroll_for_export(
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    department_id: Optional[int] = None,
    user_id: Optional[int] = None,
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> List[Dict[str, Any]]:
    """Get payroll data for export - requires payroll_export permission
    
    Args:
        start_date: Optional start date for filtering payroll records
        end_date: Optional end date for filtering payroll records
        department_id: Optional department ID to filter by
        user_id: Optional user ID to filter by
        skip: Number of records to skip for pagination
        limit: Maximum number of records to return
        current_user: The authenticated user from the JWT token
        db: Database session
        
    Returns:
        List[Dict[str, Any]]: List of payroll records for export
        
    Raises:
        HTTPException: If payroll export permission is missing
    """
    # Check if user has payroll export permission
    if not PermissionChecker.user_has_permission(current_user, "payroll_export", db):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Payroll export permission required"
        )
    """Get payroll data for export"""
    try:
        export_service = ExportService(db)
        
        # Apply filters
        filters = {}
        if start_date:
            filters['start_date'] = start_date
        if end_date:
            filters['end_date'] = end_date
        if department_id:
            filters['department_id'] = department_id
        if user_id:
            filters['user_id'] = user_id
        
        # Get payroll data using public method
        payrolls = export_service._get_payroll_data(filters)
        
        # Apply pagination
        paginated_payrolls = payrolls[skip:skip + limit]
        
        return paginated_payrolls
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting payroll for export: {str(e)}"
        )


@router.get("/overtime", summary="Get Overtime for Export", description="Retrieve overtime data for export with optional filtering by date range, status, and user. Supports pagination.")
def get_overtime_for_export(
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    status: Optional[str] = None,
    user_id: Optional[int] = None,
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> List[Dict[str, Any]]:
    """Get overtime data for export - requires overtime_export permission
    
    Args:
        start_date: Optional start date for filtering overtime records
        end_date: Optional end date for filtering overtime records
        status: Optional overtime status to filter by
        user_id: Optional user ID to filter by
        skip: Number of records to skip for pagination
        limit: Maximum number of records to return
        current_user: The authenticated user from the JWT token
        db: Database session
        
    Returns:
        List[Dict[str, Any]]: List of overtime records for export
        
    Raises:
        HTTPException: If overtime export permission is missing
    """
    # Check if user has overtime export permission
    if not PermissionChecker.user_has_permission(current_user, "overtime_export", db):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Overtime export permission required"
        )
    """Get overtime data for export"""
    try:
        export_service = ExportService(db)
        
        # Apply filters
        filters = {}
        if start_date:
            filters['start_date'] = start_date
        if end_date:
            filters['end_date'] = end_date
        if status:
            filters['status'] = status
        if user_id:
            filters['user_id'] = user_id
        
        # Get overtime data using public method
        overtime = export_service._get_overtime_data(filters)
        
        # Apply pagination
        paginated_overtime = overtime[skip:skip + limit]
        
        return paginated_overtime
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting overtime for export: {str(e)}"
        )


@router.get("/activities")
def get_activities_for_export(
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    user_id: Optional[int] = None,
    action: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> List[Dict[str, Any]]:
    """Get activity data for export - requires activity_export permission
    
    Args:
        start_date: Optional start date for filtering activity records
        end_date: Optional end date for filtering activity records
        user_id: Optional user ID to filter by
        action: Optional action text to filter by (partial match)
        skip: Number of records to skip for pagination
        limit: Maximum number of records to return
        current_user: The authenticated user from the JWT token
        db: Database session
        
    Returns:
        List[Dict[str, Any]]: List of activity records for export
        
    Raises:
        HTTPException: If activity export permission is missing
    """
    # Check if user has activity export permission
    if not PermissionChecker.user_has_permission(current_user, "activity_export", db):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Activity export permission required"
        )
    """Get activity data for export"""
    try:
        export_service = ExportService(db)
        
        # Apply filters
        filters = {}
        if start_date:
            filters['start_date'] = start_date
        if end_date:
            filters['end_date'] = end_date
        if user_id:
            filters['user_id'] = user_id
        if action:
            filters['action'] = action
        
        # Get activity data using public method
        activities = export_service._get_activity_data(filters)
        
        # Apply pagination
        paginated_activities = activities[skip:skip + limit]
        
        return paginated_activities
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting activities for export: {str(e)}"
        )


@router.get("/departments")
def get_departments(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> List[Dict[str, Any]]:
    """Get all departments for export filtering - requires department_view permission"""
    # Check if user has department view permission
    if not PermissionChecker.user_has_permission(current_user, "department_view", db):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Department view permission required"
        )
    """Get all departments for export filtering"""
    try:
        departments = db.query(Department).all()
        
        dept_list = []
        for dept in departments:
            dept_dict = {
                "department_id": dept.department_id,
                "department_name": dept.department_name
            }
            dept_list.append(dept_dict)
        
        return dept_list
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting departments: {str(e)}"
        )


@router.post("/cleanup")
def cleanup_old_exports(
    days_old: int = 30,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Clean up old export files - requires admin permission"""
    # Check if user has admin role or cleanup permission
    if not (PermissionChecker.user_has_permission(current_user, "cleanup_exports", db) or
            user_has_role(current_user, "admin")):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin or cleanup permission required"
        )
    """Clean up old export files"""
    try:
        export_service = ExportService(db)
        
        cleaned_count = export_service.cleanup_old_exports(days_old)
        
        return {
            "success": True,
            "message": f"Cleaned up {cleaned_count} old export files",
            "days_old": days_old,
            "cleaned_count": cleaned_count
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error cleaning up exports: {str(e)}"
        )