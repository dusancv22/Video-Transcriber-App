from pathlib import Path
import moviepy.editor as mp
from typing import Tuple, Optional, Callable
import logging
import time
from datetime import datetime

logger = logging.getLogger(__name__)

class AudioConverter:
    def __init__(self):
        """Initialize AudioConverter with output directory setup."""
        self.output_dir = Path("temp/audio")
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self._last_split_metadata = []  # Store metadata from last split operation
        logger.info(f"AudioConverter initialized with output directory: {self.output_dir}")

    def get_last_split_metadata(self) -> list:
        """
        Get metadata from the last split operation.
        
        Returns:
            list: List of dictionaries containing segment metadata including overlap information
        """
        return self._last_split_metadata.copy()

    def check_file_size(self, file_path: str) -> float:
        """
        Check file size in MB.
        
        Args:
            file_path: Path to the file to check
            
        Returns:
            float: File size in MB
        """
        size = Path(file_path).stat().st_size / (1024 * 1024)
        logger.info(f"File size check: {file_path} - {size:.2f} MB")
        return size

    def split_audio_if_needed(self, audio_path: str, max_size_mb: float = 25, overlap_seconds: float = 2.5):
        """
        Split audio file if larger than max_size_mb with overlap between segments to prevent
        transcription repetition issues.
        
        Args:
            audio_path: Path to the audio file
            max_size_mb: Maximum size in MB before splitting is required
            overlap_seconds: Seconds of overlap between adjacent segments (default: 2.5)
            
        Returns:
            list[str]: List of paths to audio segments
        """
        print(f"\nChecking file size for: {audio_path}")
        size = self.check_file_size(audio_path)
        print(f"File size: {size:.2f} MB")
        
        if size > max_size_mb:
            print(f"File needs splitting (exceeds {max_size_mb} MB)")
            
        try:
            if size <= max_size_mb:
                print("File size within limits - no splitting needed")
                # Reset metadata since no splitting occurred
                self._last_split_metadata = []
                return [audio_path]
                
            # Load audio and prepare for splitting
            print("Loading audio file for splitting...")
            audio = mp.AudioFileClip(audio_path)
            duration = audio.duration
            
            # Calculate segments
            segments = int(size / max_size_mb) + 1
            segment_duration = duration / segments
            print(f"Splitting into {segments} segments of {segment_duration:.2f} seconds each")
            print(f"Using {overlap_seconds:.1f}s overlap between segments to prevent repetition")
            
            split_files = []
            segment_metadata = []  # Track overlap information for potential deduplication
            
            for i in range(segments):
                # Calculate segment boundaries with overlap
                if i == 0:
                    # First segment: 0 to duration+overlap
                    start_time = 0
                    end_time = min(segment_duration + overlap_seconds, duration)
                    has_start_overlap = False
                    has_end_overlap = end_time < duration
                elif i == segments - 1:
                    # Last segment: start-overlap to duration
                    start_time = max(0, i * segment_duration - overlap_seconds)
                    end_time = duration
                    has_start_overlap = start_time > 0
                    has_end_overlap = False
                else:
                    # Middle segments: start-overlap to end+overlap
                    start_time = max(0, i * segment_duration - overlap_seconds)
                    end_time = min((i + 1) * segment_duration + overlap_seconds, duration)
                    has_start_overlap = start_time > 0
                    has_end_overlap = end_time < duration
                
                segment_path = Path(audio_path).parent / f"{Path(audio_path).stem}_part{i+1}.mp3"
                print(f"\nCreating segment {i+1}/{segments}: {segment_path.name}")
                print(f"Time range: {start_time:.2f}s to {end_time:.2f}s")
                if has_start_overlap or has_end_overlap:
                    overlap_info = []
                    if has_start_overlap:
                        overlap_info.append(f"start overlap: {overlap_seconds:.1f}s")
                    if has_end_overlap:
                        overlap_info.append(f"end overlap: {overlap_seconds:.1f}s")
                    print(f"Overlap: {', '.join(overlap_info)}")
                
                # Store metadata for potential text deduplication
                segment_metadata.append({
                    'segment_index': i,
                    'start_time': start_time,
                    'end_time': end_time,
                    'has_start_overlap': has_start_overlap,
                    'has_end_overlap': has_end_overlap,
                    'overlap_seconds': overlap_seconds if (has_start_overlap or has_end_overlap) else 0
                })
                
                # Extract and save segment
                segment = audio.subclip(start_time, end_time)
                segment.write_audiofile(
                    str(segment_path),
                    fps=44100,
                    nbytes=4,
                    codec='libmp3lame',
                    logger=None
                )
                split_files.append(str(segment_path))
                print(f"Segment {i+1} created successfully")
                
            # Cleanup
            audio.close()
            # Remove original large file
            Path(audio_path).unlink()
            print("\nOriginal file removed after splitting")
            
            # Log split information with overlap details
            total_overlap_time = sum(meta['overlap_seconds'] for meta in segment_metadata)
            logger.info(
                f"Split completed: {len(split_files)} segments created "
                f"from {Path(audio_path).name} with {overlap_seconds:.1f}s overlap "
                f"(total overlap time: {total_overlap_time:.1f}s)"
            )
            
            # Store metadata as a class attribute for potential use in text processing
            # This allows downstream components to access overlap information
            self._last_split_metadata = segment_metadata
            
            return split_files
            
        except Exception as e:
            error_msg = f"Error splitting audio: {str(e)}"
            logger.error(error_msg)
            print(f"Error: {error_msg}")
            return [audio_path]

    def convert_video_to_audio(self, video_path: str, progress_callback: Optional[Callable[[float], None]] = None) -> Tuple[bool, list[str]]:
        """
        Convert video file to audio (MP3) and split if needed with enhanced progress reporting.
        
        Args:
            video_path: Path to the video file
            progress_callback: Optional callback for progress updates
            
        Returns:
            Tuple[bool, list[str]]: Success status and list of audio file paths
        """
        try:
            start_time = time.time()
            video_path = Path(video_path)
            output_path = self.output_dir / f"{video_path.stem}.mp3"
            
            print(f"\nConverting video to audio: {video_path.name}")
            print(f"Output path: {output_path}")
            logger.info(f"Starting conversion: {video_path} -> {output_path}")
            
            # Update progress
            if progress_callback:
                progress_callback(0)
            
            # Load video and extract audio
            print("Loading video file...")
            video = mp.VideoFileClip(str(video_path))
            
            if video.audio is None:
                error_msg = "Video has no audio track"
                logger.error(error_msg)
                print(f"Error: {error_msg}")
                return False, []
                
            audio = video.audio
            
            # Convert to audio
            print("Converting to audio format...")
            audio.write_audiofile(
                str(output_path),
                fps=44100,
                nbytes=4,
                codec='libmp3lame',
                logger=None
            )
            
            # Update progress
            if progress_callback:
                progress_callback(50)
            
            # Cleanup video objects
            audio.close()
            video.close()
            
            print("\nInitial conversion completed, checking if splitting is needed")
            # Split if needed and return list of file paths
            audio_files = self.split_audio_if_needed(str(output_path))
            
            # Calculate conversion time
            conversion_time = time.time() - start_time
            print(f"\nConversion completed in {conversion_time:.2f} seconds")
            print(f"Created {len(audio_files)} audio file(s)")
            
            # Final progress update
            if progress_callback:
                progress_callback(100)
                
            logger.info(
                f"Conversion successful: {video_path.name} -> "
                f"{len(audio_files)} audio files"
            )
            
            return True, audio_files
            
        except Exception as e:
            error_msg = f"Conversion error: {str(e)}"
            logger.error(error_msg)
            print(f"\nError: {error_msg}")
            return False, []

    def cleanup_temp_files(self):
        """Clean up temporary audio files with status reporting."""
        try:
            print("\nCleaning up temporary files...")
            count = 0
            for file in self.output_dir.glob("*.mp3"):
                try:
                    file.unlink()
                    print(f"Cleaned up: {file.name}")
                    count += 1
                except Exception as e:
                    logger.error(f"Error deleting {file}: {e}")
                    print(f"Error deleting {file.name}: {e}")
            
            print(f"Cleanup completed: removed {count} temporary files")
            logger.info(f"Cleaned up {count} temporary files")
            
        except Exception as e:
            error_msg = f"Error during cleanup: {str(e)}"
            logger.error(error_msg)
            print(f"Error: {error_msg}")