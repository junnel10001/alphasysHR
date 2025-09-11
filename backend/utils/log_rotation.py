import os
import shutil
import gzip
import zipfile
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, Dict, Any, List
from loguru import logger
import threading
import schedule
import time
from concurrent.futures import ThreadPoolExecutor


class LogRotationManager:
    """
    Advanced log rotation and archival system for managing log files.
    """
    
    def __init__(
        self,
        log_dir: str = "logs",
        max_file_size: int = 10 * 1024 * 1024,  # 10MB
        max_files: int = 10,
        retention_days: int = 30,
        compression: str = "gzip",
        auto_cleanup: bool = True,
        cleanup_interval: int = 24 * 60 * 60  # 24 hours
    ):
        """
        Initialize log rotation manager.
        
        Args:
            log_dir: Base directory for log files
            max_file_size: Maximum size before rotation (in bytes)
            max_files: Maximum number of rotated files to keep
            retention_days: Number of days to keep archived logs
            compression: Compression format (gzip, zip, none)
            auto_cleanup: Whether to automatically clean up old logs
            cleanup_interval: Interval for cleanup in seconds
        """
        self.log_dir = Path(log_dir)
        self.max_file_size = max_file_size
        self.max_files = max_files
        self.retention_days = retention_days
        self.compression = compression.lower()
        self.auto_cleanup = auto_cleanup
        self.cleanup_interval = cleanup_interval
        
        # Create log directories
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.archive_dir = self.log_dir / "archive"
        self.archive_dir.mkdir(exist_ok=True)
        
        # Thread for scheduled cleanup
        self.cleanup_thread = None
        self.running = False
        
        # Setup logging
        self._setup_logging()
        
        # Start auto cleanup if enabled
        if self.auto_cleanup:
            self.start_auto_cleanup()
    
    def _setup_logging(self):
        """Setup logging for the rotation manager"""
        logger.remove()
        
        log_format = (
            "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
            "<level>{level: <8}</level> | "
            "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
            "<level>{message}</level>"
        )
        
        # Log to console
        logger.add(
            self.log_dir / "rotation.log",
            format=log_format,
            level="INFO",
            rotation="1 day",
            retention="30 days",
            backtrace=True,
            diagnose=True
        )
    
    def rotate_log_file(self, file_path: Path) -> bool:
        """
        Rotate a log file if it exceeds maximum size.
        
        Args:
            file_path: Path to the log file
            
        Returns:
            True if rotation occurred, False otherwise
        """
        if not file_path.exists():
            return False
        
        try:
            # Check file size
            file_size = file_path.stat().st_size
            
            if file_size <= self.max_file_size:
                return False
            
            logger.info(f"Rotating log file: {file_path.name} (size: {file_size / 1024 / 1024:.2f}MB)")
            
            # Create archive filename with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            archive_name = f"{file_path.stem}_{timestamp}{file_path.suffix}"
            
            if self.compression == "gzip":
                archive_path = self.archive_dir / f"{archive_name}.gz"
                self._compress_file(file_path, archive_path)
            elif self.compression == "zip":
                archive_path = self.archive_dir / f"{archive_name}.zip"
                self._zip_file(file_path, archive_path)
            else:
                # No compression, just move
                archive_path = self.archive_dir / archive_name
                shutil.move(str(file_path), str(archive_path))
            
            # Clean up old archives
            self._cleanup_old_archives(file_path.stem)
            
            logger.info(f"Log file rotated to: {archive_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error rotating log file {file_path}: {str(e)}")
            return False
    
    def _compress_file(self, source_path: Path, dest_path: Path) -> bool:
        """Compress a file using gzip"""
        try:
            with open(source_path, 'rb') as f_in:
                with gzip.open(dest_path, 'wb') as f_out:
                    shutil.copyfileobj(f_in, f_out)
            
            # Remove original file
            source_path.unlink()
            return True
            
        except Exception as e:
            logger.error(f"Error compressing file {source_path}: {str(e)}")
            return False
    
    def _zip_file(self, source_path: Path, dest_path: Path) -> bool:
        """Compress a file using zip"""
        try:
            with zipfile.ZipFile(dest_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                zipf.write(source_path, source_path.name)
            
            # Remove original file
            source_path.unlink()
            return True
            
        except Exception as e:
            logger.error(f"Error zipping file {source_path}: {str(e)}")
            return False
    
    def _cleanup_old_archives(self, file_stem: str) -> int:
        """
        Clean up old archive files for a specific log file.
        
        Args:
            file_stem: The stem name of the log file
            
        Returns:
            Number of files deleted
        """
        deleted_count = 0
        pattern = f"{file_stem}_*"
        
        # Get all archive files for this log file
        archive_files = list(self.archive_dir.glob(f"{pattern}.{self.compression}"))
        
        if self.compression == "gzip":
            archive_files.extend(list(self.archive_dir.glob(f"{pattern}.zip")))
        elif self.compression == "zip":
            archive_files.extend(list(self.archive_dir.glob(f"{pattern}.gz")))
        
        # Sort by modification time (newest first)
        archive_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
        
        # Keep only the most recent files
        for old_file in archive_files[self.max_files:]:
            try:
                old_file.unlink()
                deleted_count += 1
            except Exception as e:
                logger.error(f"Error deleting old archive {old_file}: {str(e)}")
        
        return deleted_count
    
    def archive_old_logs(self, days_old: int = 7) -> int:
        """
        Archive log files older than specified days.
        
        Args:
            days_old: Age threshold for archiving in days
            
        Returns:
            Number of files archived
        """
        archived_count = 0
        cutoff_date = datetime.now() - timedelta(days=days_old)
        
        # Find all log files in the directory
        for log_file in self.log_dir.glob("*.log*"):
            if log_file.is_file():
                try:
                    file_mtime = datetime.fromtimestamp(log_file.stat().st_mtime)
                    
                    if file_mtime < cutoff_date and not log_file.name.startswith("rotation"):
                        if self.rotate_log_file(log_file):
                            archived_count += 1
                            
                except Exception as e:
                    logger.error(f"Error checking file {log_file}: {str(e)}")
        
        logger.info(f"Archived {archived_count} old log files")
        return archived_count
    
    def cleanup_expired_archives(self) -> int:
        """
        Clean up archives older than retention period.
        
        Returns:
            Number of files deleted
        """
        deleted_count = 0
        cutoff_date = datetime.now() - timedelta(days=self.retention_days)
        
        # Find all archive files
        archive_files = list(self.archive_dir.glob("*"))
        
        for archive_file in archive_files:
            if archive_file.is_file():
                try:
                    file_mtime = datetime.fromtimestamp(archive_file.stat().st_mtime)
                    
                    if file_mtime < cutoff_date:
                        archive_file.unlink()
                        deleted_count += 1
                        
                except Exception as e:
                    logger.error(f"Error deleting expired archive {archive_file}: {str(e)}")
        
        logger.info(f"Cleaned up {deleted_count} expired archive files")
        return deleted_count
    
    def get_log_statistics(self) -> Dict[str, Any]:
        """
        Get statistics about log files and archives.
        
        Returns:
            Dictionary with log statistics
        """
        stats = {
            "log_dir": str(self.log_dir),
            "archive_dir": str(self.archive_dir),
            "max_file_size": self.max_file_size,
            "max_files": self.max_files,
            "retention_days": self.retention_days,
            "compression": self.compression,
            "total_logs": 0,
            "total_archives": 0,
            "total_size": 0,
            "log_files": [],
            "archive_files": []
        }
        
        # Count log files
        log_files = list(self.log_dir.glob("*.log*"))
        stats["total_logs"] = len(log_files)
        
        # Count archive files
        archive_files = list(self.archive_dir.glob("*"))
        stats["total_archives"] = len(archive_files)
        
        # Get individual file info
        for log_file in log_files:
            if log_file.is_file():
                file_size = log_file.stat().st_size
                stats["total_size"] += file_size
                stats["log_files"].append({
                    "name": log_file.name,
                    "size": file_size,
                    "size_mb": file_size / 1024 / 1024,
                    "modified": datetime.fromtimestamp(log_file.stat().st_mtime).isoformat()
                })
        
        for archive_file in archive_files[:10]:  # Limit to first 10
            if archive_file.is_file():
                file_size = archive_file.stat().st_size
                stats["total_size"] += file_size
                if len(stats["archive_files"]) < 10:
                    stats["archive_files"].append({
                        "name": archive_file.name,
                        "size": file_size,
                        "size_mb": file_size / 1024 / 1024,
                        "modified": datetime.fromtimestamp(archive_file.stat().st_mtime).isoformat()
                    })
        
        return stats
    
    def start_auto_cleanup(self):
        """Start automatic cleanup in a background thread"""
        if self.cleanup_thread and self.cleanup_thread.is_alive():
            return
        
        self.running = True
        self.cleanup_thread = threading.Thread(target=self._cleanup_worker, daemon=True)
        self.cleanup_thread.start()
        logger.info("Auto cleanup started")
    
    def stop_auto_cleanup(self):
        """Stop automatic cleanup"""
        self.running = False
        if self.cleanup_thread:
            self.cleanup_thread.join(timeout=5)
        logger.info("Auto cleanup stopped")
    
    def _cleanup_worker(self):
        """Background worker for scheduled cleanup"""
        while self.running:
            try:
                # Perform cleanup
                self.archive_old_logs()
                self.cleanup_expired_archives()
                
                # Sleep for the specified interval
                for _ in range(self.cleanup_interval):
                    if not self.running:
                        break
                    time.sleep(1)
                    
            except Exception as e:
                logger.error(f"Error in cleanup worker: {str(e)}")
    
    def compress_all_logs(self) -> int:
        """
        Compress all log files in the log directory.
        
        Returns:
            Number of files compressed
        """
        compressed_count = 0
        log_files = list(self.log_dir.glob("*.log*"))
        
        for log_file in log_files:
            if log_file.is_file() and not log_file.name.startswith("rotation"):
                try:
                    if self.compression == "gzip":
                        dest_path = self.archive_dir / f"{log_file.stem}.gz"
                        if self._compress_file(log_file, dest_path):
                            compressed_count += 1
                    elif self.compression == "zip":
                        dest_path = self.archive_dir / f"{log_file.stem}.zip"
                        if self._zip_file(log_file, dest_path):
                            compressed_count += 1
                    else:
                        # No compression, just move
                        dest_path = self.archive_dir / log_file.name
                        shutil.move(str(log_file), str(dest_path))
                        compressed_count += 1
                        
                except Exception as e:
                    logger.error(f"Error compressing {log_file}: {str(e)}")
        
        logger.info(f"Compressed {compressed_count} log files")
        return compressed_count
    
    def export_logs(self, output_path: Path, days: int = 30) -> bool:
        """
        Export logs to a compressed archive.
        
        Args:
            output_path: Path where to export the logs
            days: Number of days of logs to export
            
        Returns:
            True if export was successful, False otherwise
        """
        try:
            # Create export directory
            export_dir = self.log_dir / "export"
            export_dir.mkdir(exist_ok=True)
            
            # Find logs within the specified date range
            cutoff_date = datetime.now() - timedelta(days=days)
            
            # Copy relevant logs to export directory
            log_files = list(self.log_dir.glob("*.log*"))
            for log_file in log_files:
                if log_file.is_file():
                    file_mtime = datetime.fromtimestamp(log_file.stat().st_mtime)
                    if file_mtime >= cutoff_date:
                        shutil.copy2(log_file, export_dir)
            
            # Copy relevant archives
            archive_files = list(self.archive_dir.glob("*"))
            for archive_file in archive_files:
                if archive_file.is_file():
                    file_mtime = datetime.fromtimestamp(archive_file.stat().st_mtime)
                    if file_mtime >= cutoff_date:
                        shutil.copy2(archive_file, export_dir)
            
            # Create zip archive
            with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for file_to_export in export_dir.rglob("*"):
                    if file_to_export.is_file():
                        arcname = file_to_export.relative_to(export_dir)
                        zipf.write(file_to_export, arcname)
            
            # Clean up export directory
            shutil.rmtree(export_dir)
            
            logger.info(f"Logs exported to: {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error exporting logs: {str(e)}")
            return False
    
    def __del__(self):
        """Cleanup when object is destroyed"""
        self.stop_auto_cleanup()


# Global log rotation manager instance
log_rotation_manager = LogRotationManager()

def setup_log_rotation(
    log_dir: str = "logs",
    max_file_size: int = 10 * 1024 * 1024,
    max_files: int = 10,
    retention_days: int = 30,
    compression: str = "gzip",
    auto_cleanup: bool = True
):
    """
    Setup log rotation manager.
    
    Args:
        log_dir: Base directory for log files
        max_file_size: Maximum size before rotation (in bytes)
        max_files: Maximum number of rotated files to keep
        retention_days: Number of days to keep archived logs
        compression: Compression format (gzip, zip, none)
        auto_cleanup: Whether to automatically clean up old logs
    """
    global log_rotation_manager
    log_rotation_manager = LogRotationManager(
        log_dir=log_dir,
        max_file_size=max_file_size,
        max_files=max_files,
        retention_days=retention_days,
        compression=compression,
        auto_cleanup=auto_cleanup
    )
    
    logger.info("Log rotation system initialized")

if __name__ == "__main__":
    setup_log_rotation()
    
    # Example usage
    print("Log Rotation Manager Example")
    print("Log Statistics:")
    stats = log_rotation_manager.get_log_statistics()
    print(f"Total logs: {stats['total_logs']}")
    print(f"Total archives: {stats['total_archives']}")
    print(f"Total size: {stats['total_size'] / 1024 / 1024:.2f} MB")
    
    # Archive old logs
    archived = log_rotation_manager.archive_old_logs(days_old=1)
    print(f"Archived {archived} old log files")
    
    # Export logs
    export_path = Path("logs_export.zip")
    if log_rotation_manager.export_logs(export_path, days=7):
        print(f"Logs exported to: {export_path}")