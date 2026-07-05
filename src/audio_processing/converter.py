from pathlib import Path
import ffmpeg
from typing import Tuple, Optional, Callable
import logging
import math
import time
import os
import subprocess
from datetime import datetime

from src.audio_processing.optimizer import AudioQualityOptimizer

logger = logging.getLogger(__name__)

class AudioConverter:
    # Whisper resamples everything to 16kHz mono internally, so extracting to
    # 16kHz mono WAV is lossless for transcription purposes and avoids the
    # quality hit of an intermediate MP3 re-encode.
    AUDIO_SUFFIX = ".wav"

    def __init__(self, enable_quality_pass: bool = True):
        """Initialize AudioConverter with output directory setup.

        Args:
            enable_quality_pass: Analyze loudness after extraction and boost
                quiet audio so VAD/language detection get a usable signal.
        """
        self.output_dir = Path("temp/audio")
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self._last_split_metadata = []  # Store metadata from last split operation
        self.enable_quality_pass = enable_quality_pass
        self.quality_optimizer = AudioQualityOptimizer()
        self._last_quality_report = {}
        logger.info(f"AudioConverter initialized with output directory: {self.output_dir}")

    def get_last_quality_report(self) -> dict:
        """Get the audio quality pass report from the last conversion."""
        return self._last_quality_report.copy()

    def get_last_split_metadata(self) -> list:
        """
        Get metadata from the last split operation.
        
        Returns:
            list: List of dictionaries containing segment metadata including overlap information
        """
        return self._last_split_metadata.copy()

    def _get_audio_duration(self, audio_path: str) -> float:
        """
        Get duration of audio file using ffmpeg.
        
        Args:
            audio_path: Path to the audio file
            
        Returns:
            float: Duration in seconds
        """
        try:
            probe = ffmpeg.probe(audio_path)
            duration = float(probe['streams'][0]['duration'])
            return duration
        except Exception as e:
            logger.error(f"Error getting audio duration: {e}")
            return 0.0

    def _extract_audio_segment(self, input_path: str, output_path: str, start_time: float, end_time: float) -> bool:
        """
        Extract audio segment using ffmpeg.
        
        Args:
            input_path: Source audio file path
            output_path: Output segment path
            start_time: Start time in seconds
            end_time: End time in seconds
            
        Returns:
            bool: Success status
        """
        try:
            duration = end_time - start_time
            (
                ffmpeg
                .input(input_path, ss=start_time, t=duration)
                .output(output_path, **self._audio_output_params(output_path))
                .overwrite_output()
                .run(capture_stdout=True, capture_stderr=True)
            )
            return True
        except Exception as e:
            logger.error(f"Error extracting audio segment: {e}")
            return False

    @staticmethod
    def _audio_output_params(output_path: str | Path) -> dict:
        """FFmpeg output parameters matching the target extension."""
        if str(output_path).lower().endswith('.wav'):
            # 16kHz mono PCM: exactly what Whisper consumes internally.
            return {'acodec': 'pcm_s16le', 'ar': 16000, 'ac': 1}
        return {'acodec': 'libmp3lame', 'ar': 44100}

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

    def split_audio_if_needed(self, audio_path: str, max_duration_seconds: float = 1500.0, overlap_seconds: float = 2.5):
        """
        Split audio file if longer than max_duration_seconds with overlap between segments
        to prevent transcription repetition issues.

        Splitting is duration-based (not size-based): chunk length is what matters
        for transcription memory/quality, and duration is stable across audio
        codecs (a 16kHz WAV is ~15x larger than the equivalent MP3).

        Args:
            audio_path: Path to the audio file
            max_duration_seconds: Maximum duration in seconds before splitting (default: 25 min)
            overlap_seconds: Seconds of overlap between adjacent segments (default: 2.5)

        Returns:
            list[str]: List of paths to audio segments
        """
        print(f"\nChecking duration for: {audio_path}")
        self._last_split_metadata = []
        split_files = []

        try:
            duration = self._get_audio_duration(audio_path)
            if duration <= 0:
                raise RuntimeError("Could not determine audio duration for splitting")
            print(f"Audio duration: {duration:.1f}s ({duration / 60:.1f} min)")

            if duration <= max_duration_seconds:
                print("Duration within limits - no splitting needed")
                return [audio_path]

            print(f"File needs splitting (exceeds {max_duration_seconds / 60:.0f} min)")

            # Calculate segments
            segments = math.ceil(duration / max_duration_seconds)
            segment_duration = duration / segments
            print(f"Splitting into {segments} segments of {segment_duration:.2f} seconds each")
            print(f"Using {overlap_seconds:.1f}s overlap between segments to prevent repetition")
            
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
                
                source_path = Path(audio_path)
                segment_path = source_path.parent / f"{source_path.stem}_part{i+1}{source_path.suffix}"
                print(f"\nCreating segment {i+1}/{segments}: {segment_path.name}")
                print(f"Time range: {start_time:.2f}s to {end_time:.2f}s")
                if has_start_overlap or has_end_overlap:
                    overlap_info = []
                    if has_start_overlap:
                        overlap_info.append(f"start overlap: {overlap_seconds:.1f}s")
                    if has_end_overlap:
                        overlap_info.append(f"end overlap: {overlap_seconds:.1f}s")
                    print(f"Overlap: {', '.join(overlap_info)}")
                
                # Store metadata for downstream text/subtitle deduplication.
                # content_* marks the non-overlapped timeline slice owned by
                # this chunk; start/end include the audio overlap safety margin.
                segment_metadata.append({
                    'segment_index': i,
                    'start_time': start_time,
                    'end_time': end_time,
                    'duration': end_time - start_time,
                    'content_start_time': i * segment_duration,
                    'content_end_time': min((i + 1) * segment_duration, duration),
                    'has_start_overlap': has_start_overlap,
                    'has_end_overlap': has_end_overlap,
                    'overlap_seconds': overlap_seconds if (has_start_overlap or has_end_overlap) else 0
                })
                
                # Extract and save segment
                if self._extract_audio_segment(audio_path, str(segment_path), start_time, end_time):
                    split_files.append(str(segment_path))
                    print(f"Segment {i+1} created successfully")
                else:
                    raise RuntimeError(f"Failed to create segment {i+1}")
                
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
            self._last_split_metadata = []
            for split_file in split_files:
                try:
                    Path(split_file).unlink(missing_ok=True)
                except Exception as cleanup_error:
                    logger.warning(f"Error deleting partial segment {split_file}: {cleanup_error}")
            return [audio_path] if Path(audio_path).exists() else []

    def convert_video_to_audio(self, video_path: str, progress_callback: Optional[Callable[[float], None]] = None) -> Tuple[bool, list[str]]:
        """
        Convert a media file (video or audio) to 16kHz mono WAV and split if needed,
        with an optional loudness quality pass for quiet audio.

        Args:
            video_path: Path to the input media file
            progress_callback: Optional callback for progress updates

        Returns:
            Tuple[bool, list[str]]: Success status and list of audio file paths
        """
        try:
            start_time = time.time()
            video_path = Path(video_path)
            output_path = self.output_dir / f"{video_path.stem}{self.AUDIO_SUFFIX}"

            print(f"\nConverting media to audio: {video_path.name}")
            print(f"Output path: {output_path}")
            logger.info(f"Starting conversion: {video_path} -> {output_path}")

            # Update progress
            if progress_callback:
                # Normalized progress: 0.0 -> 1.0
                progress_callback(0.0)

            # Check if video has audio track and convert using ffmpeg
            print("Extracting audio...")
            try:
                (
                    ffmpeg
                    .input(str(video_path))
                    .output(str(output_path), **self._audio_output_params(output_path))
                    .overwrite_output()
                    .run(capture_stdout=True, capture_stderr=True)
                )
                print("Audio extraction completed")
            except ffmpeg.Error as e:
                error_msg = f"FFmpeg error during conversion: {e.stderr.decode() if e.stderr else str(e)}"
                logger.error(error_msg)
                print(f"Error: {error_msg}")
                return False, []

            # Update progress
            if progress_callback:
                progress_callback(0.5)

            # Audio quality pass: boost quiet audio so VAD and language
            # detection work reliably (quiet audio is a common cause of poor
            # non-English recognition).
            self._last_quality_report = {}
            if self.enable_quality_pass:
                print("\nRunning audio quality pass (loudness check)...")
                self._last_quality_report = self.quality_optimizer.process(str(output_path))
                if self._last_quality_report.get('enhanced'):
                    print(
                        f"Quiet audio boosted: {self._last_quality_report.get('input_loudness_lufs')} LUFS "
                        f"-> {self._last_quality_report.get('target_lufs')} LUFS target"
                    )
                elif self._last_quality_report.get('analyzed'):
                    print("Audio loudness OK - no boost needed")
                else:
                    print("Loudness analysis unavailable - continuing with original audio")

            if progress_callback:
                progress_callback(0.6)

            print("\nInitial conversion completed, checking if splitting is needed")
            # Split if needed and return list of file paths
            audio_files = self.split_audio_if_needed(str(output_path))
            
            # Calculate conversion time
            conversion_time = time.time() - start_time
            print(f"\nConversion completed in {conversion_time:.2f} seconds")
            print(f"Created {len(audio_files)} audio file(s)")
            
            # Final progress update
            if progress_callback:
                progress_callback(1.0)
                
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
            temp_audio_files = list(self.output_dir.glob("*.wav")) + list(self.output_dir.glob("*.mp3"))
            for file in temp_audio_files:
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
