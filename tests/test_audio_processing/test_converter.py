# tests/test_audio_processing/test_converter.py
import pytest
from src.audio_processing.converter import AudioConverter
from pathlib import Path
import os

class TestAudioConverter:
    def setup_method(self):
        self.converter = AudioConverter()
        
    def test_convert_video_to_audio(self, tmp_path):
        # Create a dummy video file for testing
        # Note: We'll need a real video file for actual testing
        test_video = tmp_path / "test_video.mp4"
        with open(test_video, "wb") as f:
            f.write(b"dummy video content")
        
        success, output_files = self.converter.convert_video_to_audio(str(test_video))
        assert not success  # Should fail with dummy content
        assert output_files == []  # Should return empty list on failure
        
    def test_invalid_video_path(self):
        success, output_files = self.converter.convert_video_to_audio("nonexistent.mp4")
        assert not success
        assert output_files == []  # Should return empty list on failure

    def teardown_method(self):
        # Cleanup any temporary files
        if self.converter.output_dir.exists():
            for file in self.converter.output_dir.iterdir():
                file.unlink()
            self.converter.output_dir.rmdir()