"""
Payroll Performance Monitor

This module provides specialized performance monitoring for payroll operations,
including metrics collection, reporting, and alerting for payroll-specific activities.
"""

import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from collections import defaultdict
import statistics
import json
import os
from pathlib import Path

from backend.utils.performance_monitor import PerformanceMonitor


@dataclass
class PayrollOperationMetrics:
    """Metrics for payroll operations"""
    operation_name: str
    execution_time: float
    success: bool
    error_message: Optional[str] = None
    user_id: Optional[int] = None
    payroll_id: Optional[int] = None
    timestamp: datetime = field(default_factory=datetime.now)
    additional_data: Dict[str, Any] = field(default_factory=dict)


class PayrollPerformanceMonitor:
    """Specialized performance monitor for payroll operations"""
    
    def __init__(self, log_dir: str = "logs"):
        """Initialize the payroll performance monitor"""
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        # Operation metrics storage
        self.operation_metrics: Dict[str, List[PayrollOperationMetrics]] = defaultdict(list)
        self.current_timers: Dict[str, str] = {}  # Maps timer_id to operation_name
        
        # Performance thresholds (in seconds)
        self.thresholds = {
            "create_payroll": 2.0,
            "update_payroll": 1.5,
            "generate_payslip": 3.0,
            "bulk_generate_payslips": 5.0,
            "download_payslip": 1.0,
            "list_payroll": 1.0,
            "get_payroll": 0.5,
            "delete_payroll": 1.0,
            "get_filtered_payroll": 2.0,
            "get_payslip_list": 1.0
        }
        
        # Initialize base performance monitor
        self.base_monitor = PerformanceMonitor()
    
    def start_timer(self, operation_name: str, user_id: Optional[int] = None, 
                   payroll_id: Optional[int] = None, **kwargs) -> str:
        """Start timing a payroll operation"""
        timer_id = f"{operation_name}_{int(time.time() * 1000000)}"
        self.current_timers[timer_id] = operation_name
        
        # Log operation start
        self._log_operation_start(operation_name, timer_id, user_id, payroll_id, **kwargs)
        
        return timer_id
    
    def stop_timer(self, timer_id: str, success: bool = True, 
                  error_message: Optional[str] = None, **additional_data):
        """Stop timing a payroll operation and record metrics"""
        operation_name = self.current_timers.pop(timer_id, None)
        if not operation_name:
            return
        
        execution_time = time.time()
        
        # Create metrics record
        metrics = PayrollOperationMetrics(
            operation_name=operation_name,
            execution_time=execution_time,
            success=success,
            error_message=error_message,
            additional_data=additional_data
        )
        
        # Store metrics
        self.operation_metrics[operation_name].append(metrics)
        
        # Log operation completion
        self._log_operation_completion(metrics)
        
        # Check for performance issues
        self._check_performance_threshold(operation_name, execution_time)
        
        # Record to base monitor as well
        self.base_monitor.record_counter(
            name=f"payroll_{operation_name}_count",
            value=1,
            tags={"type": "payroll_operation"},
            component="payroll_performance"
        )
        
        if success:
            self.base_monitor.record_gauge(
                name=f"payroll_{operation_name}_time",
                value=execution_time,
                tags={"type": "payroll_operation"},
                component="payroll_performance"
            )
    
    def _log_operation_start(self, operation_name: str, timer_id: str, 
                           user_id: Optional[int], payroll_id: Optional[int], **kwargs):
        """Log the start of a payroll operation"""
        log_data = {
            "operation": operation_name,
            "timer_id": timer_id,
            "timestamp": datetime.now().isoformat(),
            "user_id": user_id,
            "payroll_id": payroll_id,
            **kwargs
        }
        
        # Write to performance log file
        log_file = self.log_dir / "payroll_performance.log"
        with open(log_file, "a") as f:
            f.write(json.dumps({
                "type": "operation_start",
                "data": log_data,
                "timestamp": datetime.now().isoformat()
            }) + "\n")
    
    def _log_operation_completion(self, metrics: PayrollOperationMetrics):
        """Log the completion of a payroll operation"""
        log_data = {
            "operation": metrics.operation_name,
            "execution_time": metrics.execution_time,
            "success": metrics.success,
            "timestamp": metrics.timestamp.isoformat(),
            "user_id": metrics.user_id,
            "payroll_id": metrics.payroll_id,
            "additional_data": metrics.additional_data
        }
        
        if not metrics.success:
            log_data["error"] = metrics.error_message
        
        # Write to performance log file
        log_file = self.log_dir / "payroll_performance.log"
        with open(log_file, "a") as f:
            f.write(json.dumps({
                "type": "operation_completion",
                "data": log_data,
                "timestamp": datetime.now().isoformat()
            }) + "\n")
    
    def _check_performance_threshold(self, operation_name: str, execution_time: float):
        """Check if operation performance meets thresholds"""
        threshold = self.thresholds.get(operation_name, float('inf'))
        
        if execution_time > threshold:
            # Log performance warning
            warning_data = {
                "operation": operation_name,
                "execution_time": execution_time,
                "threshold": threshold,
                "severity": "warning" if execution_time < threshold * 1.5 else "critical"
            }
            
            # Write to performance warning log
            warning_file = self.log_dir / "payroll_performance_warnings.log"
            with open(warning_file, "a") as f:
                f.write(json.dumps({
                    "type": "performance_warning",
                    "data": warning_data,
                    "timestamp": datetime.now().isoformat()
                }) + "\n")
    
    def get_operation_stats(self, operation_name: str) -> Dict[str, Any]:
        """Get statistics for a specific operation"""
        if operation_name not in self.operation_metrics:
            return {}
        
        metrics = self.operation_metrics[operation_name]
        
        if not metrics:
            return {}
        
        execution_times = [m.execution_time for m in metrics]
        
        return {
            "total_operations": len(metrics),
            "successful_operations": len([m for m in metrics if m.success]),
            "failed_operations": len([m for m in metrics if not m.success]),
            "average_execution_time": statistics.mean(execution_times),
            "min_execution_time": min(execution_times),
            "max_execution_time": max(execution_times),
            "median_execution_time": statistics.median(execution_times),
            "last_execution_time": metrics[-1].execution_time,
            "last_execution_timestamp": metrics[-1].timestamp.isoformat(),
            "success_rate": len([m for m in metrics if m.success]) / len(metrics)
        }
    
    def get_all_stats(self) -> Dict[str, Dict[str, Any]]:
        """Get statistics for all operations"""
        return {
            operation: self.get_operation_stats(operation)
            for operation in self.operation_metrics
        }
    
    def get_slow_operations(self, threshold: float = 1.0) -> List[str]:
        """Get operations that are slower than the threshold"""
        slow_ops = []
        
        for operation_name in self.operation_metrics:
            stats = self.get_operation_stats(operation_name)
            if stats and stats.get("average_execution_time", 0) > threshold:
                slow_ops.append(operation_name)
        
        return slow_ops
    
    def get_error_summary(self) -> Dict[str, Any]:
        """Get a summary of errors across all operations"""
        error_summary = {
            "total_errors": 0,
            "error_by_operation": {},
            "recent_errors": []
        }
        
        for operation_name, metrics in self.operation_metrics.items():
            operation_errors = [m for m in metrics if not m.success]
            
            if operation_errors:
                error_summary["error_by_operation"][operation_name] = len(operation_errors)
                error_summary["total_errors"] += len(operation_errors)
                
                # Get recent errors (last 24 hours)
                recent_cutoff = datetime.now() - timedelta(hours=24)
                recent_errors = [
                    {
                        "timestamp": m.timestamp.isoformat(),
                        "error_message": m.error_message
                    }
                    for m in operation_errors
                    if m.timestamp > recent_cutoff
                ]
                
                error_summary["recent_errors"].extend(recent_errors)
        
        return error_summary
    
    def generate_performance_report(self) -> Dict[str, Any]:
        """Generate a comprehensive performance report"""
        return {
            "generated_at": datetime.now().isoformat(),
            "operation_stats": self.get_all_stats(),
            "slow_operations": self.get_slow_operations(),
            "error_summary": self.get_error_summary(),
            "performance_thresholds": self.thresholds
        }
    
    def cleanup_old_logs(self, days_to_keep: int = 30):
        """Clean up old performance logs"""
        cutoff_date = datetime.now() - timedelta(days=days_to_keep)
        
        # Clean up operation metrics
        for operation_name in list(self.operation_metrics.keys()):
            # Keep only recent metrics
            recent_metrics = [
                m for m in self.operation_metrics[operation_name]
                if m.timestamp > cutoff_date
            ]
            
            if recent_metrics:
                self.operation_metrics[operation_name] = recent_metrics
            else:
                del self.operation_metrics[operation_name]
        
        # Clean up log files
        for log_file in [self.log_dir / "payroll_performance.log", 
                        self.log_dir / "payroll_performance_warnings.log"]:
            if log_file.exists():
                # Read file and filter out old entries
                with open(log_file, "r") as f:
                    lines = f.readlines()
                
                filtered_lines = []
                for line in lines:
                    try:
                        log_entry = json.loads(line.strip())
                        entry_time = datetime.fromisoformat(log_entry["timestamp"])
                        if entry_time > cutoff_date:
                            filtered_lines.append(line)
                    except (json.JSONDecodeError, KeyError, ValueError):
                        # Skip malformed entries
                        continue
                
                # Write filtered lines back
                with open(log_file, "w") as f:
                    f.writelines(filtered_lines)
    
    def export_metrics(self, output_file: Optional[str] = None) -> str:
        """Export metrics to a file"""
        if output_file is None:
            output_file = self.log_dir / f"payroll_metrics_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        report = self.generate_performance_report()
        
        with open(output_file, "w") as f:
            json.dump(report, f, indent=2)
        
        return str(output_file)