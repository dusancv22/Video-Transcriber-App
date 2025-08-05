# tests/test_input_handling/test_file_handler.py
import pytest
from src.input_handling.file_handler import FileHandler
import os

class TestFileHandler:
    def setup_method(self):
        self.file_handler = FileHandler()
        
    def test_validate_file_invalid_extension(self):
        """Test validation of file with invalid extension"""
        is_valid, message = self.file_handler.validate_file("test.txt")
        assert not is_valid
        assert "Unsupported format" in message
        
    def test_validate_file_nonexistent(self):
        """Test validation of non-existent file"""
        is_valid, message = self.file_handler.validate_file("nonexistent.mp4")
        assert not is_valid
        assert "does not exist" in message
        
    def test_queue_management(self):
        """Test queue management functions"""
        # Create a temporary test file
        test_file = "test_video.mp4"
        with open(test_file, "w") as f:
            f.write("dummy content")
            
        try:
            # Test adding to queue
            assert self.file_handler.add_to_queue(test_file)
            assert len(self.file_handler.queued_files) == 1
            
            # Test queue status
            status = self.file_handler.get_queue_status()
            assert status['total_files'] == 1
            assert test_file in status['file_list'][0]
            
            # Test clearing queue
            self.file_handler.clear_queue()
            assert len(self.file_handler.queued_files) == 0
            
        finally:
            # Cleanup
            if os.path.exists(test_file):
                os.remove(test_file)