from pathlib import Path
from typing import List
import math
from pydub import AudioSegment
import logging

logger = logging.getLogger(__name__)

class AudioSplitter:
    def __init__(self, max_size_mb: int = 25):
        """Initialize AudioSplitter with maximum segment size."""
        self.max_size_mb = max_size_mb
        self.max_size_bytes = max_size_mb * 1024 * 1024
        logger.info(f"Initialized AudioSplitter with max segment size: {max_size_mb}MB")
        
    def split_audio(self, audio_path: str | Path) -> List[Path]:
        """
        Split an audio file into segments if it exceeds max_size_mb.
        
        Args:
            audio_path: Path to the audio file
            
        Returns:
            List of paths to the split audio segments
        """
        audio_path = Path(audio_path)
        logger.info(f"Processing audio file: {audio_path}")
        
        if not audio_path.exists():
            raise FileNotFoundError(f"Audio file not found: {audio_path}")
        
        file_size = audio_path.stat().st_size
        logger.info(f"File size: {file_size / (1024 * 1024):.2f}MB")
        
        # If file is smaller than max size, return original path
        if file_size <= self.max_size_bytes:
            logger.info("File is smaller than maximum size, no splitting needed")
            return [audio_path]
        
        # Create output directory
        segments_dir = audio_path.parent / f"{audio_path.stem}_segments"
        segments_dir.mkdir(exist_ok=True)
        logger.info(f"Created segments directory: {segments_dir}")
        
        # Load and split the audio
        try:
            audio = AudioSegment.from_file(str(audio_path))
            duration_ms = len(audio)
            segment_size_ms = (self.max_size_bytes / file_size) * duration_ms
            
            # Ensure minimum segment length
            segment_size_ms = max(30000, math.floor(segment_size_ms))  # minimum 30 seconds
            num_segments = math.ceil(duration_ms / segment_size_ms)
            
            logger.info(f"Splitting into {num_segments} segments")
            
            segment_paths = []
            for i in range(num_segments):
                start_ms = i * segment_size_ms
                end_ms = min((i + 1) * segment_size_ms, duration_ms)
                
                segment = audio[start_ms:end_ms]
                segment_path = segments_dir / f"{audio_path.stem}_part{i+1:03d}{audio_path.suffix}"
                
                logger.info(f"Exporting segment {i+1}/{num_segments} to {segment_path}")
                segment.export(str(segment_path), format=audio_path.suffix.lstrip('.'))
                segment_paths.append(segment_path)
            
            return segment_paths
            
        except Exception as e:
            logger.error(f"Error splitting audio file: {e}")
            # Clean up any partial segments
            self.cleanup_segments(segments_dir)
            raise
    
    def cleanup_segments(self, segments_dir: Path) -> None:
        """Clean up segment files and directory."""
        try:
            if segments_dir.exists():
                for file in segments_dir.glob("*"):
                    file.unlink()
                segments_dir.rmdir()
                logger.info(f"Cleaned up segment directory: {segments_dir}")
        except Exception as e:
            logger.warning(f"Error during cleanup: {e}")

    def get_segment_info(self, segments: List[Path]) -> dict:
        """Get information about the segments."""
        sizes = [s.stat().st_size / (1024 * 1024) for s in segments]  # sizes in MB
        return {
            'num_segments': len(segments),
            'total_size_mb': sum(sizes),
            'average_size_mb': sum(sizes) / len(segments) if segments else 0,
            'segments': [
                {
                    'name': s.name,
                    'size_mb': size
                } for s, size in zip(segments, sizes)
            ]
        }