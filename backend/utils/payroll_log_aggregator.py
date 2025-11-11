"""
Payroll Log Aggregator

This module provides specialized log aggregation and search functionality 
specifically for payroll operations and data.
"""

import os
import json
import re
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, field
import sqlite3
import threading
from collections import defaultdict, Counter
import statistics

from backend.utils.log_aggregator import LogAggregator


@dataclass
class PayrollLogEntry:
    """Represents a payroll log entry"""
    timestamp: datetime
    level: str
    message: str
    module: str
    user_id: Optional[int] = None
    payroll_id: Optional[int] = None
    operation: Optional[str] = None
    details: Dict[str, Any] = field(default_factory=dict)
    file_path: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation"""
        return {
            "timestamp": self.timestamp.isoformat(),
            "level": self.level,
            "message": self.message,
            "module": self.module,
            "user_id": self.user_id,
            "payroll_id": self.payroll_id,
            "operation": self.operation,
            "details": self.details,
            "file_path": self.file_path
        }


class PayrollLogAggregator:
    """Specialized log aggregator for payroll operations"""
    
    def __init__(self, log_dir: str = "logs/payroll"):
        """Initialize the payroll log aggregator"""
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        # Thread lock for database operations
        self.db_lock = threading.Lock()
        
        # Database for aggregated logs
        self.db_path = self.log_dir / "payroll_logs.db"
        self._init_database()
        
        # Initialize base aggregator
        self.base_aggregator = LogAggregator()
    
    def _init_database(self):
        """Initialize the SQLite database for log aggregation"""
        with self.db_lock:
            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.cursor()
            
            # Create logs table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS payroll_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    level TEXT NOT NULL,
                    message TEXT NOT NULL,
                    module TEXT NOT NULL,
                    user_id INTEGER,
                    payroll_id INTEGER,
                    operation TEXT,
                    details TEXT,
                    file_path TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Create indexes for faster queries
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_timestamp ON payroll_logs(timestamp)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_user_id ON payroll_logs(user_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_payroll_id ON payroll_logs(payroll_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_operation ON payroll_logs(operation)')
            
            conn.commit()
            conn.close()
    
    def aggregate_payroll_logs(self, source_files: List[str], days_back: int = 7) -> None:
        """Aggregate payroll logs from source files"""
        cutoff_date = datetime.now() - timedelta(days=days_back)
        
        for source_file in source_files:
            if not os.path.exists(source_file):
                continue
            
            try:
                with open(source_file, 'r') as f:
                    for line in f:
                        try:
                            log_entry = self._parse_payroll_log_line(line.strip())
                            if log_entry and log_entry.timestamp >= cutoff_date:
                                self._store_log_entry(log_entry)
                        except (json.JSONDecodeError, ValueError):
                            continue
            except Exception:
                continue
        
        # Clean up old entries
        self._cleanup_old_logs(days_back)
    
    def _parse_payroll_log_line(self, line: str) -> Optional[PayrollLogEntry]:
        """Parse a single log line into a PayrollLogEntry"""
        try:
            # Try to parse as JSON first
            data = json.loads(line)
            
            # Handle different log formats
            if "type" in data:
                # Structured log format
                if data["type"] == "operation_start":
                    return self._parse_operation_start_log(data)
                elif data["type"] == "operation_completion":
                    return self._parse_operation_completion_log(data)
                elif data["type"] == "performance_warning":
                    return self._parse_performance_warning_log(data)
                elif data["type"] == "audit_event":
                    return self._parse_audit_event_log(data)
            
            # Standard log format
            return PayrollLogEntry(
                timestamp=datetime.fromisoformat(data["timestamp"]),
                level=data.get("level", "INFO"),
                message=data.get("message", ""),
                module=data.get("module", "payroll"),
                user_id=data.get("user_id"),
                payroll_id=data.get("payroll_id"),
                operation=data.get("operation"),
                details=data.get("details", {}),
                file_path=data.get("file_path")
            )
            
        except json.JSONDecodeError:
            # Try to parse as plain text log
            return self._parse_text_log_line(line)
    
    def _parse_operation_start_log(self, data: Dict[str, Any]) -> PayrollLogEntry:
        """Parse operation start log"""
        return PayrollLogEntry(
            timestamp=datetime.fromisoformat(data["data"]["timestamp"]),
            level="INFO",
            message=f"Payroll operation started: {data['data']['operation']}",
            module="payroll",
            user_id=data["data"].get("user_id"),
            payroll_id=data["data"].get("payroll_id"),
            operation=data["data"]["operation"],
            details={"type": "operation_start", **data["data"]},
            file_path=data["data"].get("file_path")
        )
    
    def _parse_operation_completion_log(self, data: Dict[str, Any]) -> PayrollLogEntry:
        """Parse operation completion log"""
        return PayrollLogEntry(
            timestamp=datetime.fromisoformat(data["data"]["timestamp"]),
            level="INFO" if data["data"].get("success", True) else "ERROR",
            message=f"Payroll operation completed: {data['data']['operation']}",
            module="payroll",
            user_id=data["data"].get("user_id"),
            payroll_id=data["data"].get("payroll_id"),
            operation=data["data"]["operation"],
            details={"type": "operation_completion", **data["data"]},
            file_path=data["data"].get("file_path")
        )
    
    def _parse_performance_warning_log(self, data: Dict[str, Any]) -> PayrollLogEntry:
        """Parse performance warning log"""
        return PayrollLogEntry(
            timestamp=datetime.fromisoformat(data["data"]["timestamp"]),
            level="WARNING",
            message=f"Performance warning for {data['data']['operation']}: {data['data']['execution_time']:.2f}s",
            module="payroll",
            operation=data["data"]["operation"],
            details={"type": "performance_warning", **data["data"]},
            file_path=data["data"].get("file_path")
        )
    
    def _parse_audit_event_log(self, data: Dict[str, Any]) -> PayrollLogEntry:
        """Parse audit event log"""
        return PayrollLogEntry(
            timestamp=datetime.fromisoformat(data["timestamp"]),
            level="AUDIT",
            message=f"Audit event: {data['event_type']}",
            module="payroll",
            user_id=data.get("user_id"),
            payroll_id=data.get("payroll_id"),
            operation=data.get("event_type"),
            details={"type": "audit_event", **data.get("details", {})},
            file_path=data.get("file_path")
        )
    
    def _parse_text_log_line(self, line: str) -> Optional[PayrollLogEntry]:
        """Parse a plain text log line"""
        # Simple regex for common log patterns
        patterns = [
            r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})\s+(\w+)\s+(.+)',
            r'(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2})\s+(\w+)\s+(.+)',
        ]
        
        for pattern in patterns:
            match = re.match(pattern, line)
            if match:
                timestamp_str, level, message = match.groups()
                try:
                    # Try different timestamp formats
                    for fmt in ['%Y-%m-%d %H:%M:%S', '%Y-%m-%dT%H:%M:%S']:
                        try:
                            timestamp = datetime.strptime(timestamp_str, fmt)
                            return PayrollLogEntry(
                                timestamp=timestamp,
                                level=level,
                                message=message,
                                module="payroll"
                            )
                        except ValueError:
                            continue
                except ValueError:
                    continue
        
        return None
    
    def _store_log_entry(self, entry: PayrollLogEntry):
        """Store a log entry in the database"""
        with self.db_lock:
            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO payroll_logs 
                (timestamp, level, message, module, user_id, payroll_id, operation, details, file_path)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                entry.timestamp.isoformat(),
                entry.level,
                entry.message,
                entry.module,
                entry.user_id,
                entry.payroll_id,
                entry.operation,
                json.dumps(entry.details),
                entry.file_path
            ))
            
            conn.commit()
            conn.close()
    
    def search_logs(self, 
                   start_date: Optional[datetime] = None,
                   end_date: Optional[datetime] = None,
                   user_id: Optional[int] = None,
                   payroll_id: Optional[int] = None,
                   operation: Optional[str] = None,
                   level: Optional[str] = None,
                   limit: int = 100) -> List[PayrollLogEntry]:
        """Search for payroll logs with various filters"""
        with self.db_lock:
            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.cursor()
            
            # Build query
            query = "SELECT * FROM payroll_logs WHERE 1=1"
            params = []
            
            if start_date:
                query += " AND timestamp >= ?"
                params.append(start_date.isoformat())
            
            if end_date:
                query += " AND timestamp <= ?"
                params.append(end_date.isoformat())
            
            if user_id:
                query += " AND user_id = ?"
                params.append(user_id)
            
            if payroll_id:
                query += " AND payroll_id = ?"
                params.append(payroll_id)
            
            if operation:
                query += " AND operation = ?"
                params.append(operation)
            
            if level:
                query += " AND level = ?"
                params.append(level)
            
            query += " ORDER BY timestamp DESC LIMIT ?"
            params.append(limit)
            
            cursor.execute(query, params)
            rows = cursor.fetchall()
            
            conn.close()
            
            # Convert rows to PayrollLogEntry objects
            entries = []
            for row in rows:
                entry = PayrollLogEntry(
                    timestamp=datetime.fromisoformat(row[1]),
                    level=row[2],
                    message=row[3],
                    module=row[4],
                    user_id=row[5],
                    payroll_id=row[6],
                    operation=row[7],
                    details=json.loads(row[8]) if row[8] else {},
                    file_path=row[9]
                )
                entries.append(entry)
            
            return entries
    
    def get_log_statistics(self, days_back: int = 7) -> Dict[str, Any]:
        """Get statistics about payroll logs"""
        cutoff_date = datetime.now() - timedelta(days=days_back)
        
        with self.db_lock:
            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.cursor()
            
            # Total logs
            cursor.execute("SELECT COUNT(*) FROM payroll_logs WHERE timestamp >= ?", 
                          (cutoff_date.isoformat(),))
            total_logs = cursor.fetchone()[0]
            
            # Logs by level
            cursor.execute("SELECT level, COUNT(*) FROM payroll_logs WHERE timestamp >= ? GROUP BY level", 
                          (cutoff_date.isoformat(),))
            level_counts = dict(cursor.fetchall())
            
            # Logs by operation
            cursor.execute("SELECT operation, COUNT(*) FROM payroll_logs WHERE timestamp >= ? AND operation IS NOT NULL GROUP BY operation", 
                          (cutoff_date.isoformat(),))
            operation_counts = dict(cursor.fetchall())
            
            # Logs by user
            cursor.execute("SELECT user_id, COUNT(*) FROM payroll_logs WHERE timestamp >= ? AND user_id IS NOT NULL GROUP BY user_id", 
                          (cutoff_date.isoformat(),))
            user_counts = dict(cursor.fetchall())
            
            # Error rate
            error_count = level_counts.get("ERROR", 0) + level_counts.get("WARNING", 0)
            error_rate = (error_count / total_logs * 100) if total_logs > 0 else 0
            
            conn.close()
            
            return {
                "total_logs": total_logs,
                "level_distribution": level_counts,
                "operation_distribution": operation_counts,
                "user_distribution": user_counts,
                "error_rate": error_rate,
                "period_days": days_back,
                "generated_at": datetime.now().isoformat()
            }
    
    def get_user_activity_summary(self, user_id: int, days_back: int = 30) -> Dict[str, Any]:
        """Get activity summary for a specific user"""
        cutoff_date = datetime.now() - timedelta(days=days_back)
        
        with self.db_lock:
            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.cursor()
            
            # User's operations
            cursor.execute('''
                SELECT operation, COUNT(*), AVG(timestamp) 
                FROM payroll_logs 
                WHERE user_id = ? AND timestamp >= ? AND operation IS NOT NULL
                GROUP BY operation
            ''', (user_id, cutoff_date.isoformat()))
            
            operations = cursor.fetchall()
            
            # User's payroll IDs
            cursor.execute('''
                SELECT payroll_id, COUNT(*) 
                FROM payroll_logs 
                WHERE user_id = ? AND timestamp >= ? AND payroll_id IS NOT NULL
                GROUP BY payroll_id
            ''', (user_id, cutoff_date.isoformat()))
            
            payroll_ids = cursor.fetchall()
            
            # First and last activity
            cursor.execute('''
                SELECT MIN(timestamp), MAX(timestamp) 
                FROM payroll_logs 
                WHERE user_id = ? AND timestamp >= ?
            ''', (user_id, cutoff_date.isoformat()))
            
            first_last = cursor.fetchone()
            
            conn.close()
            
            return {
                "user_id": user_id,
                "total_operations": sum(count for _, count, _ in operations),
                "operations_by_type": dict(operations),
                "payroll_ids_affected": [pid for pid, _ in payroll_ids],
                "first_activity": first_last[0].isoformat() if first_last[0] else None,
                "last_activity": first_last[1].isoformat() if first_last[1] else None,
                "period_days": days_back
            }
    
    def get_payroll_operation_summary(self, payroll_id: int) -> Dict[str, Any]:
        """Get summary of operations for a specific payroll"""
        with self.db_lock:
            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.cursor()
            
            # Operations for this payroll
            cursor.execute('''
                SELECT operation, level, COUNT(*) 
                FROM payroll_logs 
                WHERE payroll_id = ? 
                GROUP BY operation, level
            ''', (payroll_id,))
            
            operations = cursor.fetchall()
            
            # Timeline of operations
            cursor.execute('''
                SELECT timestamp, operation, level, message
                FROM payroll_logs 
                WHERE payroll_id = ? 
                ORDER BY timestamp
            ''', (payroll_id,))
            
            timeline = cursor.fetchall()
            
            conn.close()
            
            return {
                "payroll_id": payroll_id,
                "operation_counts": dict(operations),
                "timeline": [
                    {
                        "timestamp": row[0].isoformat(),
                        "operation": row[1],
                        "level": row[2],
                        "message": row[3]
                    }
                    for row in timeline
                ]
            }
    
    def export_logs(self, output_file: str, 
                   start_date: Optional[datetime] = None,
                   end_date: Optional[datetime] = None,
                   user_id: Optional[int] = None,
                   payroll_id: Optional[int] = None,
                   operation: Optional[str] = None) -> str:
        """Export logs to a file"""
        logs = self.search_logs(start_date, end_date, user_id, payroll_id, operation, limit=10000)
        
        export_data = {
            "exported_at": datetime.now().isoformat(),
            "filters": {
                "start_date": start_date.isoformat() if start_date else None,
                "end_date": end_date.isoformat() if end_date else None,
                "user_id": user_id,
                "payroll_id": payroll_id,
                "operation": operation
            },
            "logs": [log.to_dict() for log in logs]
        }
        
        with open(output_file, 'w') as f:
            json.dump(export_data, f, indent=2)
        
        return output_file
    
    def _cleanup_old_logs(self, days_to_keep: int = 30):
        """Clean up old log entries"""
        cutoff_date = datetime.now() - timedelta(days=days_to_keep)
        
        with self.db_lock:
            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.cursor()
            
            cursor.execute("DELETE FROM payroll_logs WHERE timestamp < ?", (cutoff_date.isoformat(),))
            conn.commit()
            conn.close()