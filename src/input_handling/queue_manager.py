from pathlib import Path
from typing import List, Optional, Callable
from dataclasses import dataclass
from enum import Enum
import threading
import logging

logger = logging.getLogger(__name__)

class FileStatus(Enum):
    QUEUED = "queued"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"

@dataclass
class QueueItem:
    file_path: Path
    status: FileStatus
    progress: float = 0.0
    error: Optional[str] = None

class QueueManager:
    def __init__(self):
        self._queue: List[QueueItem] = []
        self._lock = threading.Lock()
        self._current_item: Optional[QueueItem] = None
        self._processing = False
        
    @property
    def is_processing(self) -> bool:
        return self._processing
        
    @property
    def current_item(self) -> Optional[QueueItem]:
        return self._current_item
        
    @property
    def queue_size(self) -> int:
        with self._lock:
            return len(self._queue)
            
    def add_file(self, file_path: str | Path) -> bool:
        """Add a file to the processing queue."""
        file_path = Path(file_path)
        
        with self._lock:
            # Check if file already exists in queue
            if any(item.file_path == file_path for item in self._queue):
                logger.warning(f"File already in queue: {file_path}")
                return False
                
            # Add new file to queue
            self._queue.append(QueueItem(
                file_path=file_path,
                status=FileStatus.QUEUED
            ))
            logger.info(f"Added file to queue: {file_path}")
            return True
            
    def get_next_file(self) -> Optional[QueueItem]:
        """Get the next file to process."""
        with self._lock:
            pending_items = [
                item for item in self._queue 
                if item.status == FileStatus.QUEUED
            ]
            if pending_items:
                self._current_item = pending_items[0]
                self._current_item.status = FileStatus.PROCESSING
                return self._current_item
        return None
        
    def update_progress(self, file_path: Path, progress: float):
        """Update progress for a specific file."""
        with self._lock:
            for item in self._queue:
                if item.file_path == file_path:
                    item.progress = progress
                    break
                    
    def mark_completed(self, file_path: Path):
        """Mark a file as completed."""
        with self._lock:
            for item in self._queue:
                if item.file_path == file_path:
                    item.status = FileStatus.COMPLETED
                    item.progress = 100.0
                    if item == self._current_item:
                        self._current_item = None
                    break
                    
    def mark_failed(self, file_path: Path, error: str):
        """Mark a file as failed with error message."""
        with self._lock:
            for item in self._queue:
                if item.file_path == file_path:
                    item.status = FileStatus.FAILED
                    item.error = error
                    if item == self._current_item:
                        self._current_item = None
                    break
                    
    def clear_queue(self):
        """Clear all items from the queue."""
        with self._lock:
            self._queue.clear()
            self._current_item = None
            self._processing = False
            
    def get_queue_status(self) -> List[dict]:
        """Get status of all files in queue."""
        with self._lock:
            return [
                {
                    'file_name': item.file_path.name,
                    'status': item.status.value,
                    'progress': item.progress,
                    'error': item.error
                }
                for item in self._queue
            ]
            
    def start_processing(self):
        """Mark queue as processing."""
        with self._lock:
            self._processing = True
            
    def stop_processing(self):
        """Mark queue as stopped."""
        with self._lock:
            self._processing = False