# src/input_handling/file_handler.py
#test_comment
from pathlib import Path
from typing import List, Tuple

class FileHandler:
    def __init__(self):
        self.supported_formats = {'.mp4', '.avi', '.mkv', '.mov'}
        self.queued_files: List[Path] = []

    def validate_file(self, file_path: str) -> Tuple[bool, str]:
        """Validate a video file."""
        import os
        path = Path(file_path)
        
        # Check file extension first
        if path.suffix.lower() not in self.supported_formats:
            return False, f"Unsupported format: {path.suffix}"
        
        # Handle both absolute and relative paths
        if os.path.isabs(file_path):
            # For absolute paths (Electron mode), do full validation
            if not path.exists():
                return False, "File does not exist"
            
            # Check file size
            if path.stat().st_size == 0:
                return False, "File is empty"
        else:
            # For relative paths (web mode), skip file system validation
            # since we can't access the actual file in web mode
            pass
            
        return True, "File is valid"

    def add_to_queue(self, file_path: str) -> bool:
        """Add a file to the processing queue."""
        is_valid, message = self.validate_file(file_path)
        if is_valid:
            self.queued_files.append(Path(file_path))
            return True
        return False

    def clear_queue(self):
        """Clear the processing queue."""
        self.queued_files.clear()

    def get_queue_status(self) -> dict:
        """Get current queue status."""
        return {
            'total_files': len(self.queued_files),
            'file_list': [str(f) for f in self.queued_files]
        }