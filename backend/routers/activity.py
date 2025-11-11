from fastapi import APIRouter, Depends, HTTPException, Query, Path, WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session
from typing import Optional, List, Dict, Any
from datetime import datetime, date, time
import json
import pandas as pd
import asyncio

from backend.database import get_db
from backend.models import ActivityLog, User
from backend.services.activity_service import ActivityService
from backend.utils.auth import get_current_user
from backend.utils.logger import activity_logger, setup_activity_logging
from backend.utils.log_aggregator import log_aggregator, SearchResult
from backend.utils.dashboard_integration import dashboard_integration

router = APIRouter(prefix="/activity", tags=["activity"])

# Initialize logging when router is imported
setup_activity_logging()

@router.get("/logs", response_model=None)
def get_activity_logs(
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    user_id: Optional[int] = Query(None, ge=1),
    action: Optional[str] = Query(None),
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    current_user: User = Depends(get_current_user)
):
    """Get activity logs with optional filters"""
    try:
        # Log the API call
        activity_logger.log_activity(
            user_id=current_user.user_id,
            action="get_activity_logs",
            details={
                "limit": limit,
                "offset": offset,
                "user_id_filter": user_id,
                "action_filter": action,
                "has_date_filter": bool(start_date and end_date)
            },
            log_to_db=True,
            log_to_file=True
        )
        
        # Get database session using context manager
        from backend.database import get_db
        db = next(get_db())
        try:
            activity_service = ActivityService(db)
            # All database operations are done within the service
        finally:
            db.close()
        
        # Check permissions
        if user_id and user_id != current_user.user_id and not (current_user.role_name == "admin" or current_user.role_name == "manager"):
            raise HTTPException(status_code=403, detail="Not authorized to view this user's activities")
        
        # Apply filters
        if user_id:
            activities = activity_service.get_user_activities(user_id, limit, offset)
        elif action:
            activities = activity_service.get_activities_by_action(action, limit, offset)
        elif start_date and end_date:
            start_datetime = datetime.combine(start_date, time.min)
            end_datetime = datetime.combine(end_date, time.max)
            activities = activity_service.get_activities_by_date_range(start_datetime, end_datetime, limit, offset)
        else:
            # Get all activities if admin/manager, otherwise only current user
            if current_user.role_name in ["admin", "manager"]:
                activities = activity_service.get_all_activities(limit, offset)
            else:
                activities = activity_service.get_user_activities(current_user.user_id, limit, offset)
        
        return {
            "activities": [
                {
                    "log_id": activity.log_id,
                    "user_id": activity.user_id,
                    "action": activity.action,
                    "timestamp": activity.timestamp.isoformat()
                }
                for activity in activities
            ],
            "total": len(activities),
            "limit": limit,
            "offset": offset
        }
    except HTTPException:
        raise
    except Exception as e:
        activity_logger.log_error(e, {
            "endpoint": "get_activity_logs",
            "user_id": current_user.user_id,
            "limit": limit,
            "offset": offset
        })
        raise HTTPException(status_code=500, detail=f"Error fetching activity logs: {str(e)}")

@router.get("/logs/{log_id}", response_model=None)
def get_activity_log(
    log_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get a specific activity log"""
    try:
        # Log the API call
        activity_logger.log_activity(
            user_id=current_user.user_id,
            action="get_activity_log",
            details={"log_id": log_id},
            log_to_db=True,
            log_to_file=True
        )
        
        activity_service = ActivityService(db)
        
        # Get the activity log
        activity = db.query(ActivityLog).filter(ActivityLog.log_id == log_id).first()
        
        if not activity:
            raise HTTPException(status_code=404, detail="Activity log not found")
        
        # Check permissions
        if activity.user_id != current_user.user_id and not (current_user.role_name == "admin" or current_user.role_name == "manager"):
            raise HTTPException(status_code=403, detail="Not authorized to view this activity log")
        
        return {
            "log_id": activity.log_id,
            "user_id": activity.user_id,
            "action": activity.action,
            "timestamp": activity.timestamp.isoformat()
        }
    except HTTPException:
        raise
    except Exception as e:
        activity_logger.log_error(e, {
            "endpoint": "get_activity_log",
            "user_id": current_user.user_id,
            "log_id": log_id
        })
        raise HTTPException(status_code=500, detail=f"Error fetching activity log: {str(e)}")

@router.get("/user/{user_id}/activities", response_model=None)
def get_user_activities(
    user_id: int,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get activities for a specific user"""
    try:
        # Log the API call
        activity_logger.log_activity(
            user_id=current_user.user_id,
            action="get_user_activities",
            details={"target_user_id": user_id, "limit": limit, "offset": offset},
            log_to_db=True,
            log_to_file=True
        )
        
        activity_service = ActivityService(db)
        
        # Check permissions
        if user_id != current_user.user_id and not (current_user.role_name == "admin" or current_user.role_name == "manager"):
            raise HTTPException(status_code=403, detail="Not authorized to view this user's activities")
        
        activities = activity_service.get_user_activities(user_id, limit, offset)
        
        return {
            "activities": [
                {
                    "log_id": activity.log_id,
                    "user_id": activity.user_id,
                    "action": activity.action,
                    "timestamp": activity.timestamp.isoformat()
                }
                for activity in activities
            ],
            "total": len(activities),
            "limit": limit,
            "offset": offset
        }
    except HTTPException:
        raise
    except Exception as e:
        activity_logger.log_error(e, {
            "endpoint": "get_user_activities",
            "user_id": current_user.user_id,
            "target_user_id": user_id
        })
        raise HTTPException(status_code=500, detail=f"Error fetching user activities: {str(e)}")

@router.get("/stats", response_model=None)
def get_activity_stats(
    user_id: Optional[int] = Query(None, ge=1),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get activity statistics"""
    try:
        # Log the API call
        activity_logger.log_activity(
            user_id=current_user.user_id,
            action="get_activity_stats",
            details={"target_user_id": user_id},
            log_to_db=True,
            log_to_file=True
        )
        
        activity_service = ActivityService(db)
        
        # Check permissions
        if user_id and user_id != current_user.user_id and not (current_user.role_name == "admin" or current_user.role_name == "manager"):
            raise HTTPException(status_code=403, detail="Not authorized to view this user's stats")
        
        if user_id:
            stats = activity_service.get_user_activity_stats(user_id)
            target_user_id = user_id
        else:
            stats = activity_service.get_activity_dashboard_stats()
            target_user_id = current_user.user_id
        
        return {
            "stats": stats,
            "user_id": target_user_id
        }
    except HTTPException:
        raise
    except Exception as e:
        activity_logger.log_error(e, {
            "endpoint": "get_activity_stats",
            "user_id": current_user.user_id,
            "target_user_id": user_id
        })
        raise HTTPException(status_code=500, detail=f"Error fetching activity stats: {str(e)}")

@router.delete("/logs/cleanup", response_model=None)
async def cleanup_old_activities(
    days_to_keep: int = Query(90, ge=1, le=365),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Clean up old activity logs (admin only)"""
    try:
        # Log the API call
        activity_logger.log_activity(
            user_id=current_user.user_id,
            action="cleanup_old_activities",
            details={"days_to_keep": days_to_keep},
            log_to_db=True,
            log_to_file=True
        )
        
        if current_user.role_name not in ["admin", "manager"]:
            raise HTTPException(status_code=403, detail="Not authorized to cleanup activities")
        
        activity_service = ActivityService(db)
        deleted_count = activity_service.clear_old_activities(days_to_keep)
        
        # Log the cleanup result
        activity_logger.log_activity(
            user_id=current_user.user_id,
            action="cleanup_completed",
            details={"deleted_count": deleted_count, "days_kept": days_to_keep},
            log_to_db=True,
            log_to_file=True
        )
        
        return {
            "message": f"Successfully deleted {deleted_count} old activity logs",
            "days_kept": days_to_keep
        }
    except HTTPException:
        raise
    except Exception as e:
        activity_logger.log_error(e, {
            "endpoint": "cleanup_old_activities",
            "user_id": current_user.user_id,
            "days_to_keep": days_to_keep
        })
        raise HTTPException(status_code=500, detail=f"Error cleaning up activities: {str(e)}")

@router.get("/recent", response_model=None)
def get_recent_activities(
    limit: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get recent activities"""
    try:
        # Log the API call
        activity_logger.log_activity(
            user_id=current_user.user_id,
            action="get_recent_activities",
            details={"limit": limit},
            log_to_db=True,
            log_to_file=True
        )
        
        activity_service = ActivityService(db)
        
        activities = activity_service.get_recent_activities(limit)
        
        return {
            "activities": [
                {
                    "log_id": activity.log_id,
                    "user_id": activity.user_id,
                    "action": activity.action,
                    "timestamp": activity.timestamp.isoformat()
                }
                for activity in activities
            ],
            "total": len(activities),
            "limit": limit
        }
    except HTTPException:
        raise
    except Exception as e:
        activity_logger.log_error(e, {
            "endpoint": "get_recent_activities",
            "user_id": current_user.user_id,
            "limit": limit
        })
        raise HTTPException(status_code=500, detail=f"Error fetching recent activities: {str(e)}")

@router.get("/search", response_model=None)
def search_activity_logs(
    query: str = Query(..., description="Search query string"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of results"),
    offset: int = Query(0, ge=0, description="Offset for pagination"),
    current_user: User = Depends(get_current_user)
):
    """Search activity logs with full-text search using log aggregation."""
    try:
        # Log the API call
        activity_logger.log_activity(
            user_id=current_user.user_id,
            action="search_activity_logs",
            details={
                "query": query,
                "limit": limit,
                "offset": offset
            },
            log_to_db=True,
            log_to_file=True
        )
        
        # Use log aggregator for enhanced search
        search_results = log_aggregator.search_logs(
            query=query,
            limit=limit,
            offset=offset
        )
        
        # Log search metrics
        activity_logger.log_activity(
            user_id=current_user.user_id,
            action="log_aggregation_search",
            details={
                "search_query": query,
                "search_results": search_results.total_count,
                "search_time": search_results.search_time,
                "files_searched": search_results.files_searched
            },
            log_to_db=True,
            log_to_file=True
        )
        
        # Format results for API response
        formatted_results = []
        for entry in search_results.entries:
            formatted_results.append({
                "timestamp": entry.timestamp.isoformat(),
                "level": entry.level,
                "module": entry.module,
                "function": entry.function,
                "line": entry.line,
                "message": entry.message,
                "file_path": entry.file_path
            })
        
        return {
            "results": formatted_results,
            "total_count": search_results.total_count,
            "search_time": search_results.search_time,
            "files_searched": search_results.files_searched,
            "query": search_results.query,
            "filters": search_results.filters
        }
        
    except HTTPException:
        raise
    except Exception as e:
        activity_logger.log_error(e, {
            "endpoint": "search_activity_logs",
            "user_id": current_user.user_id,
            "query": query
        })
        raise HTTPException(status_code=500, detail=f"Error searching activity logs: {str(e)}")

@router.get("/export/{format}", response_model=None)
def export_activity_logs(
    format: str = Path(..., regex="^(json|csv)$", description="Export format (json or csv)"),
    limit: int = Query(1000, ge=1, le=10000, description="Maximum number of logs to export"),
    current_user: User = Depends(get_current_user)
):
    """Export activity logs in specified format using log aggregation."""
    try:
        # Log the API call
        activity_logger.log_activity(
            user_id=current_user.user_id,
            action="export_activity_logs",
            details={
                "format": format,
                "limit": limit
            },
            log_to_db=True,
            log_to_file=True
        )
        
        # Use log aggregator for enhanced export
        search_results = log_aggregator.search_logs(
            query="activity",
            limit=limit
        )
        
        # Create output filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_filename = f"activity_export_{timestamp}.{format}"
        output_path = Path("logs/exports") / output_filename
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Export search results
        export_success = log_aggregator.export_search_results(
            results=search_results,
            output_path=output_path,
            format=format
        )
        
        if export_success:
            activity_logger.log_activity(
                user_id=current_user.user_id,
                action="log_aggregation_export_success",
                details={
                    "format": format,
                    "export_path": str(output_path),
                    "exported_count": search_results.total_count
                },
                log_to_db=True,
                log_to_file=True
            )
            
            return {
                "message": "Export completed successfully",
                "file_path": str(output_path),
                "format": format,
                "exported_count": search_results.total_count
            }
        else:
            activity_logger.log_activity(
                user_id=current_user.user_id,
                action="log_aggregation_export_failed",
                details={
                    "format": format,
                    "export_path": str(output_path)
                },
                log_to_db=True,
                log_to_file=True
            )
            raise HTTPException(
                status_code=500,
                detail="Failed to export logs"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        activity_logger.log_error(e, {
            "endpoint": "export_activity_logs",
            "user_id": current_user.user_id,
            "format": format
        })
        raise HTTPException(status_code=500, detail=f"Export failed: {str(e)}")

@router.get("/dashboard/stats", response_model=None)
def get_dashboard_stats(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get dashboard statistics for activity monitoring with log aggregation."""
    try:
        # Log the API call
        activity_logger.log_activity(
            user_id=current_user.user_id,
            action="get_dashboard_stats",
            details={"dashboard": "activity"},
            log_to_db=True,
            log_to_file=True
        )
        
        activity_service = ActivityService(db)
        
        # Get database stats
        db_stats = activity_service.get_activity_dashboard_stats()
        
        # Get log aggregation stats
        log_stats = log_aggregator.get_log_stats(hours=24)
        
        # Get cache info
        cache_info = log_aggregator.get_cache_info()
        
        # Log dashboard metrics
        activity_logger.log_activity(
            user_id=current_user.user_id,
            action="dashboard_stats_retrieved",
            details={
                "db_stats": db_stats,
                "log_stats": log_stats,
                "cache_info": cache_info
            },
            log_to_db=True,
            log_to_file=True
        )
        
        # Combine stats for dashboard
        dashboard_stats = {
            "database_stats": db_stats,
            "log_aggregation_stats": log_stats,
            "cache_info": cache_info,
            "timestamp": datetime.now().isoformat()
        }
        
        return dashboard_stats
        
    except HTTPException:
        raise
    except Exception as e:
        activity_logger.log_error(e, {
            "endpoint": "get_dashboard_stats",
            "user_id": current_user.user_id
        })
        raise HTTPException(status_code=500, detail=f"Error fetching dashboard stats: {str(e)}")

@router.websocket("/ws/dashboard")
async def websocket_dashboard_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time dashboard updates."""
    client_id = f"websocket_{id(websocket)}"
    
    try:
        # Accept the WebSocket connection
        await websocket.accept()
        
        # Add client to dashboard
        dashboard_integration.add_websocket_client(client_id, websocket)
        
        # Log the connection
        activity_logger.log_activity(
            user_id=0,  # System activity
            action="websocket_dashboard_connected",
            details={"client_id": client_id},
            log_to_db=True,
            log_to_file=True
        )
        
        # Send initial dashboard data
        initial_data = dashboard_integration.get_dashboard_data()
        await websocket.send_text(json.dumps({
            "type": "initial_data",
            "data": initial_data
        }))
        
        # Keep the connection alive and listen for messages
        while True:
            try:
                # Wait for messages (this keeps the connection open)
                data = await websocket.receive_text()
                
                # Parse incoming message
                try:
                    message = json.loads(data)
                    
                    if message.get("type") == "ping":
                        # Respond to ping
                        await websocket.send_text(json.dumps({"type": "pong"}))
                    
                    elif message.get("type") == "get_data":
                        # Send current dashboard data
                        dashboard_data = dashboard_integration.get_dashboard_data()
                        await websocket.send_text(json.dumps({
                            "type": "dashboard_data",
                            "data": dashboard_data
                        }))
                    
                    elif message.get("type") == "record_activity":
                        # Record activity from client
                        activity_data = message.get("data", {})
                        dashboard_integration.record_activity(
                            user_id=activity_data.get("user_id", 0),
                            action=activity_data.get("action", ""),
                            details=activity_data.get("details", {}),
                            source="websocket"
                        )
                        
                        # Send confirmation
                        await websocket.send_text(json.dumps({
                            "type": "activity_recorded",
                            "success": True
                        }))
                
                except json.JSONDecodeError:
                    await websocket.send_text(json.dumps({
                        "type": "error",
                        "message": "Invalid JSON format"
                    }))
                
            except WebSocketDisconnect:
                break
                
    except WebSocketDisconnect:
        # Client disconnected
        dashboard_integration.remove_websocket_client(client_id)
        
        activity_logger.log_activity(
            user_id=0,  # System activity
            action="websocket_dashboard_disconnected",
            details={"client_id": client_id},
            log_to_db=True,
            log_to_file=True
        )
        
    except Exception as e:
        dashboard_integration.remove_websocket_client(client_id)
        
        activity_logger.log_error(e, {
            "endpoint": "websocket_dashboard_endpoint",
            "client_id": client_id
        })

@router.get("/dashboard/data", response_model=None)
def get_dashboard_data(
    current_user: User = Depends(get_current_user)
):
    """Get current dashboard data."""
    try:
        # Log the API call
        activity_logger.log_activity(
            user_id=current_user.user_id,
            action="get_dashboard_data",
            details={"dashboard": "realtime"},
            log_to_db=True,
            log_to_file=True
        )
        
        dashboard_data = dashboard_integration.get_dashboard_data()
        
        return dashboard_data
        
    except Exception as e:
        activity_logger.log_error(e, {
            "endpoint": "get_dashboard_data",
            "user_id": current_user.user_id
        })
        raise HTTPException(status_code=500, detail=f"Error fetching dashboard data: {str(e)}")


@router.post("/dashboard/activity")
def record_dashboard_activity(
    activity_data: Dict[str, Any],
    current_user: User = Depends(get_current_user)
):
    """Record an activity for the dashboard."""
    try:
        # Validate required fields
        if "action" not in activity_data:
            raise HTTPException(status_code=400, detail="Action is required")
        
        # Log the API call
        activity_logger.log_activity(
            user_id=current_user.user_id,
            action="record_dashboard_activity",
            details={
                "action": activity_data["action"],
                "has_details": bool(activity_data.get("details"))
            },
            log_to_db=True,
            log_to_file=True
        )
        
        # Record activity in dashboard
        dashboard_integration.record_activity(
            user_id=current_user.user_id,
            action=activity_data["action"],
            details=activity_data.get("details", {}),
            source="api"
        )
        
        return {
            "message": "Activity recorded successfully",
            "action": activity_data["action"],
            "timestamp": datetime.now().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        activity_logger.log_error(e, {
            "endpoint": "record_dashboard_activity",
            "user_id": current_user.user_id,
            "activity_data": activity_data
        })
        raise HTTPException(status_code=500, detail=f"Error recording dashboard activity: {str(e)}")

@router.get("/dashboard/export/{format}", response_model=None)
def export_dashboard_data(
    format: str = Path(..., regex="^(json|csv)$", description="Export format (json or csv)"),
    hours: int = Query(24, ge=1, le=168, description="Number of hours of data to export"),
    current_user: User = Depends(get_current_user)
):
    """Export dashboard data in specified format."""
    try:
        # Log the API call
        activity_logger.log_activity(
            user_id=current_user.user_id,
            action="export_dashboard_data",
            details={
                "format": format,
                "hours": hours
            },
            log_to_db=True,
            log_to_file=True
        )
        
        # Create output filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_filename = f"dashboard_export_{timestamp}.{format}"
        output_path = Path("logs/exports") / output_filename
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Get dashboard data for export
        dashboard_data = dashboard_integration.get_dashboard_data()
        activity_history = dashboard_integration.get_activity_history(hours=hours)
        
        # Prepare export data
        export_data = {
            "export_timestamp": datetime.now().isoformat(),
            "format": format,
            "time_period_hours": hours,
            "dashboard_data": dashboard_data,
            "activity_history": activity_history
        }
        
        # Export based on format
        if format.lower() == "json":
            with open(output_path, 'w') as f:
                json.dump(export_data, f, indent=2, default=str)
        
        elif format.lower() == "csv":
            # Convert to DataFrame for CSV export
            df_data = []
            
            # Add dashboard metrics
            for key, value in dashboard_data.items():
                if key != "recent_activities" and key != "metrics_summary":
                    df_data.append({
                        "type": "dashboard_metric",
                        "metric": key,
                        "value": str(value)
                    })
            
            # Add activities
            for activity in activity_history:
                df_data.append({
                    "type": "activity",
                    "timestamp": activity["timestamp"],
                    "user_id": activity["user_id"],
                    "action": activity["action"],
                    "source": activity["source"]
                })
            
            df = pd.DataFrame(df_data)
            df.to_csv(output_path, index=False)
        
        else:
            raise HTTPException(status_code=400, detail=f"Unsupported export format: {format}")
        
        # Log export success
        activity_logger.log_activity(
            user_id=current_user.user_id,
            action="dashboard_export_success",
            details={
                "format": format,
                "export_path": str(output_path),
                "exported_hours": hours,
                "activity_count": len(activity_history)
            },
            log_to_db=True,
            log_to_file=True
        )
        
        return {
            "message": "Dashboard data exported successfully",
            "file_path": str(output_path),
            "format": format,
            "exported_hours": hours,
            "activity_count": len(activity_history)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        activity_logger.log_error(e, {
            "endpoint": "export_dashboard_data",
            "user_id": current_user.user_id,
            "format": format,
            "hours": hours
        })
        raise HTTPException(status_code=500, detail=f"Error exporting dashboard data: {str(e)}")