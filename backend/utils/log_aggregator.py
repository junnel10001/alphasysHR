import json
import gzip
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass, asdict
from collections import defaultdict, deque
import re
from loguru import logger
import pandas as pd
from concurrent.futures import ThreadPoolExecutor
import threading


@dataclass
class LogEntry:
    """Data class for log entries"""
    timestamp: datetime
    level: str
    message: str
    module: str
    function: str
    line: int
    exception: Optional[str] = None
    extra: Optional[Dict[str, Any]] = None
    file_path: Optional[str] = None
    file_size: Optional[int] = None


@dataclass
class SearchResult:
    """Data class for search results"""
    entries: List[LogEntry]
    total_count: int
    search_time: float
    files_searched: int
    query: str
    filters: Dict[str, Any]


class LogAggregator:
    """
    Log aggregation and search functionality for enhanced logging system.
    """
    
    def __init__(
        self,
        log_dir: str = "logs",
        max_file_size: int = 100 * 1024 * 1024,  # 100MB
        max_cache_size: int = 10000,
        search_workers: int = 4,
        cache_dir: str = "logs/cache"
    ):
        """
        Initialize log aggregator.
        
        Args:
            log_dir: Directory containing log files
            max_file_size: Maximum size of log files before rotation
            max_cache_size: Maximum number of entries to cache
            search_workers: Number of workers for parallel search
            cache_dir: Directory for log search cache
        """
        self.log_dir = Path(log_dir)
        self.max_file_size = max_file_size
        self.max_cache_size = max_cache_size
        self.search_workers = search_workers
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        # Log cache
        self.log_cache: deque = deque(maxlen=max_cache_size)
        self.cache_lock = threading.Lock()
        
        # Index for faster searching
        self.log_index: Dict[str, List[int]] = defaultdict(list)
        self.index_lock = threading.Lock()
        
        # Setup logging
        self._setup_logging()
        
        # Build initial index
        self._build_index()
    
    def _setup_logging(self):
        """Setup logging for the log aggregator"""
        logger.remove()
        
        log_format = (
            "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
            "<level>{level: <8}</level> | "
            "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
            "<level>{message}</level>"
        )
        
        logger.add(
            self.log_dir / "aggregator.log",
            format=log_format,
            level="INFO",
            rotation="1 day",
            retention="30 days",
            backtrace=True,
            diagnose=True
        )
    
    def _build_index(self):
        """Build search index from existing logs"""
        logger.info("Building log search index...")
        
        try:
            with ThreadPoolExecutor(max_workers=self.search_workers) as executor:
                log_files = list(self.log_dir.rglob("*.log"))
                futures = []
                
                for log_file in log_files:
                    futures.append(executor.submit(self._index_file, log_file))
                
                for future in futures:
                    future.result()
                
                logger.info(f"Built index for {len(log_files)} log files")
                
        except Exception as e:
            logger.error(f"Error building log index: {str(e)}")
    
    def _index_file(self, file_path: Path):
        """Index a single log file"""
        try:
            file_size = file_path.stat().st_size
            
            # Skip files that are too large
            if file_size > self.max_file_size:
                logger.warning(f"Skipping large file: {file_path} ({file_size} bytes)")
                return
            
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                for line_num, line in enumerate(f, 1):
                    # Extract basic info for indexing
                    timestamp = self._extract_timestamp(line)
                    level = self._extract_log_level(line)
                    module = self._extract_module(line)
                    
                    # Add to index
                    with self.index_lock:
                        index_key = f"{timestamp.date()}_{module}_{level}"
                        self.log_index[index_key].append((file_path, line_num))
            
        except Exception as e:
            logger.error(f"Error indexing file {file_path}: {str(e)}")
    
    def _extract_timestamp(self, line: str) -> Optional[datetime]:
        """Extract timestamp from log line"""
        try:
            # Look for common timestamp patterns
            patterns = [
                r'<green>(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\.\d{3})</green>',
                r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\.\d{3})',
                r'(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2})',
                r'(\d{2}/\d{2}/\d{4} \d{2}:\d{2}:\d{2})',
            ]
            
            for pattern in patterns:
                match = re.search(pattern, line)
                if match:
                    timestamp_str = match.group(1)
                    try:
                        # Try different datetime formats
                        for fmt in ['%Y-%m-%d %H:%M:%S.%f', '%Y-%m-%d %H:%M:%S', '%Y-%m-%dT%H:%M:%S']:
                            try:
                                return datetime.strptime(timestamp_str, fmt)
                            except ValueError:
                                continue
                    except ValueError:
                        continue
            
            return None
            
        except Exception:
            return None
    
    def _extract_log_level(self, line: str) -> str:
        """Extract log level from log line"""
        try:
            # Look for log level patterns
            patterns = [
                r'<level>(\w{4,5})</level>',
                r'\b(DEBUG|INFO|WARNING|ERROR|CRITICAL)\b',
                r'\[(DEBUG|INFO|WARNING|ERROR|CRITICAL)\]',
            ]
            
            for pattern in patterns:
                match = re.search(pattern, line, re.IGNORECASE)
                if match:
                    return match.group(1).upper()
            
            return "UNKNOWN"
            
        except Exception:
            return "UNKNOWN"
    
    def _extract_module(self, line: str) -> str:
        """Extract module name from log line"""
        try:
            # Look for module patterns
            patterns = [
                r'<cyan>(\w+)</cyan>',
                r'(\w+):',
                r'(\w+)\.',
            ]
            
            for pattern in patterns:
                match = re.search(pattern, line)
                if match:
                    return match.group(1)
            
            return "UNKNOWN"
            
        except Exception:
            return "UNKNOWN"
    
    def _parse_log_line(self, line: str, file_path: Path) -> Optional[LogEntry]:
        """Parse a single log line"""
        try:
            timestamp = self._extract_timestamp(line)
            level = self._extract_log_level(line)
            module = self._extract_module(line)
            
            # Extract function and line number (simplified)
            function = "unknown"
            line_num = 0
            
            # Create log entry
            entry = LogEntry(
                timestamp=timestamp or datetime.now(),
                level=level,
                message=line,
                module=module,
                function=function,
                line=line_num,
                file_path=str(file_path),
                file_size=file_path.stat().st_size if file_path.exists() else None
            )
            
            return entry
            
        except Exception as e:
            logger.error(f"Error parsing log line: {str(e)}")
            return None
    
    def search_logs(
        self,
        query: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        log_level: Optional[str] = None,
        module: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> SearchResult:
        """
        Search logs with various filters.
        
        Args:
            query: Search query string
            start_date: Start date for search
            end_date: End date for search
            log_level: Filter by log level
            module: Filter by module
            limit: Maximum number of results
            offset: Offset for pagination
            
        Returns:
            SearchResult object with search results
        """
        import time
        start_time = time.time()
        
        try:
            results = []
            files_searched = 0
            
            # Get relevant log files
            log_files = self._get_relevant_files(start_date, end_date)
            
            # Search in parallel
            with ThreadPoolExecutor(max_workers=self.search_workers) as executor:
                futures = []
                
                for log_file in log_files:
                    futures.append(executor.submit(
                        self._search_file,
                        log_file,
                        query,
                        log_level,
                        module
                    ))
                
                for future in futures:
                    file_results = future.result()
                    results.extend(file_results)
                    files_searched += 1
            
            # Sort results by timestamp
            results.sort(key=lambda x: x.timestamp, reverse=True)
            
            # Apply pagination
            total_count = len(results)
            results = results[offset:offset + limit]
            
            search_time = time.time() - start_time
            
            return SearchResult(
                entries=results,
                total_count=total_count,
                search_time=search_time,
                files_searched=files_searched,
                query=query,
                filters={
                    "start_date": start_date,
                    "end_date": end_date,
                    "log_level": log_level,
                    "module": module
                }
            )
            
        except Exception as e:
            logger.error(f"Error searching logs: {str(e)}")
            return SearchResult(
                entries=[],
                total_count=0,
                search_time=0,
                files_searched=0,
                query=query,
                filters={}
            )
    
    def _get_relevant_files(self, start_date: Optional[datetime], end_date: Optional[datetime]) -> List[Path]:
        """Get log files relevant to the search criteria"""
        log_files = []
        
        for file_path in self.log_dir.rglob("*.log"):
            # Check file size
            if file_path.stat().st_size > self.max_file_size:
                continue
            
            # Check date range if specified
            if start_date or end_date:
                file_date = datetime.fromtimestamp(file_path.stat().st_mtime)
                if start_date and file_date < start_date:
                    continue
                if end_date and file_date > end_date:
                    continue
            
            log_files.append(file_path)
        
        return log_files
    
    def _search_file(
        self,
        file_path: Path,
        query: str,
        log_level: Optional[str],
        module: Optional[str]
    ) -> List[LogEntry]:
        """Search a single log file"""
        results = []
        
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                for line in f:
                    # Parse log line
                    entry = self._parse_log_line(line, file_path)
                    if not entry:
                        continue
                    
                    # Apply filters
                    if log_level and entry.level != log_level:
                        continue
                    
                    if module and entry.module != module:
                        continue
                    
                    # Apply query search
                    if query.lower() not in line.lower():
                        continue
                    
                    results.append(entry)
                    
                    # Limit results per file for performance
                    if len(results) >= 1000:
                        break
            
        except Exception as e:
            logger.error(f"Error searching file {file_path}: {str(e)}")
        
        return results
    
    def get_log_stats(self, hours: int = 24) -> Dict[str, Any]:
        """
        Get statistics about logs.
        
        Args:
            hours: Number of hours to include in stats
            
        Returns:
            Dictionary with log statistics
        """
        try:
            cutoff_time = datetime.now() - timedelta(hours=hours)
            
            stats = {
                "period_hours": hours,
                "total_files": 0,
                "total_size": 0,
                "log_levels": {},
                "modules": {},
                "hourly_distribution": {}
            }
            
            # Get log files in time range
            log_files = []
            for file_path in self.log_dir.rglob("*.log"):
                file_time = datetime.fromtimestamp(file_path.stat().st_mtime)
                if file_time >= cutoff_time:
                    log_files.append(file_path)
            
            stats["total_files"] = len(log_files)
            
            # Calculate total size
            total_size = sum(f.stat().st_size for f in log_files)
            stats["total_size"] = total_size
            
            # Parse files for statistics
            with ThreadPoolExecutor(max_workers=self.search_workers) as executor:
                futures = []
                
                for log_file in log_files:
                    futures.append(executor.submit(self._get_file_stats, log_file, cutoff_time))
                
                for future in futures:
                    file_stats = future.result()
                    
                    # Aggregate log levels
                    for level, count in file_stats["log_levels"].items():
                        stats["log_levels"][level] = stats["log_levels"].get(level, 0) + count
                    
                    # Aggregate modules
                    for module, count in file_stats["modules"].items():
                        stats["modules"][module] = stats["modules"].get(module, 0) + count
                    
                    # Aggregate hourly distribution
                    for hour, count in file_stats["hourly_distribution"].items():
                        stats["hourly_distribution"][hour] = stats["hourly_distribution"].get(hour, 0) + count
            
            return stats
            
        except Exception as e:
            logger.error(f"Error getting log stats: {str(e)}")
            return {}
    
    def _get_file_stats(self, file_path: Path, cutoff_time: datetime) -> Dict[str, Any]:
        """Get statistics for a single log file"""
        stats = {
            "log_levels": {},
            "modules": {},
            "hourly_distribution": {}
        }
        
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                for line in f:
                    entry = self._parse_log_line(line, file_path)
                    if not entry:
                        continue
                    
                    # Skip entries before cutoff time
                    if entry.timestamp < cutoff_time:
                        continue
                    
                    # Count log levels
                    level = entry.level
                    stats["log_levels"][level] = stats["log_levels"].get(level, 0) + 1
                    
                    # Count modules
                    module = entry.module
                    stats["modules"][module] = stats["modules"].get(module, 0) + 1
                    
                    # Count hourly distribution
                    hour_key = entry.timestamp.strftime("%Y-%m-%d %H:00")
                    stats["hourly_distribution"][hour_key] = stats["hourly_distribution"].get(hour_key, 0) + 1
        
        except Exception as e:
            logger.error(f"Error getting file stats for {file_path}: {str(e)}")
        
        return stats
    
    def export_search_results(
        self,
        results: SearchResult,
        output_path: Path,
        format: str = "json"
    ) -> bool:
        """
        Export search results to a file.
        
        Args:
            results: Search results to export
            output_path: Path where to export the results
            format: Export format ('json' or 'csv')
            
        Returns:
            True if export was successful, False otherwise
        """
        try:
            if format.lower() == "json":
                with open(output_path, 'w') as f:
                    json.dump({
                        "query": results.query,
                        "filters": results.filters,
                        "search_time": results.search_time,
                        "files_searched": results.files_searched,
                        "total_count": results.total_count,
                        "results": [asdict(entry) for entry in results.entries]
                    }, f, indent=2, default=str)
            
            elif format.lower() == "csv":
                df_data = []
                for entry in results.entries:
                    df_data.append({
                        "timestamp": entry.timestamp.isoformat(),
                        "level": entry.level,
                        "module": entry.module,
                        "function": entry.function,
                        "line": entry.line,
                        "message": entry.message,
                        "file_path": entry.file_path
                    })
                
                df = pd.DataFrame(df_data)
                df.to_csv(output_path, index=False)
            
            else:
                logger.error(f"Unsupported export format: {format}")
                return False
            
            logger.info(f"Search results exported to: {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error exporting search results: {str(e)}")
            return False
    
    def clear_cache(self):
        """Clear the log cache"""
        with self.cache_lock:
            self.log_cache.clear()
        
        with self.index_lock:
            self.log_index.clear()
        
        logger.info("Log cache cleared")
    
    def get_cache_info(self) -> Dict[str, Any]:
        """Get information about the cache"""
        with self.cache_lock:
            cache_size = len(self.log_cache)
        
        with self.index_lock:
            index_size = len(self.log_index)
        
        return {
            "cache_size": cache_size,
            "max_cache_size": self.max_cache_size,
            "index_size": index_size,
            "cache_usage": cache_size / self.max_cache_size if self.max_cache_size > 0 else 0
        }
    
    def __del__(self):
        """Cleanup when object is destroyed"""
        self.clear_cache()


# Global log aggregator instance
log_aggregator = LogAggregator()

def setup_log_aggregator(
    log_dir: str = "logs",
    max_file_size: int = 100 * 1024 * 1024,
    max_cache_size: int = 10000,
    search_workers: int = 4,
    cache_dir: str = "logs/cache"
):
    """
    Setup log aggregator.
    
    Args:
        log_dir: Directory containing log files
        max_file_size: Maximum size of log files before rotation
        max_cache_size: Maximum number of entries to cache
        search_workers: Number of workers for parallel search
        cache_dir: Directory for log search cache
    """
    global log_aggregator
    log_aggregator = LogAggregator(
        log_dir=log_dir,
        max_file_size=max_file_size,
        max_cache_size=max_cache_size,
        search_workers=search_workers,
        cache_dir=cache_dir
    )
    
    logger.info("Log aggregation system initialized")

if __name__ == "__main__":
    setup_log_aggregator()
    
    # Example usage
    print("Log Aggregator Example")
    
    # Search logs
    results = log_aggregator.search_logs(
        query="error",
        log_level="ERROR",
        limit=10
    )
    
    print(f"Search results: {results.total_count} entries found in {results.search_time:.4f}s")
    print(f"Searched {results.files_searched} files")
    
    # Get log stats
    stats = log_aggregator.get_log_stats(hours=24)
    print(f"Log stats: {json.dumps(stats, indent=2, default=str)}")
    
    # Export results
    export_path = Path("search_results.json")
    if log_aggregator.export_search_results(results, export_path, format="json"):
        print(f"Results exported to: {export_path}")
    
    # Get cache info
    cache_info = log_aggregator.get_cache_info()
    print(f"Cache info: {cache_info}")