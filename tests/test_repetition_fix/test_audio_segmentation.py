"""
Tests for audio segmentation with overlap to prevent repetition bug.

Exercises the real splitting implementation (AudioConverter.split_audio_if_needed)
with real generated audio files.
"""

import pytest
from pathlib import Path
import tempfile
import shutil
from pydub import AudioSegment
import numpy as np

from src.audio_processing.converter import AudioConverter


class TestAudioSegmentationWithOverlap:
    """Test audio segmentation with overlap functionality."""

    def setup_method(self):
        """Set up test environment."""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.converter = AudioConverter(enable_quality_pass=False)

    def teardown_method(self):
        """Clean up test environment."""
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)

    def create_test_audio(self, path: Path, duration_ms=60000, sample_rate=16000):
        """Create a real test audio file (sine wave)."""
        total_frames = int(duration_ms * sample_rate / 1000)
        frequency = 440  # A4 note

        sine_wave = np.sin(2 * np.pi * frequency * np.linspace(0, duration_ms / 1000, total_frames))
        audio_data = (sine_wave * 32767).astype(np.int16)

        audio = AudioSegment(
            audio_data.tobytes(),
            frame_rate=sample_rate,
            sample_width=2,
            channels=1
        )
        audio.export(str(path), format=path.suffix.lstrip('.'))
        return path

    def test_overlap_is_applied_when_splitting(self):
        """Splitting a long file produces overlapping segments with metadata."""
        test_file = self.create_test_audio(
            self.temp_dir / "large_test.wav", duration_ms=90000  # 90 seconds
        )

        segments = self.converter.split_audio_if_needed(
            str(test_file), max_duration_seconds=30.0, overlap_seconds=2.5
        )
        metadata = self.converter.get_last_split_metadata()

        # Should create multiple segments
        assert len(segments) == 3, "90s file with 30s max should split into 3 segments"
        assert len(metadata) == 3
        for segment_path in segments:
            assert Path(segment_path).exists()

        # Middle segment should have overlap on both sides
        assert metadata[1]['has_start_overlap']
        assert metadata[1]['has_end_overlap']
        assert metadata[1]['start_time'] == pytest.approx(30.0 - 2.5, abs=0.1)
        # Content window excludes the overlap margins
        assert metadata[1]['content_start_time'] == pytest.approx(30.0, abs=0.1)
        assert metadata[1]['content_end_time'] == pytest.approx(60.0, abs=0.1)

    def test_no_overlap_for_small_files(self):
        """Files under the duration threshold are not split."""
        test_file = self.create_test_audio(
            self.temp_dir / "small_test.wav", duration_ms=30000  # 30 seconds
        )

        segments = self.converter.split_audio_if_needed(
            str(test_file), max_duration_seconds=1500.0
        )

        assert len(segments) == 1, "Small file should not be split"
        assert segments[0] == str(test_file), "Original file should be returned"
        assert self.converter.get_last_split_metadata() == []


# Integration test markers
pytestmark = [
    pytest.mark.integration,
    pytest.mark.repetition_fix
]
