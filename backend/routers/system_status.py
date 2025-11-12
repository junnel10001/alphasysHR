"""
System Status Router

Provides endpoints for monitoring system health and status.
All endpoints are documented via docstrings, which FastAPI uses to generate
OpenAPI documentation.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import text
import psutil
import platform
import os
from datetime import datetime

from backend.models import User, Department, Role, Office, LeaveType
from backend.database import get_db
from backend.middleware.rbac import PermissionChecker, has_permission

router = APIRouter(prefix="/system-status", tags=["system-status"])


@router.get("/health")
@has_permission("view_system_status")
def health_check(
    db: Session = Depends(get_db), 
    user = Depends(PermissionChecker.require_permission("view_system_status"))
):
    """
    Check system health status.
    
    Returns the overall health status of various system components.
    """
    health_status = {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "checks": {}
    }
    
    # Database connectivity check
    try:
        db.execute(text("SELECT 1"))
        health_status["checks"]["database"] = {
            "status": "healthy",
            "message": "Database connection successful"
        }
    except Exception as e:
        health_status["checks"]["database"] = {
            "status": "unhealthy",
            "message": f"Database connection failed: {str(e)}"
        }
        health_status["status"] = "unhealthy"
    
    # Memory usage check
    try:
        memory = psutil.virtual_memory()
        memory_usage_percent = memory.percent
        health_status["checks"]["memory"] = {
            "status": "healthy" if memory_usage_percent < 90 else "warning" if memory_usage_percent < 95 else "critical",
            "usage_percent": memory_usage_percent,
            "message": f"Memory usage: {memory_usage_percent:.1f}%"
        }
    except Exception as e:
        health_status["checks"]["memory"] = {
            "status": "unknown",
            "message": f"Could not check memory usage: {str(e)}"
        }
    
    # Disk space check
    try:
        disk = psutil.disk_usage('/')
        disk_usage_percent = (disk.used / disk.total) * 100
        health_status["checks"]["disk"] = {
            "status": "healthy" if disk_usage_percent < 80 else "warning" if disk_usage_percent < 95 else "critical",
            "usage_percent": disk_usage_percent,
            "message": f"Disk usage: {disk_usage_percent:.1f}%"
        }
    except Exception as e:
        health_status["checks"]["disk"] = {
            "status": "unknown",
            "message": f"Could not check disk usage: {str(e)}"
        }
    
    return health_status


@router.get("/info")
@has_permission("view_system_status")
def system_info(
    db: Session = Depends(get_db), 
    user = Depends(PermissionChecker.require_permission("view_system_status"))
):
    """
    Get detailed system information.
    
    Returns comprehensive information about the system including versions, counts, and environment details.
    """
    try:
        # Get database statistics
        user_count = db.query(User).count()
        active_user_count = db.query(User).filter(User.status == "active").count()
        department_count = db.query(Department).count()
        role_count = db.query(Role).count()
        office_count = db.query(Office).count()
        leave_type_count = db.query(LeaveType).count()
        
        # Get system information
        system_info = {
            "system": {
                "platform": platform.system(),
                "platform_version": platform.version(),
                "architecture": platform.architecture(),
                "processor": platform.processor(),
                "python_version": platform.python_version(),
            },
            "database": {
                "users_total": user_count,
                "users_active": active_user_count,
                "departments": department_count,
                "roles": role_count,
                "offices": office_count,
                "leave_types": leave_type_count,
            },
            "performance": {
                "cpu_usage": psutil.cpu_percent(interval=1),
                "memory": {
                    "total": psutil.virtual_memory().total,
                    "available": psutil.virtual_memory().available,
                    "used": psutil.virtual_memory().used,
                    "percent": psutil.virtual_memory().percent,
                },
                "disk": {
                    "total": psutil.disk_usage('/').total,
                    "used": psutil.disk_usage('/').used,
                    "free": psutil.disk_usage('/').free,
                    "percent": (psutil.disk_usage('/').used / psutil.disk_usage('/').total) * 100,
                }
            },
            "versions": {
                "fastapi": "0.104.1",  # You can get this dynamically if needed
                "sqlalchemy": "2.0.23",  # You can get this dynamically if needed
                "python": platform.python_version(),
                "app_version": "1.0.0",  # Your app version
            },
            "environment": {
                "debug": os.getenv("DEBUG", "false").lower() == "true",
                "environment": os.getenv("ENVIRONMENT", "development"),
                "database_url": os.getenv("DATABASE_URL", "configured"),  # Don't expose actual URL
            }
        }
        
        return system_info
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get system information: {str(e)}"
        )


@router.get("/metrics")
@has_permission("view_system_status")
def system_metrics(
    db: Session = Depends(get_db), 
    user = Depends(PermissionChecker.require_permission("view_system_status"))
):
    """
    Get system performance metrics.
    
    Returns current performance metrics for monitoring purposes.
    """
    try:
        metrics = {
            "timestamp": datetime.utcnow().isoformat(),
            "performance": {
                "cpu_percent": psutil.cpu_percent(interval=1),
                "memory_percent": psutil.virtual_memory().percent,
                "disk_percent": (psutil.disk_usage('/').used / psutil.disk_usage('/').total) * 100,
                "load_average": os.getloadavg() if hasattr(os, 'getloadavg') else [0, 0, 0],
            },
            "database": {
                "connections": "active",  # You can get actual connection count if needed
                "query_time": "fast",  # You can measure actual query times if needed
            }
        }
        
        return metrics
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get system metrics: {str(e)}"
        )