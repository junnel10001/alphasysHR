import os
import sys
from datetime import datetime
from pathlib import Path
from loguru import logger
from typing import Optional, Dict, Any

# Configure Loguru
def setup_logger(
    log_level: str = "INFO",
    log_file: Optional[str] = None,
    json_logs: bool = False,
    rotation: str = "1 day",
    retention: str = "30 days",
    compression: str = "zip"
):
    """
    Setup Loguru logger with custom configuration.
    
    Args:
        log_level: Minimum log level to display
        log_file: Path to log file (if None, only console logging)
        json_logs: Whether to use JSON format for logs
        rotation: Log rotation policy
        retention: Log retention policy
        compression: Log compression format
    """
    # Remove default handler
    logger.remove()
    
    # Define log format
    if json_logs:
        # JSON format for structured logging
        log_format = (
            "{time:YYYY-MM-DD HH:mm:ss.SSS} | "
            "{level} | "
            "{name} | "
            "{function}:{line} | "
            "{message}"
        )
    else:
        # Colored format for console
        log_format = (
            "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
            "<level>{level: <8}</level> | "
            "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
            "<level>{message}</level>"
        )
    
    # Console handler
    logger.add(
        sys.stderr,
        format=log_format,
        level=log_level,
        colorize=(not json_logs),
        backtrace=True,
        diagnose=True
    )
    
    # File handler (if specified)
    if log_file:
        # Ensure log directory exists
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        logger.add(
            log_file,
            format=log_format,
            level=log_level,
            rotation=rotation,
            retention=retention,
            compression=compression,
            backtrace=True,
            diagnose=True,
            serialize=json_logs
        )

class ActivityLogger:
    """
    Enhanced activity logger using Loguru with structured logging capabilities.
    """
    
    def __init__(self, db_session=None):
        self.db_session = db_session
        self._ensure_log_directories()
    
    def _ensure_log_directories(self):
        """Ensure log directories exist"""
        log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)
        
        # Create subdirectories for different log types
        (log_dir / "activity").mkdir(exist_ok=True)
        (log_dir / "errors").mkdir(exist_ok=True)
        (log_dir / "audit").mkdir(exist_ok=True)
    
    def log_activity(
        self,
        user_id: int,
        action: str,
        details: Optional[Dict[str, Any]] = None,
        log_level: str = "INFO",
        log_to_db: bool = True,
        log_to_file: bool = True
    ):
        """
        Log user activity with enhanced features.
        
        Args:
            user_id: ID of the user performing the action
            action: Description of the action performed
            details: Additional details about the activity
            log_level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
            log_to_db: Whether to log to database
            log_to_file: Whether to log to file
        """
        timestamp = datetime.utcnow()
        
        # Prepare structured log data
        log_data = {
            "user_id": user_id,
            "action": action,
            "timestamp": timestamp.isoformat(),
            "source": "hr_system"
        }
        
        # Add additional details if provided
        if details:
            log_data.update(details)
        
        # Determine Loguru level
        loguru_level = getattr(__import__('loguru').logger, log_level.lower(), "INFO")
        
        # Log to console with structured format
        logger.bind(user_id=user_id, action=action).log(
            loguru_level,
            "Activity: {action}",
            **log_data
        )
        
        # Log to file if enabled
        if log_to_file:
            self._log_to_file(user_id, action, log_data, log_level)
        
        # Log to database if enabled and session provided
        if log_to_db and self.db_session:
            self._log_to_database(user_id, action, log_data, timestamp)
    
    def _log_to_file(self, user_id: int, action: str, log_data: Dict[str, Any], log_level: str):
        """Log activity to file"""
        timestamp = datetime.utcnow()
        date_str = timestamp.strftime("%Y-%m-%d")
        
        # Create filename based on date and user
        filename = f"logs/activity/activity_{user_id}_{date_str}.log"
        
        # Configure file logging for this specific log
        logger.add(
            filename,
            format="{time:YYYY-MM-DD HH:mm:ss.SSS} | {level} | {message}",
            level=log_level,
            rotation="1 day",
            retention="30 days",
            compression="zip",
            serialize=True
        )
        
        # Log the structured data
        logger.bind(user_id=user_id, action=action).info(
            "Structured log: {log_data}",
            log_data=log_data
        )
    
    def _log_to_database(self, user_id: int, action: str, log_data: Dict[str, Any], timestamp: datetime):
        """Log activity to database using existing service"""
        try:
            from backend.services.activity_service import ActivityService
            
            activity_service = ActivityService(self.db_session)
            activity_service.log_activity(user_id, action, timestamp)
        except Exception as e:
            logger.error(f"Failed to log activity to database: {str(e)}")
    
    def log_error(
        self,
        error: Exception,
        context: Optional[Dict[str, Any]] = None,
        user_id: Optional[int] = None
    ):
        """
        Log errors with enhanced context.
        
        Args:
            error: The exception that occurred
            context: Additional context about the error
            user_id: ID of the user (if applicable)
        """
        error_data = {
            "error_type": type(error).__name__,
            "error_message": str(error),
            "error_traceback": str(error.__traceback__) if error.__traceback__ else None,
        }
        
        if context:
            error_data.update(context)
        
        if user_id:
            logger.bind(user_id=user_id).error(
                "System error occurred",
                error_data=error_data
            )
        else:
            logger.error(
                "System error occurred",
                error_data=error_data
            )
        
        # Log to error file
        timestamp = datetime.utcnow()
        date_str = timestamp.strftime("%Y-%m-%d")
        filename = f"logs/errors/error_{date_str}.log"
        
        logger.add(
            filename,
            format="{time:YYYY-MM-DD HH:mm:ss.SSS} | {level} | {message}",
            level="ERROR",
            rotation="1 day",
            retention="90 days",
            compression="zip",
            serialize=True
        )
        
        logger.error(
            "Error logged: {error_data}",
            error_data=error_data
        )
    
    def log_audit_event(
        self,
        event_type: str,
        description: str,
        user_id: Optional[int] = None,
        affected_resources: Optional[Dict[str, Any]] = None
    ):
        """
        Log audit events for security and compliance.
        
        Args:
            event_type: Type of audit event (login, data_access, etc.)
            description: Description of the audit event
            user_id: ID of the user performing the action
            affected_resources: Resources affected by the event
        """
        audit_data = {
            "event_type": event_type,
            "description": description,
            "timestamp": datetime.utcnow().isoformat(),
        }
        
        if user_id:
            audit_data["user_id"] = user_id
        
        if affected_resources:
            audit_data["affected_resources"] = affected_resources
        
        # Log to audit log
        logger.bind(event_type=event_type).info(
            "Audit event: {description}",
            description=description,
            audit_data=audit_data
        )
        
        # Log to audit file
        timestamp = datetime.utcnow()
        date_str = timestamp.strftime("%Y-%m-%d")
        filename = f"logs/audit/audit_{date_str}.log"
        
        logger.add(
            filename,
            format="{time:YYYY-MM-DD HH:mm:ss.SSS} | {level} | {message}",
            level="INFO",
            rotation="1 day",
            retention="365 days",  # Keep audit logs longer
            compression="zip",
            serialize=True
        )
        
        logger.info(
            "Audit event logged: {audit_data}",
            audit_data=audit_data
        )
    
    def get_activity_stats(self, user_id: Optional[int] = None) -> Dict[str, Any]:
        """
        Get activity statistics for analytics.
        
        Args:
            user_id: Specific user ID (if None, get global stats)
            
        Returns:
            Dictionary containing activity statistics
        """
        try:
            from backend.services.activity_service import ActivityService
            
            if self.db_session:
                activity_service = ActivityService(self.db_session)
                
                if user_id:
                    return activity_service.get_user_activity_stats(user_id)
                else:
                    return activity_service.get_activity_dashboard_stats()
            else:
                # Fallback to log file analysis if no database
                return self._analyze_log_files(user_id)
        except Exception as e:
            logger.error(f"Failed to get activity stats: {str(e)}")
            return {"error": str(e)}
    
    def _analyze_log_files(self, user_id: Optional[int] = None) -> Dict[str, Any]:
        """
        Analyze log files for activity statistics when database is not available.
        
        Args:
            user_id: Specific user ID to analyze (if None, analyze all)
            
        Returns:
            Dictionary containing activity statistics from logs
        """
        try:
            log_dir = Path("logs/activity")
            if not log_dir.exists():
                return {"error": "Log directory not found"}
            
            activity_count = 0
            recent_activities = []
            
            # Get today's date
            today = datetime.utcnow().date()
            
            # Parse log files
            for log_file in log_dir.glob("*.log"):
                with open(log_file, 'r') as f:
                    for line in f:
                        if "Structured log:" in line and user_id is None:
                            activity_count += 1
                        elif user_id and f"user_id={user_id}" in line:
                            activity_count += 1
            
            return {
                "total_activities": activity_count,
                "recent_activities": recent_activities,
                "activity_rate": activity_count / 30 if activity_count > 0 else 0  # Assuming 30-day period
            }
        except Exception as e:
            logger.error(f"Failed to analyze log files: {str(e)}")
            return {"error": str(e)}

# Global logger instance
activity_logger = ActivityLogger()

def setup_activity_logging(db_session=None):
    """
    Setup activity logging with Loguru.
    
    Args:
        db_session: Database session for logging to database
    """
    # Setup Loguru with custom configuration
    setup_logger(
        log_level="INFO",
        log_file="logs/activity/activity.log",
        json_logs=False,
        rotation="1 day",
        retention="30 days",
        compression="zip"
    )
    
    # Initialize activity logger
    global activity_logger
    activity_logger = ActivityLogger(db_session)
    
    logger.info("Activity logging system initialized with Loguru")

# Initialize logging when module is imported
if __name__ == "__main__":
    setup_activity_logging()