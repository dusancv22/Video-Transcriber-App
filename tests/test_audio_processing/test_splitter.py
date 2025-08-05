import unittest
from pathlib import Path
import shutil
import sys

# Add project root to Python path
project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from src.audio_processing.splitter import AudioSplitter

class TestAudioSplitter(unittest.TestCase):
    def setUp(self):
        """Set up test environment."""
        self.splitter = AudioSplitter(max_size_mb=25)  # Standard Whisper size limit
        self.test_dir = Path("tests/test_audio_processing/test_files")
        self.test_dir.mkdir(parents=True, exist_ok=True)
        
        # Path to your test audio file
        self.test_audio_path = self.test_dir / "Test video_audio.mp3"  # Replace with your file name
            
    def test_audio_splitting(self):
        """Test splitting of audio file."""
        # Skip if test file doesn't exist
        if not self.test_audio_path.exists():
            self.skipTest(f"Test file not found at {self.test_audio_path}")
        
        print(f"\nTest file size: {self.test_audio_path.stat().st_size / (1024*1024):.2f} MB")
        
        # Split the audio
        segments = self.splitter.split_audio(self.test_audio_path)
        
        # Verify segments
        if self.test_audio_path.stat().st_size > self.splitter.max_size_bytes:
            self.assertGreater(len(segments), 1, "File should be split into multiple segments")
            
            # Check each segment
            for segment in segments:
                self.assertTrue(segment.exists(), f"Segment {segment} should exist")
                self.assertLessEqual(
                    segment.stat().st_size, 
                    self.splitter.max_size_bytes,
                    f"Segment {segment.name} is larger than max size"
                )
                
            # Get and print segment info
            info = self.splitter.get_segment_info(segments)
            print("\nSegment Info:", info)
        else:
            self.assertEqual(len(segments), 1, "Small file should not be split")
            self.assertEqual(segments[0], self.test_audio_path)

if __name__ == '__main__':
    unittest.main(verbosity=2)