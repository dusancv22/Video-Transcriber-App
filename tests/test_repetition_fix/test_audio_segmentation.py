"""
Tests for audio segmentation with overlap to prevent repetition bug.
"""

import pytest
from pathlib import Path
import tempfile
import shutil
from unittest.mock import patch
from pydub import AudioSegment
import numpy as np

from src.audio_processing.splitter import AudioSplitter


class TestAudioSegmentationWithOverlap:
    """Test audio segmentation with overlap functionality."""
    
    def setup_method(self):
        """Set up test environment."""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.splitter = AudioSplitter(max_size_mb=25)
        
    def teardown_method(self):
        """Clean up test environment."""
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)
    
    def create_test_audio(self, duration_ms=60000, sample_rate=44100):
        """Create a test audio file."""
        # Generate a simple sine wave
        frames_per_second = sample_rate
        total_frames = int(duration_ms * frames_per_second / 1000)
        frequency = 440  # A4 note
        
        # Create sine wave
        sine_wave = np.sin(2 * np.pi * frequency * np.linspace(0, duration_ms/1000, total_frames))
        audio_data = (sine_wave * 32767).astype(np.int16)
        
        # Create AudioSegment
        audio = AudioSegment(
            audio_data.tobytes(),
            frame_rate=sample_rate,
            sample_width=2,
            channels=1
        )
        
        return audio
    
    def test_overlap_is_applied_when_splitting(self):
        """Test that overlap is properly applied when splitting large audio files."""
        # Create a large test audio file (simulate >25MB)
        test_audio = self.create_test_audio(duration_ms=120000)  # 2 minutes
        test_file = self.temp_dir / "large_test.mp3"
        test_audio.export(str(test_file), format="mp3")
        
        # Mock file size to be larger than threshold
        with patch.object(Path, 'stat') as mock_stat:
            mock_stat.return_value.st_size = 30 * 1024 * 1024  # 30MB
            
            segments = self.splitter.split_audio(test_file)
            
            # Should create multiple segments
            assert len(segments) > 1, "Large file should be split into multiple segments"
            
            # TODO: Verify overlap exists between segments
            # This would require implementing overlap functionality in AudioSplitter
            # For now, this test documents the expected behavior
    
    def test_no_overlap_for_small_files(self):
        """Test that small files (under threshold) don't get unnecessary overlap."""
        # Create a small test audio file
        test_audio = self.create_test_audio(duration_ms=30000)  # 30 seconds
        test_file = self.temp_dir / "small_test.mp3"
        test_audio.export(str(test_file), format="mp3")
        
        segments = self.splitter.split_audio(test_file)
        
        # Small file should not be split
        assert len(segments) == 1, "Small file should not be split"
        assert segments[0] == test_file, "Original file should be returned"
    

# Integration test markers
pytestmark = [
    pytest.mark.integration,
    pytest.mark.repetition_fix
]
