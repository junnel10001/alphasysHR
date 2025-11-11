import json
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, Union
from loguru import logger
import uuid


class JSONActivityLogger:
    """
    Enhanced JSON logger for structured activity logging with better parsing capabilities.
    """
    
    def __init__(self, log_dir: str = "logs/json"):
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self._setup_logger()
    
    def _setup_logger(self):
        """Setup Loguru for JSON logging"""
        # Remove default handler
        logger.remove()
        
        # JSON format string
        json_format = (
            "{time:YYYY-MM-DD HH:mm:ss.SSS} | "
            "{level} | "
            "{name}:{function}:{line} | "
            "{message}"
        )
        
        # Console handler with JSON format
        logger.add(
            self._get_log_file("console"),
            format=json_format,
            level="INFO",
            serialize=True,
            backtrace=True,
            diagnose=True
        )
    
    def _get_log_file(self, log_type: str, date: Optional[datetime] = None) -> str:
        """Get log file path based on type and date"""
        if date is None:
            date = datetime.utcnow()
        
        date_str = date.strftime("%Y-%m-%d")
        return str(self.log_dir / f"{log_type}_{date_str}.jsonl")
    
    def _generate_log_id(self) -> str:
        """Generate a unique log ID"""
        return str(uuid.uuid4())
    
    def log_activity(
        self,
        user_id: int,
        action: str,
        details: Optional[Dict[str, Any]] = None,
        log_level: str = "INFO",
        log_type: str = "activity",
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Log structured activity data in JSON format.
        
        Args:
            user_id: ID of the user performing the action
            action: Description of the action performed
            details: Additional details about the activity
            log_level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
            log_type: Type of log (activity, audit, error, etc.)
            metadata: Additional metadata to include
            
        Returns:
            Dictionary containing the logged data
        """
        timestamp = datetime.utcnow()
        
        # Create structured log entry
        log_entry = {
            "log_id": self._generate_log_id(),
            "timestamp": timestamp.isoformat(),
            "log_type": log_type,
            "user_id": user_id,
            "action": action,
            "source": "hr_system",
            "version": "1.0"
        }
        
        # Add details if provided
        if details:
            log_entry["details"] = details
        
        # Add metadata if provided
        if metadata:
            log_entry["metadata"] = metadata
        
        # Add session context if available
        if hasattr(self, '_session_context'):
            log_entry["session"] = self._session_context
        
        # Convert to JSON string and log
        json_log = json.dumps(log_entry, default=str)
        
        # Determine Loguru level
        loguru_level = getattr(__import__('loguru').logger, log_level.lower(), "INFO")
        
        # Log the entry
        logger.log(loguru_level, json_log)
        
        # Also write to specific log file
        log_file = self._get_log_file(log_type, timestamp)
        with open(log_file, 'a', encoding='utf-8') as f:
            f.write(json_log + '\n')
        
        return log_entry
    
    def log_audit_event(
        self,
        event_type: str,
        description: str,
        user_id: Optional[int] = None,
        affected_resources: Optional[Dict[str, Any]] = None,
        severity: str = "INFO",
        **kwargs
    ) -> Dict[str, Any]:
        """
        Log audit events in structured JSON format.
        
        Args:
            event_type: Type of audit event
            description: Description of the event
            user_id: ID of the user performing the action
            affected_resources: Resources affected by the event
            severity: Severity level of the event
            **kwargs: Additional event-specific data
            
        Returns:
            Dictionary containing the logged audit data
        """
        audit_data = {
            "event_type": event_type,
            "description": description,
            "severity": severity,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        if user_id:
            audit_data["user_id"] = user_id
        
        if affected_resources:
            audit_data["affected_resources"] = affected_resources
        
        # Add any additional kwargs
        audit_data.update(kwargs)
        
        return self.log_activity(
            user_id=user_id or 0,
            action=f"audit_{event_type}",
            details=audit_data,
            log_level=severity,
            log_type="audit"
        )
    
    def log_security_event(
        self,
        event_type: str,
        description: str,
        user_id: Optional[int] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        severity: str = "WARNING",
        **kwargs
    ) -> Dict[str, Any]:
        """
        Log security-related events in structured JSON format.
        
        Args:
            event_type: Type of security event
            description: Description of the security event
            user_id: ID of the user (if applicable)
            ip_address: IP address of the request
            user_agent: User agent string
            severity: Severity level of the security event
            **kwargs: Additional event-specific data
            
        Returns:
            Dictionary containing the logged security data
        """
        security_data = {
            "event_type": event_type,
            "description": description,
            "severity": severity,
            "timestamp": datetime.utcnow().isoformat(),
            "category": "security"
        }
        
        if user_id:
            security_data["user_id"] = user_id
        
        if ip_address:
            security_data["ip_address"] = ip_address
        
        if user_agent:
            security_data["user_agent"] = user_agent
        
        # Add any additional kwargs
        security_data.update(kwargs)
        
        return self.log_activity(
            user_id=user_id or 0,
            action=f"security_{event_type}",
            details=security_data,
            log_level=severity,
            log_type="security"
        )
    
    def log_error(
        self,
        error: Exception,
        context: Optional[Dict[str, Any]] = None,
        user_id: Optional[int] = None,
        component: Optional[str] = None,
        severity: str = "ERROR"
    ) -> Dict[str, Any]:
        """
        Log errors in structured JSON format with enhanced context.
        
        Args:
            error: The exception that occurred
            context: Additional context about the error
            user_id: ID of the user (if applicable)
            component: Component where the error occurred
            severity: Severity level of the error
            
        Returns:
            Dictionary containing the logged error data
        """
        error_data = {
            "error_type": type(error).__name__,
            "error_message": str(error),
            "error_timestamp": datetime.utcnow().isoformat(),
            "severity": severity
        }
        
        # Add traceback if available
        if error.__traceback__:
            import traceback
            error_data["traceback"] = traceback.format_exception(type(error), error, error.__traceback__)
        
        # Add context if provided
        if context:
            error_data["context"] = context
        
        # Add component if provided
        if component:
            error_data["component"] = component
        
        # Add user ID if provided
        if user_id:
            error_data["user_id"] = user_id
        
        return self.log_activity(
            user_id=user_id or 0,
            action="error",
            details=error_data,
            log_level=severity,
            log_type="error"
        )
    
    def log_performance_metric(
        self,
        metric_name: str,
        value: Union[int, float],
        unit: Optional[str] = None,
        component: Optional[str] = None,
        user_id: Optional[int] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Log performance metrics in structured JSON format.
        
        Args:
            metric_name: Name of the performance metric
            value: Value of the metric
            unit: Unit of measurement
            component: Component where the metric was recorded
            user_id: ID of the user (if applicable)
            **kwargs: Additional metric-specific data
            
        Returns:
            Dictionary containing the logged metric data
        """
        metric_data = {
            "metric_name": metric_name,
            "value": value,
            "timestamp": datetime.utcnow().isoformat(),
            "category": "performance"
        }
        
        if unit:
            metric_data["unit"] = unit
        
        if component:
            metric_data["component"] = component
        
        # Add any additional kwargs
        metric_data.update(kwargs)
        
        return self.log_activity(
            user_id=user_id or 0,
            action=f"metric_{metric_name}",
            details=metric_data,
            log_level="INFO",
            log_type="performance"
        )
    
    def search_logs(
        self,
        log_type: str = "activity",
        filters: Optional[Dict[str, Any]] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 100
    ) -> list:
        """
        Search through log files based on filters.
        
        Args:
            log_type: Type of logs to search (activity, audit, error, etc.)
            filters: Dictionary of filters to apply
            start_date: Start date for log search
            end_date: End date for log search
            limit: Maximum number of results to return
            
        Returns:
            List of matching log entries
        """
        results = []
        
        # Determine which log files to search
        if start_date and end_date:
            # Search date range
            current_date = start_date
            while current_date <= end_date:
                log_file = self._get_log_file(log_type, current_date)
                if log_file.exists():
                    results.extend(self._search_file(log_file, filters))
                current_date += datetime.timedelta(days=1)
        else:
            # Search today's log
            log_file = self._get_log_file(log_type)
            if log_file.exists():
                results.extend(self._search_file(log_file, filters))
        
        return results[:limit]
    
    def _search_file(self, log_file: Path, filters: Optional[Dict[str, Any]] = None) -> list:
        """
        Search a specific log file for matching entries.
        
        Args:
            log_file: Path to the log file
            filters: Dictionary of filters to apply
            
        Returns:
            List of matching log entries
        """
        results = []
        
        try:
            with open(log_file, 'r', encoding='utf-8') as f:
                for line in f:
                    try:
                        log_entry = json.loads(line.strip())
                        
                        # Apply filters
                        if filters:
                            match = True
                            for key, value in filters.items():
                                if key in log_entry and log_entry[key] != value:
                                    match = False
                                    break
                            
                            if match:
                                results.append(log_entry)
                        else:
                            results.append(log_entry)
                    
                    except json.JSONDecodeError:
                        # Skip malformed JSON lines
                        continue
        
        except Exception as e:
            logger.error(f"Error searching log file {log_file}: {str(e)}")
        
        return results
    
    def get_log_statistics(self, log_type: str = "activity", days: int = 30) -> Dict[str, Any]:
        """
        Get statistics about log entries.
        
        Args:
            log_type: Type of logs to analyze
            days: Number of days to analyze
            
        Returns:
            Dictionary containing log statistics
        """
        from datetime import timedelta
        
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        logs = self.search_logs(log_type, start_date=start_date, end_date=end_date)
        
        stats = {
            "total_logs": len(logs),
            "days_analyzed": days,
            "log_type": log_type,
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat()
        }
        
        if logs:
            # Count by action type
            action_counts = {}
            for log in logs:
                action = log.get("action", "unknown")
                action_counts[action] = action_counts.get(action, 0) + 1
            
            stats["action_counts"] = action_counts
            
            # Count by user
            user_counts = {}
            for log in logs:
                user_id = log.get("user_id", 0)
                user_counts[str(user_id)] = user_counts.get(str(user_id), 0) + 1
            
            stats["user_counts"] = user_counts
            
            # Most recent log
            stats["most_recent"] = max(logs, key=lambda x: x.get("timestamp", ""))
        
        return stats
    
    def cleanup_old_logs(self, log_type: str = "activity", days_to_keep: int = 30) -> int:
        """
        Clean up old log files.
        
        Args:
            log_type: Type of logs to clean up
            days_to_keep: Number of days of logs to keep
            
        Returns:
            Number of files deleted
        """
        from datetime import timedelta
        
        cutoff_date = datetime.utcnow() - timedelta(days=days_to_keep)
        deleted_count = 0
        
        # Clean up old log files
        for log_file in self.log_dir.glob(f"{log_type}_*.jsonl"):
            try:
                # Extract date from filename
                date_str = log_file.stem.split('_', 1)[1]
                file_date = datetime.strptime(date_str, "%Y-%m-%d")
                
                if file_date < cutoff_date:
                    log_file.unlink()
                    deleted_count += 1
            
            except (ValueError, IndexError):
                # Skip malformed filenames
                continue
        
        return deleted_count


# Global JSON logger instance
json_logger = JSONActivityLogger()

def setup_json_logging(log_dir: str = "logs/json"):
    """
    Setup JSON logging with Loguru.
    
    Args:
        log_dir: Directory for log files
    """
    global json_logger
    json_logger = JSONActivityLogger(log_dir)
    
    logger.info("JSON logging system initialized")

if __name__ == "__main__":
    setup_json_logging()
    
    # Example usage
    json_logger.log_activity(
        user_id=1,
        action="user_login",
        details={"method": "password", "ip": "192.168.1.1"}
    )
    
    json_logger.log_audit_event(
        event_type="data_access",
        description="User accessed sensitive data",
        user_id=1,
        affected_resources={"table": "employees", "record_id": 123}
    )