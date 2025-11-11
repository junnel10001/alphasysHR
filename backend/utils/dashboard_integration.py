import asyncio
import json
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, asdict
from collections import defaultdict, deque
import threading
import time
from pathlib import Path
from loguru import logger
import psutil
import pandas as pd
from fastapi import WebSocket, WebSocketDisconnect
from contextlib import asynccontextmanager

from backend.utils.logger import ActivityLogger as EnhancedLogger
from backend.utils.json_logger import JSONActivityLogger as JsonLogger
from backend.utils.performance_monitor import performance_monitor
from backend.utils.log_aggregator import log_aggregator


@dataclass
class DashboardMetric:
    """Data class for dashboard metrics"""
    timestamp: datetime
    metric_name: str
    value: float
    unit: str
    category: str
    tags: Dict[str, Any]


@dataclass
class RealtimeActivity:
    """Data class for real-time activity data"""
    timestamp: datetime
    user_id: int
    action: str
    details: Dict[str, Any]
    source: str
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None


class RealtimeDashboard:
    """
    Real-time dashboard integration for activity monitoring.
    """
    
    def __init__(
        self,
        max_metrics: int = 1000,
        max_activities: int = 500,
        metrics_dir: str = "logs/dashboard",
        websocket_timeout: int = 300
    ):
        """
        Initialize real-time dashboard.
        
        Args:
            max_metrics: Maximum number of metrics to keep
            max_activities: Maximum number of activities to keep
            metrics_dir: Directory for storing dashboard metrics
            websocket_timeout: WebSocket timeout in seconds
        """
        self.max_metrics = max_metrics
        self.max_activities = max_activities
        self.metrics_dir = Path(metrics_dir)
        self.metrics_dir.mkdir(parents=True, exist_ok=True)
        
        # Setup logging
        self.logger = EnhancedLogger()
        self.json_logger = JsonLogger()
        
        # Metrics storage
        self.metrics: deque = deque(maxlen=max_metrics)
        self.activities: deque = deque(maxlen=max_activities)
        self.system_metrics: Dict[str, float] = {}
        
        # WebSocket connections
        self.websocket_connections: Dict[str, WebSocket] = {}
        self.connection_lock = threading.Lock()
        
        # Background tasks
        self.background_tasks: List[Callable] = []
        self.task_thread = None
        self.running = False
        
        # Dashboard state
        self.dashboard_state = {
            "last_update": datetime.now(),
            "total_activities": 0,
            "active_users": 0,
            "system_load": 0.0,
            "memory_usage": 0.0,
            "recent_activities": [],
            "metrics_summary": {}
        }
        
        # Setup logging
        self._setup_logging()
        
        # Start background monitoring
        self.start_monitoring()
    
    def _setup_logging(self):
        """Setup logging for the dashboard integration"""
        logger.remove()
        
        log_format = (
            "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
            "<level>{level: <8}</level> | "
            "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
            "<level>{message}</level>"
        )
        
        logger.add(
            self.metrics_dir / "dashboard.log",
            format=log_format,
            level="INFO",
            rotation="1 day",
            retention="30 days",
            backtrace=True,
            diagnose=True
        )
    
    def start_monitoring(self):
        """Start the monitoring thread"""
        if self.task_thread and self.task_thread.is_alive():
            return
        
        self.running = True
        self.task_thread = threading.Thread(target=self._monitoring_worker, daemon=True)
        self.task_thread.start()
        logger.info("Real-time dashboard monitoring started")
    
    def stop_monitoring(self):
        """Stop the monitoring thread"""
        self.running = False
        if self.task_thread:
            self.task_thread.join(timeout=5)
        logger.info("Real-time dashboard monitoring stopped")
    
    def _monitoring_worker(self):
        """Background worker for monitoring system"""
        while self.running:
            try:
                # Update system metrics
                self._update_system_metrics()
                
                # Update dashboard state
                self._update_dashboard_state()
                
                # Broadcast updates to WebSocket clients
                self._broadcast_dashboard_update()
                
                # Clean up old data
                self._cleanup_old_data()
                
                # Sleep for monitoring interval
                time.sleep(5)  # 5 second intervals
                
            except Exception as e:
                logger.error(f"Error in monitoring worker: {str(e)}")
    
    def _update_system_metrics(self):
        """Update system metrics"""
        try:
            # CPU usage
            cpu_percent = psutil.cpu_percent(interval=1)
            self.system_metrics["cpu_percent"] = cpu_percent
            performance_monitor.record_gauge("system_cpu_percent", cpu_percent, "percent")
            
            # Memory usage
            memory = psutil.virtual_memory()
            self.system_metrics["memory_percent"] = memory.percent
            self.system_metrics["memory_used"] = memory.used / 1024 / 1024  # MB
            self.system_metrics["memory_total"] = memory.total / 1024 / 1024  # MB
            performance_monitor.record_gauge("system_memory_percent", memory.percent, "percent")
            
            # Disk usage
            disk = psutil.disk_usage('/')
            self.system_metrics["disk_percent"] = disk.percent
            self.system_metrics["disk_used"] = disk.used / 1024 / 1024  # MB
            self.system_metrics["disk_total"] = disk.total / 1024 / 1024  # MB
            performance_monitor.record_gauge("system_disk_percent", disk.percent, "percent")
            
            # Record dashboard metric
            self.record_metric(
                name="system_update",
                value=1,
                unit="count",
                category="system",
                tags={"interval": "5s"}
            )
            
        except Exception as e:
            logger.error(f"Error updating system metrics: {str(e)}")
    
    def _update_dashboard_state(self):
        """Update dashboard state"""
        try:
            # Update last update time
            self.dashboard_state["last_update"] = datetime.now()
            
            # Update total activities
            self.dashboard_state["total_activities"] = len(self.activities)
            
            # Update active users (users with activities in last 5 minutes)
            cutoff_time = datetime.now() - timedelta(minutes=5)
            recent_users = {activity.user_id for activity in self.activities if activity.timestamp >= cutoff_time}
            self.dashboard_state["active_users"] = len(recent_users)
            
            # Update system load
            self.dashboard_state["system_load"] = self.system_metrics.get("cpu_percent", 0.0)
            self.dashboard_state["memory_usage"] = self.system_metrics.get("memory_percent", 0.0)
            
            # Update recent activities (last 10)
            recent_activities = list(self.activities)[-10:]
            self.dashboard_state["recent_activities"] = [
                {
                    "timestamp": activity.timestamp.isoformat(),
                    "user_id": activity.user_id,
                    "action": activity.action,
                    "source": activity.source,
                    "details": activity.details
                }
                for activity in recent_activities
            ]
            
            # Update metrics summary
            self._update_metrics_summary()
            
        except Exception as e:
            logger.error(f"Error updating dashboard state: {str(e)}")
    
    def _update_metrics_summary(self):
        """Update metrics summary"""
        try:
            # Get recent metrics (last 100)
            recent_metrics = list(self.metrics)[-100:]
            
            summary = {
                "total_metrics": len(recent_metrics),
                "time_period": "last_100_metrics",
                "categories": {},
                "metric_types": {}
            }
            
            # Group by category
            for metric in recent_metrics:
                category = metric.category
                if category not in summary["categories"]:
                    summary["categories"][category] = 0
                summary["categories"][category] += 1
                
                # Group by metric name
                metric_name = metric.metric_name
                if metric_name not in summary["metric_types"]:
                    summary["metric_types"][metric_name] = {
                        "count": 0,
                        "min": float('inf'),
                        "max": 0,
                        "avg": 0
                    }
                
                metric_info = summary["metric_types"][metric_name]
                metric_info["count"] += 1
                metric_info["min"] = min(metric_info["min"], metric.value)
                metric_info["max"] = max(metric_info["max"], metric.value)
            
            # Calculate averages
            for metric_name, info in summary["metric_types"].items():
                if info["count"] > 0:
                    info["avg"] = sum(m.value for m in recent_metrics if m.metric_name == metric_name) / info["count"]
            
            self.dashboard_state["metrics_summary"] = summary
            
        except Exception as e:
            logger.error(f"Error updating metrics summary: {str(e)}")
    
    def _cleanup_old_data(self):
        """Clean up old data"""
        try:
            # Clean up old metrics (older than 24 hours)
            cutoff_time = datetime.now() - timedelta(hours=24)
            while self.metrics and self.metrics[0].timestamp < cutoff_time:
                self.metrics.popleft()
            
            # Clean up old activities (older than 1 hour)
            cutoff_time = datetime.now() - timedelta(hours=1)
            while self.activities and self.activities[0].timestamp < cutoff_time:
                self.activities.popleft()
            
        except Exception as e:
            logger.error(f"Error cleaning up old data: {str(e)}")
    
    def _broadcast_dashboard_update(self):
        """Broadcast dashboard update to WebSocket clients"""
        try:
            if not self.websocket_connections:
                return
            
            dashboard_data = {
                "type": "dashboard_update",
                "timestamp": datetime.now().isoformat(),
                "data": self.dashboard_state
            }
            
            message = json.dumps(dashboard_data)
            
            with self.connection_lock:
                disconnected_clients = []
                for client_id, websocket in self.websocket_connections.items():
                    try:
                        # Send async message
                        asyncio.run(websocket.send_text(message))
                    except Exception as e:
                        logger.error(f"Error sending to WebSocket client {client_id}: {str(e)}")
                        disconnected_clients.append(client_id)
                
                # Remove disconnected clients
                for client_id in disconnected_clients:
                    del self.websocket_connections[client_id]
            
        except Exception as e:
            logger.error(f"Error broadcasting dashboard update: {str(e)}")
    
    def record_metric(
        self,
        name: str,
        value: float,
        unit: str = "",
        category: str = "activity",
        tags: Optional[Dict[str, Any]] = None
    ):
        """
        Record a dashboard metric.
        
        Args:
            name: Name of the metric
            value: Value of the metric
            unit: Unit of measurement
            category: Category of the metric
            tags: Additional tags for the metric
        """
        metric = DashboardMetric(
            timestamp=datetime.now(),
            metric_name=name,
            value=value,
            unit=unit,
            category=category,
            tags=tags or {}
        )
        
        self.metrics.append(metric)
        
        # Log the metric
        self.logger.log_activity(
            user_id=0,  # System metric
            action="dashboard_metric_recorded",
            details={
                "metric_name": name,
                "value": value,
                "unit": unit,
                "category": category
            },
            log_to_db=False,
            log_to_file=True
        )
        
        logger.info(f"Recorded dashboard metric: {name}={value}{unit}")
    
    def record_activity(
        self,
        user_id: int,
        action: str,
        details: Dict[str, Any],
        source: str = "dashboard",
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ):
        """
        Record a real-time activity.
        
        Args:
            user_id: User ID
            action: Action performed
            details: Additional details about the activity
            source: Source of the activity
            ip_address: IP address of the user
            user_agent: User agent string
        """
        activity = RealtimeActivity(
            timestamp=datetime.now(),
            user_id=user_id,
            action=action,
            details=details,
            source=source,
            ip_address=ip_address,
            user_agent=user_agent
        )
        
        self.activities.append(activity)
        
        # Log the activity
        self.logger.log_activity(
            user_id=user_id,
            action=action,
            details={
                **details,
                "source": source,
                "dashboard_realtime": True
            },
            log_to_db=False,
            log_to_file=True
        )
        
        # Record activity metric
        self.record_metric(
            name="activity_recorded",
            value=1,
            unit="count",
            category="activity",
            tags={"user_id": str(user_id), "action": action}
        )
        
        logger.info(f"Recorded real-time activity: {user_id} performed {action}")
    
    def add_websocket_client(self, client_id: str, websocket: WebSocket):
        """
        Add a WebSocket client for real-time updates.
        
        Args:
            client_id: Unique client ID
            websocket: WebSocket connection
        """
        with self.connection_lock:
            self.websocket_connections[client_id] = websocket
        
        self.logger.log_activity(
            user_id=0,  # System activity
            action="websocket_client_added",
            details={"client_id": client_id, "total_clients": len(self.websocket_connections)},
            log_to_db=False,
            log_to_file=True
        )
        
        logger.info(f"Added WebSocket client: {client_id}")
    
    def remove_websocket_client(self, client_id: str):
        """
        Remove a WebSocket client.
        
        Args:
            client_id: Client ID to remove
        """
        with self.connection_lock:
            if client_id in self.websocket_connections:
                del self.websocket_connections[client_id]
        
        self.logger.log_activity(
            user_id=0,  # System activity
            action="websocket_client_removed",
            details={"client_id": client_id, "total_clients": len(self.websocket_connections)},
            log_to_db=False,
            log_to_file=True
        )
        
        logger.info(f"Removed WebSocket client: {client_id}")
    
    def get_dashboard_data(self) -> Dict[str, Any]:
        """
        Get current dashboard data.
        
        Returns:
            Dictionary containing dashboard data
        """
        return {
            **self.dashboard_state,
            "websocket_clients": len(self.websocket_connections),
            "system_metrics": self.system_metrics.copy()
        }
    
    def get_activity_history(
        self,
        hours: int = 24,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Get activity history for the specified time period.
        
        Args:
            hours: Number of hours to include
            limit: Maximum number of activities to return
            
        Returns:
            List of recent activities
        """
        try:
            cutoff_time = datetime.now() - timedelta(hours=hours)
            recent_activities = [
                activity for activity in self.activities
                if activity.timestamp >= cutoff_time
            ]
            
            # Limit results
            recent_activities = recent_activities[-limit:]
            
            return [
                {
                    "timestamp": activity.timestamp.isoformat(),
                    "user_id": activity.user_id,
                    "action": activity.action,
                    "source": activity.source,
                    "details": activity.details,
                    "ip_address": activity.ip_address,
                    "user_agent": activity.user_agent
                }
                for activity in recent_activities
            ]
            
        except Exception as e:
            logger.error(f"Error getting activity history: {str(e)}")
            return []
    
    def export_dashboard_data(
        self,
        output_path: Path,
        hours: int = 24
    ) -> bool:
        """
        Export dashboard data to a file.
        
        Args:
            output_path: Path where to export the data
            hours: Number of hours of data to export
            
        Returns:
            True if export was successful, False otherwise
        """
        try:
            dashboard_data = {
                "export_timestamp": datetime.now().isoformat(),
                "time_period_hours": hours,
                "dashboard_state": self.dashboard_state,
                "system_metrics": self.system_metrics,
                "activity_history": self.get_activity_history(hours=hours),
                "metrics_history": [
                    {
                        "timestamp": metric.timestamp.isoformat(),
                        "metric_name": metric.metric_name,
                        "value": metric.value,
                        "unit": metric.unit,
                        "category": metric.category,
                        "tags": metric.tags
                    }
                    for metric in list(self.metrics)[-1000:]  # Last 1000 metrics
                ]
            }
            
            with open(output_path, 'w') as f:
                json.dump(dashboard_data, f, indent=2, default=str)
            
            self.logger.log_activity(
                user_id=0,  # System activity
                action="dashboard_data_exported",
                details={
                    "output_path": str(output_path),
                    "exported_hours": hours,
                    "activity_count": len(dashboard_data["activity_history"]),
                    "metrics_count": len(dashboard_data["metrics_history"])
                },
                log_to_db=False,
                log_to_file=True
            )
            
            logger.info(f"Dashboard data exported to: {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error exporting dashboard data: {str(e)}")
            return False
    
    def get_dashboard_stats(self, hours: int = 24) -> Dict[str, Any]:
        """
        Get dashboard statistics.
        
        Args:
            hours: Number of hours to include in stats
            
        Returns:
            Dictionary with dashboard statistics
        """
        try:
            # Get activity history
            activity_history = self.get_activity_history(hours=hours)
            
            # Calculate statistics
            total_activities = len(activity_history)
            
            # Get unique users
            unique_users = len({activity["user_id"] for activity in activity_history})
            
            # Get most common actions
            action_counts = defaultdict(int)
            for activity in activity_history:
                action_counts[activity["action"]] += 1
            
            most_common_actions = sorted(
                action_counts.items(),
                key=lambda x: x[1],
                reverse=True
            )[:5]
            
            # Get system performance
            avg_cpu = self.system_metrics.get("cpu_percent", 0.0)
            avg_memory = self.system_metrics.get("memory_percent", 0.0)
            
            # Get metrics summary
            metrics_summary = self.dashboard_state.get("metrics_summary", {})
            
            stats = {
                "period_hours": hours,
                "total_activities": total_activities,
                "unique_users": unique_users,
                "most_common_actions": dict(most_common_actions),
                "system_performance": {
                    "cpu_percent": avg_cpu,
                    "memory_percent": avg_memory,
                    "active_websocket_clients": len(self.websocket_connections)
                },
                "metrics_summary": metrics_summary,
                "last_update": self.dashboard_state["last_update"].isoformat()
            }
            
            return stats
            
        except Exception as e:
            logger.error(f"Error getting dashboard stats: {str(e)}")
            return {}
    
    def __del__(self):
        """Cleanup when object is destroyed"""
        self.stop_monitoring()


# Global dashboard instance
dashboard_integration = RealtimeDashboard()

def setup_dashboard_integration(
    max_metrics: int = 1000,
    max_activities: int = 500,
    metrics_dir: str = "logs/dashboard",
    websocket_timeout: int = 300
):
    """
    Setup dashboard integration.
    
    Args:
        max_metrics: Maximum number of metrics to keep
        max_activities: Maximum number of activities to keep
        metrics_dir: Directory for storing dashboard metrics
        websocket_timeout: WebSocket timeout in seconds
    """
    global dashboard_integration
    dashboard_integration = RealtimeDashboard(
        max_metrics=max_metrics,
        max_activities=max_activities,
        metrics_dir=metrics_dir,
        websocket_timeout=websocket_timeout
    )
    
    logger.info("Dashboard integration system initialized")

if __name__ == "__main__":
    setup_dashboard_integration()
    
    # Example usage
    print("Dashboard Integration Example")
    
    # Record some metrics
    dashboard_integration.record_metric("test_metric", 42.5, "units", "test")
    dashboard_integration.record_metric("test_metric", 45.2, "units", "test")
    dashboard_integration.record_metric("performance", 95.8, "percent", "system")
    
    # Record some activities
    dashboard_integration.record_activity(1, "login", {"method": "password"}, "web")
    dashboard_integration.record_activity(2, "view_page", {"page": "dashboard"}, "web")
    dashboard_integration.record_activity(1, "upload_file", {"file": "document.pdf"}, "web")
    
    # Get dashboard data
    dashboard_data = dashboard_integration.get_dashboard_data()
    print(f"Dashboard data: {json.dumps(dashboard_data, indent=2, default=str)}")
    
    # Get dashboard stats
    stats = dashboard_integration.get_dashboard_stats(hours=1)
    print(f"Dashboard stats: {json.dumps(stats, indent=2, default=str)}")
    
    # Export dashboard data
    export_path = Path("dashboard_export.json")
    if dashboard_integration.export_dashboard_data(export_path, hours=1):
        print(f"Dashboard data exported to: {export_path}")