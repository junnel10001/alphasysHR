from sqlalchemy.orm import Session
from backend.models import ActivityLog
from datetime import datetime, timedelta, time
from typing import Optional, List, Dict, Any
from backend.utils.logger import activity_logger
from backend.utils.performance_monitor import performance_monitor


class ActivityService:
    """Service for managing user activity logs"""
    
    def __init__(self, db: Session):
        self.db = db
        self.logger = activity_logger
        
        # Initialize performance monitoring
        self._setup_performance_monitoring()
    
    def _setup_performance_monitoring(self):
        """Setup performance monitoring for the activity service."""
        # Record service initialization
        performance_monitor.record_metric(
            name="service_initialization",
            value=1,
            unit="count",
            tags={"service": "ActivityService", "event": "initialization"},
            component="activity_service"
        )
        
        # Record histogram for service initialization time
        timer_id = performance_monitor.start_timer("service_initialization")
        # Simulate initialization work
        import time
        time.sleep(0.001)  # Small delay to simulate initialization
        performance_monitor.stop_timer(timer_id)
    
    def log_activity(
        self,
        user_id: int,
        action: str,
        timestamp: Optional[datetime] = None
    ) -> ActivityLog:
        """Log a user activity"""
        
        # Start timer for this operation
        timer_id = performance_monitor.start_timer("log_activity")
        
        try:
            # Log to enhanced logger first
            self.logger.log_activity(
                user_id=user_id,
                action=action,
                details={"source": "database", "service": "ActivityService"},
                log_to_db=False,  # Avoid double logging
                log_to_file=True
            )
            
            # Record creation metrics
            performance_monitor.record_counter(
                name="activity_creation_count",
                value=1,
                tags={"type": "log_activity"},
                component="activity_service"
            )
            
            performance_monitor.record_metric(
                name="activity_created",
                value=1,
                unit="count",
                tags={"user_id": str(user_id), "action": action},
                component="activity_service"
            )
            
            # Then log to database
            activity_log = ActivityLog(
                user_id=user_id,
                action=action,
                timestamp=timestamp or datetime.utcnow()
            )
            
            self.db.add(activity_log)
            self.db.commit()
            self.db.refresh(activity_log)
            
            return activity_log
            
        except Exception as e:
            self.db.rollback()
            performance_monitor.record_metric(
                name="activity_creation_error",
                value=1,
                unit="count",
                tags={"error": "database", "action": action},
                component="activity_service"
            )
            self.logger.log_error(e, {"service": "ActivityService", "method": "log_activity"})
            raise e
        finally:
            # Stop timer
            duration = performance_monitor.stop_timer(timer_id)
            if duration:
                performance_monitor.record_histogram(
                    name="log_activity_duration",
                    value=duration,
                    tags={"type": "database_operation"},
                    component="activity_service"
                )
    
    def get_user_activities(
        self,
        user_id: int,
        limit: int = 50,
        offset: int = 0
    ) -> List[ActivityLog]:
        """Get activities for a specific user"""
        
        # Start timer for this operation
        timer_id = performance_monitor.start_timer("get_user_activities")
        
        try:
            activities = self.db.query(ActivityLog)\
                .filter(ActivityLog.user_id == user_id)\
                .order_by(ActivityLog.timestamp.desc())\
                .offset(offset)\
                .limit(limit)\
                .all()
            
            # Record query metrics
            performance_monitor.record_counter(
                name="activity_query_count",
                value=1,
                tags={"type": "get_user_activities"},
                component="activity_service"
            )
            
            performance_monitor.record_metric(
                name="activity_query_results",
                value=len(activities),
                unit="count",
                tags={"user_id": str(user_id)},
                component="activity_service"
            )
            
            # Log this query for monitoring
            self.logger.log_activity(
                user_id=0,  # System user
                action="get_user_activities",
                details={
                    "target_user_id": user_id,
                    "limit": limit,
                    "offset": offset
                },
                log_to_db=False,
                log_to_file=True
            )
            return activities
            
        except Exception as e:
            performance_monitor.record_metric(
                name="activity_query_error",
                value=1,
                unit="count",
                tags={"error": "database", "operation": "get_user_activities"},
                component="activity_service"
            )
            self.logger.log_error(e, {
                "service": "ActivityService",
                "method": "get_user_activities",
                "user_id": user_id
            })
            raise e
        finally:
            # Stop timer
            duration = performance_monitor.stop_timer(timer_id)
            if duration:
                performance_monitor.record_histogram(
                    name="get_user_activities_duration",
                    value=duration,
                    tags={"type": "database_query"},
                    component="activity_service"
                )
    
    def get_all_activities(
        self,
        limit: int = 100,
        offset: int = 0
    ) -> List[ActivityLog]:
        """Get all activities (admin only)"""
        
        # Start timer for this operation
        timer_id = performance_monitor.start_timer("get_all_activities")
        
        try:
            activities = self.db.query(ActivityLog)\
                .order_by(ActivityLog.timestamp.desc())\
                .offset(offset)\
                .limit(limit)\
                .all()
            
            # Record query metrics
            performance_monitor.record_counter(
                name="activity_query_count",
                value=1,
                tags={"type": "get_all_activities"},
                component="activity_service"
            )
            
            performance_monitor.record_metric(
                name="activity_query_results",
                value=len(activities),
                unit="count",
                component="activity_service"
            )
            
            # Log this query for monitoring
            self.logger.log_activity(
                user_id=0,  # System user
                action="get_all_activities",
                details={"limit": limit, "offset": offset},
                log_to_db=False,
                log_to_file=True
            )
            return activities
            
        except Exception as e:
            performance_monitor.record_metric(
                name="activity_query_error",
                value=1,
                unit="count",
                tags={"error": "database", "operation": "get_all_activities"},
                component="activity_service"
            )
            self.logger.log_error(e, {
                "service": "ActivityService",
                "method": "get_all_activities"
            })
            raise e
        finally:
            # Stop timer
            duration = performance_monitor.stop_timer(timer_id)
            if duration:
                performance_monitor.record_histogram(
                    name="get_all_activities_duration",
                    value=duration,
                    tags={"type": "database_query"},
                    component="activity_service"
                )
    
    def get_activities_by_action(
        self,
        action: str,
        limit: int = 50,
        offset: int = 0
    ) -> List[ActivityLog]:
        """Get activities by action type"""
        
        # Start timer for this operation
        timer_id = performance_monitor.start_timer("get_activities_by_action")
        
        try:
            activities = self.db.query(ActivityLog)\
                .filter(ActivityLog.action.like(f"%{action}%"))\
                .order_by(ActivityLog.timestamp.desc())\
                .offset(offset)\
                .limit(limit)\
                .all()
            
            # Record query metrics
            performance_monitor.record_counter(
                name="activity_query_count",
                value=1,
                tags={"type": "get_activities_by_action"},
                component="activity_service"
            )
            
            performance_monitor.record_metric(
                name="activity_query_results",
                value=len(activities),
                unit="count",
                tags={"action": action},
                component="activity_service"
            )
            
            # Log this query for monitoring
            self.logger.log_activity(
                user_id=0,  # System user
                action="get_activities_by_action",
                details={"action": action, "limit": limit, "offset": offset},
                log_to_db=False,
                log_to_file=True
            )
            return activities
            
        except Exception as e:
            performance_monitor.record_metric(
                name="activity_query_error",
                value=1,
                unit="count",
                tags={"error": "database", "operation": "get_activities_by_action"},
                component="activity_service"
            )
            self.logger.log_error(e, {
                "service": "ActivityService",
                "method": "get_activities_by_action",
                "action": action
            })
            raise e
        finally:
            # Stop timer
            duration = performance_monitor.stop_timer(timer_id)
            if duration:
                performance_monitor.record_histogram(
                    name="get_activities_by_action_duration",
                    value=duration,
                    tags={"type": "database_query"},
                    component="activity_service"
                )
    
    def get_activities_by_date_range(
        self,
        start_date: datetime,
        end_date: datetime,
        limit: int = 100,
        offset: int = 0
    ) -> List[ActivityLog]:
        """Get activities within a date range"""
        
        # Start timer for this operation
        timer_id = performance_monitor.start_timer("get_activities_by_date_range")
        
        try:
            activities = self.db.query(ActivityLog)\
                .filter(ActivityLog.timestamp >= start_date)\
                .filter(ActivityLog.timestamp <= end_date)\
                .order_by(ActivityLog.timestamp.desc())\
                .offset(offset)\
                .limit(limit)\
                .all()
            
            # Record query metrics
            performance_monitor.record_counter(
                name="activity_query_count",
                value=1,
                tags={"type": "get_activities_by_date_range"},
                component="activity_service"
            )
            
            performance_monitor.record_metric(
                name="activity_query_results",
                value=len(activities),
                unit="count",
                component="activity_service"
            )
            
            # Log this query for monitoring
            self.logger.log_activity(
                user_id=0,  # System user
                action="get_activities_by_date_range",
                details={
                    "start_date": start_date.isoformat(),
                    "end_date": end_date.isoformat(),
                    "limit": limit,
                    "offset": offset
                },
                log_to_db=False,
                log_to_file=True
            )
            return activities
            
        except Exception as e:
            performance_monitor.record_metric(
                name="activity_query_error",
                value=1,
                unit="count",
                tags={"error": "database", "operation": "get_activities_by_date_range"},
                component="activity_service"
            )
            self.logger.log_error(e, {
                "service": "ActivityService",
                "method": "get_activities_by_date_range"
            })
            raise e
        finally:
            # Stop timer
            duration = performance_monitor.stop_timer(timer_id)
            if duration:
                performance_monitor.record_histogram(
                    name="get_activities_by_date_range_duration",
                    value=duration,
                    tags={"type": "database_query"},
                    component="activity_service"
                )
    
    def get_activity_count(self, user_id: Optional[int] = None) -> int:
        """Get total activity count"""
        
        # Start timer for this operation
        timer_id = performance_monitor.start_timer("get_activity_count")
        
        try:
            query = self.db.query(ActivityLog)
            if user_id:
                query = query.filter(ActivityLog.user_id == user_id)
                performance_monitor.record_metric(
                    name="user_id_filter_applied",
                    value=1,
                    unit="count",
                    component="activity_service"
                )
            
            count = query.count()
            
            # Record query metrics
            performance_monitor.record_counter(
                name="activity_query_count",
                value=1,
                tags={"type": "get_activity_count"},
                component="activity_service"
            )
            
            performance_monitor.record_metric(
                name="activity_count_result",
                value=count,
                unit="count",
                tags={"user_id": str(user_id) if user_id else "all"},
                component="activity_service"
            )
            
            # Log this query for monitoring
            self.logger.log_activity(
                user_id=0,  # System user
                action="get_activity_count",
                details={"user_id": user_id},
                log_to_db=False,
                log_to_file=True
            )
            return count
            
        except Exception as e:
            performance_monitor.record_metric(
                name="activity_query_error",
                value=1,
                unit="count",
                tags={"error": "database", "operation": "get_activity_count"},
                component="activity_service"
            )
            self.logger.log_error(e, {
                "service": "ActivityService",
                "method": "get_activity_count",
                "user_id": user_id
            })
            raise e
        finally:
            # Stop timer
            duration = performance_monitor.stop_timer(timer_id)
            if duration:
                performance_monitor.record_histogram(
                    name="get_activity_count_duration",
                    value=duration,
                    tags={"type": "database_query"},
                    component="activity_service"
                )
    
    def get_recent_activities(self, limit: int = 20) -> List[ActivityLog]:
        """Get recent activities across all users"""
        
        # Start timer for this operation
        timer_id = performance_monitor.start_timer("get_recent_activities")
        
        try:
            activities = self.db.query(ActivityLog)\
                .order_by(ActivityLog.timestamp.desc())\
                .limit(limit)\
                .all()
            
            # Record query metrics
            performance_monitor.record_counter(
                name="activity_query_count",
                value=1,
                tags={"type": "get_recent_activities"},
                component="activity_service"
            )
            
            performance_monitor.record_metric(
                name="activity_query_results",
                value=len(activities),
                unit="count",
                component="activity_service"
            )
            
            # Log this query for monitoring
            self.logger.log_activity(
                user_id=0,  # System user
                action="get_recent_activities",
                details={"limit": limit},
                log_to_db=False,
                log_to_file=True
            )
            return activities
            
        except Exception as e:
            performance_monitor.record_metric(
                name="activity_query_error",
                value=1,
                unit="count",
                tags={"error": "database", "operation": "get_recent_activities"},
                component="activity_service"
            )
            self.logger.log_error(e, {
                "service": "ActivityService",
                "method": "get_recent_activities"
            })
            raise e
        finally:
            # Stop timer
            duration = performance_monitor.stop_timer(timer_id)
            if duration:
                performance_monitor.record_histogram(
                    name="get_recent_activities_duration",
                    value=duration,
                    tags={"type": "database_query"},
                    component="activity_service"
                )
    
    def clear_old_activities(self, days_to_keep: int = 90) -> int:
        """Clear activities older than specified days"""
        
        # Start timer for this operation
        timer_id = performance_monitor.start_timer("clear_old_activities")
        
        try:
            from datetime import timedelta
            
            cutoff_date = datetime.utcnow() - timedelta(days=days_to_keep)
            
            deleted_count = self.db.query(ActivityLog)\
                .filter(ActivityLog.timestamp < cutoff_date)\
                .delete()
            
            self.db.commit()
            
            # Record cleanup metrics
            performance_monitor.record_counter(
                name="activity_cleanup_count",
                value=1,
                tags={"type": "clear_old_activities"},
                component="activity_service"
            )
            
            performance_monitor.record_metric(
                name="activities_deleted",
                value=deleted_count,
                unit="count",
                tags={"days_to_keep": days_to_keep},
                component="activity_service"
            )
            
            # Log cleanup operation
            self.logger.log_activity(
                user_id=0,  # System user
                action="clear_old_activities",
                details={"days_to_keep": days_to_keep, "deleted_count": deleted_count},
                log_to_db=False,
                log_to_file=True
            )
            return deleted_count
            
        except Exception as e:
            self.db.rollback()
            performance_monitor.record_metric(
                name="activity_cleanup_error",
                value=1,
                unit="count",
                tags={"error": "database", "operation": "clear_old_activities"},
                component="activity_service"
            )
            self.logger.log_error(e, {
                "service": "ActivityService",
                "method": "clear_old_activities",
                "days_to_keep": days_to_keep
            })
            raise e
        finally:
            # Stop timer
            duration = performance_monitor.stop_timer(timer_id)
            if duration:
                performance_monitor.record_histogram(
                    name="clear_old_activities_duration",
                    value=duration,
                    tags={"type": "database_operation"},
                    component="activity_service"
                )
    
    def get_user_activity_stats(self, user_id: int) -> dict:
        """Get activity statistics for a user"""
        
        # Start timer for this operation
        timer_id = performance_monitor.start_timer("get_user_activity_stats")
        
        try:
            total_activities = self.db.query(ActivityLog)\
                .filter(ActivityLog.user_id == user_id)\
                .count()
            
            # Get activities from last 30 days
            thirty_days_ago = datetime.utcnow() - timedelta(days=30)
            
            recent_activities = self.db.query(ActivityLog)\
                .filter(ActivityLog.user_id == user_id)\
                .filter(ActivityLog.timestamp >= thirty_days_ago)\
                .count()
            
            # Record stats metrics
            performance_monitor.record_counter(
                name="activity_stats_query_count",
                value=1,
                tags={"type": "get_user_activity_stats"},
                component="activity_service"
            )
            
            performance_monitor.record_metric(
                name="user_total_activities",
                value=total_activities,
                unit="count",
                tags={"user_id": str(user_id)},
                component="activity_service"
            )
            
            performance_monitor.record_metric(
                name="user_recent_activities",
                value=recent_activities,
                unit="count",
                tags={"user_id": str(user_id)},
                component="activity_service"
            )
            
            # Log stats retrieval
            self.logger.log_activity(
                user_id=0,  # System user
                action="get_user_activity_stats",
                details={"target_user_id": user_id},
                log_to_db=False,
                log_to_file=True
            )
            return {
                "total_activities": total_activities,
                "recent_activities": recent_activities,
                "activity_rate": recent_activities / 30 if recent_activities > 0 else 0
            }
            
        except Exception as e:
            performance_monitor.record_metric(
                name="activity_stats_error",
                value=1,
                unit="count",
                tags={"error": "database", "operation": "get_user_activity_stats"},
                component="activity_service"
            )
            self.logger.log_error(e, {
                "service": "ActivityService",
                "method": "get_user_activity_stats",
                "user_id": user_id
            })
            raise e
        finally:
            # Stop timer
            duration = performance_monitor.stop_timer(timer_id)
            if duration:
                performance_monitor.record_histogram(
                    name="get_user_activity_stats_duration",
                    value=duration,
                    tags={"type": "database_query"},
                    component="activity_service"
                )
    
    def get_activity_dashboard_stats(self) -> dict:
        """Get activity statistics for dashboard"""
        
        # Start timer for this operation
        timer_id = performance_monitor.start_timer("get_activity_dashboard_stats")
        
        try:
            # Get total activities today
            
            today = datetime.utcnow().date()
            today_start = datetime.combine(today, time.min)
            today_end = datetime.combine(today, time.max)
            
            today_activities = self.db.query(ActivityLog)\
                .filter(ActivityLog.timestamp >= today_start)\
                .filter(ActivityLog.timestamp <= today_end)\
                .count()
            
            # Get total activities this week
            week_start = today_start - timedelta(days=today.weekday())
            week_activities = self.db.query(ActivityLog)\
                .filter(ActivityLog.timestamp >= week_start)\
                .filter(ActivityLog.timestamp <= today_end)\
                .count()
            
            # Get total activities this month
            month_start = today_start.replace(day=1)
            month_activities = self.db.query(ActivityLog)\
                .filter(ActivityLog.timestamp >= month_start)\
                .filter(ActivityLog.timestamp <= today_end)\
                .count()
            
            # Get active users (users with activities in last 7 days)
            week_ago = today_start - timedelta(days=7)
            active_users = self.db.query(ActivityLog.user_id)\
                .filter(ActivityLog.timestamp >= week_ago)\
                .distinct()\
                .count()
            
            # Record dashboard metrics
            performance_monitor.record_counter(
                name="activity_dashboard_query_count",
                value=1,
                tags={"type": "get_activity_dashboard_stats"},
                component="activity_service"
            )
            
            performance_monitor.record_metric(
                name="dashboard_today_activities",
                value=today_activities,
                unit="count",
                component="activity_service"
            )
            
            performance_monitor.record_metric(
                name="dashboard_week_activities",
                value=week_activities,
                unit="count",
                component="activity_service"
            )
            
            performance_monitor.record_metric(
                name="dashboard_month_activities",
                value=month_activities,
                unit="count",
                component="activity_service"
            )
            
            performance_monitor.record_metric(
                name="dashboard_active_users",
                value=active_users,
                unit="count",
                component="activity_service"
            )
            
            # Log dashboard stats retrieval
            self.logger.log_activity(
                user_id=0,  # System user
                action="get_activity_dashboard_stats",
                details={"dashboard": "activity"},
                log_to_db=False,
                log_to_file=True
            )
            return {
                "today_activities": today_activities,
                "week_activities": week_activities,
                "month_activities": month_activities,
                "active_users": active_users
            }
            
        except Exception as e:
            performance_monitor.record_metric(
                name="activity_dashboard_error",
                value=1,
                unit="count",
                tags={"error": "database", "operation": "get_activity_dashboard_stats"},
                component="activity_service"
            )
            self.logger.log_error(e, {
                "service": "ActivityService",
                "method": "get_activity_dashboard_stats"
            })
            raise e
        finally:
            # Stop timer
            duration = performance_monitor.stop_timer(timer_id)
            if duration:
                performance_monitor.record_histogram(
                    name="get_activity_dashboard_stats_duration",
                    value=duration,
                    tags={"type": "database_query"},
                    component="activity_service"
                )