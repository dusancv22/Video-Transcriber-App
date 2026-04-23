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

    def test_split_metadata_tracks_original_timeline_window(self, monkeypatch):
        audio_path = self.converter.output_dir / "large_audio.mp3"
        audio_path.write_bytes(b"fake audio")

        monkeypatch.setattr(self.converter, "check_file_size", lambda _: 50.0)
        monkeypatch.setattr(self.converter, "_get_audio_duration", lambda _: 90.0)

        def fake_extract(_input_path, output_path, _start_time, _end_time):
            Path(output_path).touch()
            return True

        monkeypatch.setattr(self.converter, "_extract_audio_segment", fake_extract)

        split_files = self.converter.split_audio_if_needed(
            str(audio_path),
            max_size_mb=25,
            overlap_seconds=2.5
        )
        metadata = self.converter.get_last_split_metadata()

        assert len(split_files) == 3
        assert len(metadata) == 3
        assert metadata[0]["start_time"] == 0
        assert metadata[0]["content_start_time"] == 0
        assert metadata[0]["content_end_time"] == 30
        assert metadata[1]["start_time"] == 27.5
        assert metadata[1]["content_start_time"] == 30
        assert metadata[1]["content_end_time"] == 60
        assert metadata[2]["content_start_time"] == 60
        assert metadata[2]["content_end_time"] == 90

    def teardown_method(self):
        # Cleanup any temporary files
        if self.converter.output_dir.exists():
            for file in self.converter.output_dir.iterdir():
                file.unlink()
            self.converter.output_dir.rmdir()
