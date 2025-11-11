import time
import threading
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass, asdict
from collections import defaultdict, deque
from loguru import logger
import psutil
import json
from pathlib import Path


@dataclass
class PerformanceMetric:
    """Data class for performance metrics"""
    timestamp: datetime
    metric_name: str
    value: float
    unit: str
    tags: Dict[str, Any]
    component: str


class PerformanceMonitor:
    """
    Performance monitoring system for tracking activity logging metrics.
    """
    
    def __init__(
        self,
        max_metrics: int = 1000,
        cleanup_interval: int = 3600,  # 1 hour
        metrics_dir: str = "logs/metrics"
    ):
        """
        Initialize performance monitor.
        
        Args:
            max_metrics: Maximum number of metrics to keep in memory
            cleanup_interval: Interval for cleaning up old metrics (in seconds)
            metrics_dir: Directory for storing metrics
        """
        self.max_metrics = max_metrics
        self.cleanup_interval = cleanup_interval
        self.metrics_dir = Path(metrics_dir)
        self.metrics_dir.mkdir(parents=True, exist_ok=True)
        
        # Metrics storage
        self.metrics: deque = deque(maxlen=max_metrics)
        self.histograms: Dict[str, deque] = defaultdict(lambda: deque(maxlen=1000))
        self.counters: Dict[str, int] = defaultdict(int)
        self.gauges: Dict[str, float] = defaultdict(float)
        
        # Timers
        self.active_timers: Dict[str, float] = {}
        self.timer_stats: Dict[str, Dict[str, float]] = defaultdict(lambda: {
            "min": float('inf'),
            "max": 0,
            "total": 0,
            "count": 0
        })
        
        # Monitoring thread
        self.monitoring_thread = None
        self.running = False
        
        # Setup logging
        self._setup_logging()
        
        # Start monitoring thread
        self.start_monitoring()
    
    def _setup_logging(self):
        """Setup logging for the performance monitor"""
        logger.remove()
        
        log_format = (
            "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
            "<level>{level: <8}</level> | "
            "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
            "<level>{message}</level>"
        )
        
        logger.add(
            self.metrics_dir / "performance.log",
            format=log_format,
            level="INFO",
            rotation="1 day",
            retention="30 days",
            backtrace=True,
            diagnose=True
        )
    
    def start_monitoring(self):
        """Start the monitoring thread"""
        if self.monitoring_thread and self.monitoring_thread.is_alive():
            return
        
        self.running = True
        self.monitoring_thread = threading.Thread(target=self._monitoring_worker, daemon=True)
        self.monitoring_thread.start()
        logger.info("Performance monitoring started")
    
    def stop_monitoring(self):
        """Stop the monitoring thread"""
        self.running = False
        if self.monitoring_thread:
            self.monitoring_thread.join(timeout=5)
        logger.info("Performance monitoring stopped")
    
    def _monitoring_worker(self):
        """Background worker for monitoring system resources"""
        while self.running:
            try:
                # Monitor system resources
                self._monitor_system_resources()
                
                # Monitor performance metrics
                self._monitor_performance_metrics()
                
                # Sleep for the interval
                for _ in range(self.cleanup_interval):
                    if not self.running:
                        break
                    time.sleep(1)
                    
            except Exception as e:
                logger.error(f"Error in monitoring worker: {str(e)}")
    
    def _monitor_system_resources(self):
        """Monitor system resources (CPU, memory, disk)"""
        try:
            # CPU usage
            cpu_percent = psutil.cpu_percent(interval=1)
            self.record_gauge("system_cpu_percent", cpu_percent, "percent")
            
            # Memory usage
            memory = psutil.virtual_memory()
            self.record_gauge("system_memory_percent", memory.percent, "percent")
            self.record_gauge("system_memory_used", memory.used / 1024 / 1024, "MB")
            self.record_gauge("system_memory_total", memory.total / 1024 / 1024, "MB")
            
            # Disk usage
            disk = psutil.disk_usage('/')
            self.record_gauge("system_disk_percent", disk.percent, "percent")
            self.record_gauge("system_disk_used", disk.used / 1024 / 1024, "MB")
            self.record_gauge("system_disk_total", disk.total / 1024 / 1024, "MB")
            
            # Network I/O
            net_io = psutil.net_io_counters()
            self.record_counter("system_network_bytes_sent", net_io.bytes_sent)
            self.record_counter("system_network_bytes_recv", net_io.bytes_recv)
            
        except Exception as e:
            logger.error(f"Error monitoring system resources: {str(e)}")
    
    def _monitor_performance_metrics(self):
        """Monitor performance metrics and cleanup old data"""
        try:
            # Clean up old metrics
            cutoff_time = datetime.now() - timedelta(hours=24)
            
            # Remove old metrics
            while self.metrics and self.metrics[0].timestamp < cutoff_time:
                self.metrics.popleft()
            
            # Clean up histogram data
            for hist_name in list(self.histograms.keys()):
                while self.histograms[hist_name] and self.histograms[hist_name][0][0] < cutoff_time:
                    self.histograms[hist_name].popleft()
            
            # Save metrics to file
            self._save_metrics_to_file()
            
        except Exception as e:
            logger.error(f"Error monitoring performance metrics: {str(e)}")
    
    def _save_metrics_to_file(self):
        """Save metrics to file for persistence"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            metrics_file = self.metrics_dir / f"metrics_{timestamp}.jsonl"
            
            with open(metrics_file, 'w') as f:
                for metric in self.metrics:
                    f.write(json.dumps(asdict(metric)) + '\n')
            
        except Exception as e:
            logger.error(f"Error saving metrics to file: {str(e)}")
    
    def record_metric(
        self,
        name: str,
        value: float,
        unit: str = "",
        tags: Optional[Dict[str, Any]] = None,
        component: str = "activity_logging"
    ):
        """
        Record a performance metric.
        
        Args:
            name: Name of the metric
            value: Value of the metric
            unit: Unit of measurement
            tags: Additional tags for the metric
            component: Component that generated the metric
        """
        metric = PerformanceMetric(
            timestamp=datetime.now(),
            metric_name=name,
            value=value,
            unit=unit,
            tags=tags or {},
            component=component
        )
        
        self.metrics.append(metric)
        logger.info(f"Recorded metric: {name}={value}{unit}")
    
    def record_histogram(
        self,
        name: str,
        value: float,
        tags: Optional[Dict[str, Any]] = None,
        component: str = "activity_logging"
    ):
        """
        Record a histogram metric.
        
        Args:
            name: Name of the histogram
            value: Value to add to histogram
            tags: Additional tags for the metric
            component: Component that generated the metric
        """
        timestamp = datetime.now()
        self.histograms[name].append((timestamp, value))
        
        # Update histogram statistics
        values = [v for t, v in self.histograms[name]]
        if values:
            self.timer_stats[name].update({
                "min": min(values),
                "max": max(values),
                "avg": sum(values) / len(values)
            })
    
    def record_counter(self, name: str, value: int = 1):
        """
        Record a counter metric.
        
        Args:
            name: Name of the counter
            value: Value to increment by (default: 1)
        """
        self.counters[name] += value
    
    def record_gauge(self, name: str, value: float, unit: str = ""):
        """
        Record a gauge metric.
        
        Args:
            name: Name of the gauge
            value: Value of the gauge
            unit: Unit of measurement
        """
        self.gauges[name] = value
    
    def start_timer(self, name: str) -> str:
        """
        Start a timer for measuring execution time.
        
        Args:
            name: Name of the timer
            
        Returns:
            Timer ID
        """
        timer_id = f"{name}_{time.time()}"
        self.active_timers[timer_id] = time.time()
        return timer_id
    
    def stop_timer(self, timer_id: str) -> Optional[float]:
        """
        Stop a timer and record the duration.
        
        Args:
            timer_id: ID of the timer to stop
            
        Returns:
            Duration in seconds, or None if timer not found
        """
        if timer_id not in self.active_timers:
            logger.warning(f"Timer {timer_id} not found")
            return None
        
        start_time = self.active_timers.pop(timer_id)
        duration = time.time() - start_time
        
        # Record as histogram
        self.record_histogram(f"timer_{timer_id}", duration, component="activity_logging")
        
        # Update timer statistics
        timer_name = f"timer_{timer_id}"
        if duration < self.timer_stats[timer_name]["min"]:
            self.timer_stats[timer_name]["min"] = duration
        if duration > self.timer_stats[timer_name]["max"]:
            self.timer_stats[timer_name]["max"] = duration
        self.timer_stats[timer_name]["total"] += duration
        self.timer_stats[timer_name]["count"] += 1
        
        logger.info(f"Timer stopped: {timer_id}={duration:.4f}s")
        return duration
    
    def get_timer_stats(self, timer_name: str) -> Dict[str, float]:
        """
        Get statistics for a specific timer.
        
        Args:
            timer_name: Name of the timer (without timestamp)
            
        Returns:
            Dictionary with timer statistics
        """
        full_name = f"timer_{timer_name}"
        if full_name not in self.timer_stats:
            return {}
        
        stats = self.timer_stats[full_name].copy()
        if stats["count"] > 0:
            stats["avg"] = stats["total"] / stats["count"]
        else:
            stats["avg"] = 0
        
        return stats
    
    def get_metrics_summary(self, hours: int = 24) -> Dict[str, Any]:
        """
        Get a summary of metrics for the specified time period.
        
        Args:
            hours: Number of hours to include in summary
            
        Returns:
            Dictionary with metrics summary
        """
        cutoff_time = datetime.now() - timedelta(hours=hours)
        
        # Filter metrics by time
        recent_metrics = [m for m in self.metrics if m.timestamp >= cutoff_time]
        
        summary = {
            "period_hours": hours,
            "total_metrics": len(recent_metrics),
            "system_metrics": {},
            "activity_metrics": {},
            "timer_metrics": {},
            "counter_metrics": {},
            "gauge_metrics": {}
        }
        
        # System metrics
        summary["system_metrics"] = {
            "cpu_percent": self.gauges.get("system_cpu_percent", 0),
            "memory_percent": self.gauges.get("system_memory_percent", 0),
            "disk_percent": self.gauges.get("system_disk_percent", 0)
        }
        
        # Activity metrics
        activity_metrics = [m for m in recent_metrics if m.component == "activity_logging"]
        if activity_metrics:
            # Group by metric name
            metric_groups = defaultdict(list)
            for metric in activity_metrics:
                metric_groups[metric.metric_name].append(metric)
            
            for name, metrics in metric_groups.items():
                values = [m.value for m in metrics]
                summary["activity_metrics"][name] = {
                    "count": len(values),
                    "min": min(values),
                    "max": max(values),
                    "avg": sum(values) / len(values) if values else 0,
                    "unit": metrics[0].unit if metrics else ""
                }
        
        # Timer metrics
        for timer_name, stats in self.timer_stats.items():
            if timer_name.startswith("timer_") and stats["count"] > 0:
                summary["timer_metrics"][timer_name] = {
                    "count": stats["count"],
                    "min": stats["min"],
                    "max": stats["max"],
                    "avg": stats["total"] / stats["count"],
                    "total": stats["total"]
                }
        
        # Counter metrics
        summary["counter_metrics"] = dict(self.counters)
        
        # Gauge metrics
        summary["gauge_metrics"] = dict(self.gauges)
        
        return summary
    
    def export_metrics(self, output_path: Path, hours: int = 24) -> bool:
        """
        Export metrics to a file.
        
        Args:
            output_path: Path where to export the metrics
            hours: Number of hours of metrics to export
            
        Returns:
            True if export was successful, False otherwise
        """
        try:
            summary = self.get_metrics_summary(hours)
            
            with open(output_path, 'w') as f:
                json.dump(summary, f, indent=2, default=str)
            
            logger.info(f"Metrics exported to: {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error exporting metrics: {str(e)}")
            return False
    
    def reset_metrics(self):
        """Reset all metrics"""
        self.metrics.clear()
        self.histograms.clear()
        self.counters.clear()
        self.gauges.clear()
        self.active_timers.clear()
        self.timer_stats.clear()
        
        logger.info("All metrics reset")
    
    def __del__(self):
        """Cleanup when object is destroyed"""
        self.stop_monitoring()


# Global performance monitor instance
performance_monitor = PerformanceMonitor()

def setup_performance_monitor(
    max_metrics: int = 1000,
    cleanup_interval: int = 3600,
    metrics_dir: str = "logs/metrics"
):
    """
    Setup performance monitor.
    
    Args:
        max_metrics: Maximum number of metrics to keep in memory
        cleanup_interval: Interval for cleaning up old metrics (in seconds)
        metrics_dir: Directory for storing metrics
    """
    global performance_monitor
    performance_monitor = PerformanceMonitor(
        max_metrics=max_metrics,
        cleanup_interval=cleanup_interval,
        metrics_dir=metrics_dir
    )
    
    logger.info("Performance monitoring system initialized")

if __name__ == "__main__":
    setup_performance_monitor()
    
    # Example usage
    print("Performance Monitor Example")
    
    # Record some metrics
    performance_monitor.record_metric("test_metric", 42.5, "units", {"category": "test"})
    performance_monitor.record_histogram("test_histogram", 10.5, {"type": "performance"})
    performance_monitor.record_counter("test_counter", 5)
    performance_monitor.record_gauge("test_gauge", 99.9, "percent")
    
    # Start and stop timers
    timer_id = performance_monitor.start_timer("test_timer")
    time.sleep(0.1)  # Simulate work
    duration = performance_monitor.stop_timer(timer_id)
    print(f"Timer duration: {duration:.4f}s")
    
    # Get metrics summary
    summary = performance_monitor.get_metrics_summary(hours=1)
    print(f"Metrics summary: {json.dumps(summary, indent=2, default=str)}")
    
    # Export metrics
    export_path = Path("performance_metrics.json")
    if performance_monitor.export_metrics(export_path, hours=1):
        print(f"Metrics exported to: {export_path}")