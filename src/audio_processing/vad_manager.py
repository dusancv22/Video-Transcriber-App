"""Voice Activity Detection manager for detecting speech regions in audio."""

import torch
import torchaudio
from pathlib import Path
from typing import List, Dict, Tuple, Optional
import logging
import numpy as np
from pydub import AudioSegment
from pydub.utils import which
import tempfile
import os
import warnings

# Configure pydub to find ffmpeg
AudioSegment.converter = which("ffmpeg")
AudioSegment.ffmpeg = which("ffmpeg")
AudioSegment.ffprobe = which("ffprobe")

logger = logging.getLogger(__name__)


class VADManager:
    """Manages Voice Activity Detection using Silero VAD model."""
    
    def __init__(
        self,
        threshold: float = 0.3,  # Lower threshold for more sensitive detection
        min_speech_duration_ms: int = 100,  # Shorter minimum to catch brief words
        min_silence_duration_ms: int = 300,  # Longer silence to avoid over-splitting
        sample_rate: int = 16000
    ):
        """Initialize VAD manager with configuration.
        
        Args:
            threshold: Speech detection threshold (0.0-1.0)
            min_speech_duration_ms: Minimum duration to consider as speech
            min_silence_duration_ms: Minimum silence to split segments
            sample_rate: Audio sample rate for VAD processing
        """
        self.threshold = threshold
        self.min_speech_duration_ms = min_speech_duration_ms
        self.min_silence_duration_ms = min_silence_duration_ms
        self.sample_rate = sample_rate
        self.model = None
        self.utils = None
        self._model_loaded = False
        
        logger.info(f"Initializing VADManager with threshold={threshold}")
    
    def _load_model(self):
        """Load Silero VAD model."""
        if self._model_loaded:
            logger.debug("VAD model already loaded")
            return
            
        try:
            logger.info("Loading Silero VAD model...")
            print("Loading VAD model (this may take a moment on first use)...")
            
            # Set cache directory
            torch.hub.set_dir(Path.home() / '.cache' / 'torch' / 'hub')
            
            # Download and load the model with trust_repo to avoid prompts
            self.model, self.utils = torch.hub.load(
                repo_or_dir='snakers4/silero-vad',
                model='silero_vad',
                force_reload=False,
                onnx=False,
                verbose=False,
                trust_repo=True  # Trust the repo to avoid interactive prompts
            )
            
            self._model_loaded = True
            logger.info("Silero VAD model loaded successfully")
            print("VAD model loaded successfully")
            
        except Exception as e:
            logger.error(f"Failed to load VAD model: {e}", exc_info=True)
            raise RuntimeError(f"Failed to load VAD model: {e}")
    
    def detect_speech_regions(
        self,
        audio_path: str | Path,
        return_milliseconds: bool = False
    ) -> List[Dict[str, float]]:
        """Detect speech regions in audio file.
        
        This method analyzes the audio and returns timestamps of where
        speech occurs, preserving the original timeline.
        
        Args:
            audio_path: Path to audio file (MP3 or WAV)
            return_milliseconds: Return times in milliseconds instead of seconds
            
        Returns:
            List of dictionaries with 'start' and 'end' keys representing
            speech regions in the original audio timeline
        """
        # Load model on first use
        self._load_model()
        
        audio_path = Path(audio_path)
        
        if not audio_path.exists():
            raise FileNotFoundError(f"Audio file not found: {audio_path}")
        
        logger.info(f"Detecting speech regions in: {audio_path.name}")
        
        try:
            # Convert to WAV if needed (VAD works best with WAV)
            logger.info(f"Ensuring audio is in WAV format: {audio_path}")
            wav_path = self._ensure_wav_format(audio_path)
            logger.info(f"Audio path for VAD: {wav_path}")
            
            # Load audio with torchaudio
            logger.info(f"Loading audio with torchaudio: {wav_path}")
            waveform, orig_sample_rate = torchaudio.load(str(wav_path))
            logger.info(f"Audio loaded: shape={waveform.shape}, sample_rate={orig_sample_rate}")
            
            # Resample to 16kHz if needed (Silero VAD requirement)
            if orig_sample_rate != self.sample_rate:
                resampler = torchaudio.transforms.Resample(
                    orig_sample_rate, 
                    self.sample_rate
                )
                waveform = resampler(waveform)
            
            # Convert to mono if stereo
            if waveform.shape[0] > 1:
                waveform = torch.mean(waveform, dim=0, keepdim=True)
            
            # Get VAD timestamps using the utility function
            get_speech_timestamps = self.utils[0]
            
            speech_timestamps = get_speech_timestamps(
                waveform[0],
                self.model,
                threshold=self.threshold,
                min_speech_duration_ms=self.min_speech_duration_ms,
                min_silence_duration_ms=self.min_silence_duration_ms,
                return_seconds=not return_milliseconds,
                sampling_rate=self.sample_rate
            )
            
            # Convert to our format
            speech_regions = []
            for ts in speech_timestamps:
                if return_milliseconds:
                    speech_regions.append({
                        'start': ts['start'],
                        'end': ts['end']
                    })
                else:
                    # Already in seconds
                    speech_regions.append({
                        'start': ts['start'],
                        'end': ts['end']
                    })
            
            # Clean up temp file if created
            if wav_path != audio_path and wav_path.exists():
                wav_path.unlink()
            
            logger.info(f"Detected {len(speech_regions)} speech regions")
            
            # Log first and last regions for debugging
            if speech_regions:
                first = speech_regions[0]
                last = speech_regions[-1]
                unit = "ms" if return_milliseconds else "s"
                logger.info(f"First speech: {first['start']:.2f}{unit} - {first['end']:.2f}{unit}")
                logger.info(f"Last speech: {last['start']:.2f}{unit} - {last['end']:.2f}{unit}")
            
            return speech_regions
            
        except Exception as e:
            logger.error(f"VAD detection failed: {e}")
            raise RuntimeError(f"VAD detection failed: {e}")
    
    def _ensure_wav_format(self, audio_path: Path) -> Path:
        """Convert audio to WAV format if needed.
        
        Args:
            audio_path: Path to audio file
            
        Returns:
            Path to WAV file (original or converted)
        """
        if audio_path.suffix.lower() == '.wav':
            return audio_path
        
        logger.info(f"Converting {audio_path.suffix} to WAV for VAD processing")
        
        # Create temp WAV file
        temp_wav = tempfile.NamedTemporaryFile(suffix='.wav', delete=False)
        temp_wav_path = Path(temp_wav.name)
        temp_wav.close()
        
        try:
            # Check if ffmpeg is available
            if not which("ffmpeg"):
                logger.warning("ffmpeg not found in PATH, trying direct file read")
                # Try to use torchaudio directly for MP3
                if audio_path.suffix.lower() == '.mp3':
                    return audio_path  # torchaudio can handle MP3 directly
                else:
                    raise RuntimeError("ffmpeg is required for audio conversion")
            
            # Use pydub to convert
            audio = AudioSegment.from_file(str(audio_path))
            
            # Log the duration to debug truncation issues
            duration_seconds = len(audio) / 1000.0
            logger.info(f"Audio duration after loading: {duration_seconds:.2f} seconds")
            print(f"DEBUG: Loaded audio duration: {duration_seconds:.2f} seconds ({duration_seconds/60:.2f} minutes)")
            
            audio.export(str(temp_wav_path), format='wav')
            
            # Verify the exported file duration
            exported_audio = AudioSegment.from_file(str(temp_wav_path))
            exported_duration = len(exported_audio) / 1000.0
            logger.info(f"Exported WAV duration: {exported_duration:.2f} seconds")
            print(f"DEBUG: Exported WAV duration: {exported_duration:.2f} seconds ({exported_duration/60:.2f} minutes)")
            
            return temp_wav_path
            
        except Exception as e:
            # Clean up on error
            if temp_wav_path.exists():
                temp_wav_path.unlink()
            raise RuntimeError(f"Failed to convert audio to WAV: {e}")
    
    def extract_audio_segment(
        self,
        audio_path: str | Path,
        start_time: float,
        end_time: float,
        output_path: Optional[str | Path] = None
    ) -> Path:
        """Extract a segment of audio between start and end times.
        
        Args:
            audio_path: Path to source audio file
            start_time: Start time in seconds
            end_time: End time in seconds
            output_path: Optional output path (temp file if not specified)
            
        Returns:
            Path to extracted audio segment
        """
        audio_path = Path(audio_path)
        
        if output_path is None:
            # Create temp file
            temp_file = tempfile.NamedTemporaryFile(
                suffix=audio_path.suffix,
                delete=False
            )
            output_path = Path(temp_file.name)
            temp_file.close()
        else:
            output_path = Path(output_path)
        
        try:
            # Load audio with pydub
            audio = AudioSegment.from_file(str(audio_path))
            
            # Extract segment (pydub uses milliseconds)
            start_ms = int(start_time * 1000)
            end_ms = int(end_time * 1000)
            segment = audio[start_ms:end_ms]
            
            # Export segment
            segment.export(str(output_path), format=output_path.suffix[1:])
            
            logger.info(f"Extracted audio segment: {start_time:.2f}s - {end_time:.2f}s")
            
            return output_path
            
        except Exception as e:
            # Clean up on error
            if output_path.exists():
                output_path.unlink()
            raise RuntimeError(f"Failed to extract audio segment: {e}")
    
    def merge_close_regions(
        self,
        regions: List[Dict[str, float]],
        max_gap: float = 0.5
    ) -> List[Dict[str, float]]:
        """Merge speech regions that are close together.
        
        Args:
            regions: List of speech regions
            max_gap: Maximum gap in seconds to merge regions
            
        Returns:
            Merged list of regions
        """
        if not regions:
            return regions
        
        merged = []
        current = regions[0].copy()
        
        for next_region in regions[1:]:
            gap = next_region['start'] - current['end']
            
            if gap <= max_gap:
                # Merge regions
                current['end'] = next_region['end']
            else:
                # Keep separate
                merged.append(current)
                current = next_region.copy()
        
        # Don't forget the last region
        merged.append(current)
        
        logger.info(f"Merged {len(regions)} regions into {len(merged)} regions")
        
        return merged
    
    def get_first_speech_time(self, audio_path: str | Path) -> float:
        """Get the timestamp of the first detected speech.
        
        Useful for quick offset detection without full VAD analysis.
        
        Args:
            audio_path: Path to audio file
            
        Returns:
            Time in seconds when first speech is detected, or 0.0 if no speech
        """
        regions = self.detect_speech_regions(audio_path)
        
        if regions:
            return regions[0]['start']
        
        logger.warning("No speech detected in audio")
        return 0.0
    
    def calculate_speech_ratio(self, regions: List[Dict[str, float]], total_duration: float) -> float:
        """Calculate the ratio of speech to total duration.
        
        Args:
            regions: List of speech regions
            total_duration: Total audio duration in seconds
            
        Returns:
            Ratio of speech time to total time (0.0 - 1.0)
        """
        if not regions or total_duration <= 0:
            return 0.0
        
        speech_duration = sum(r['end'] - r['start'] for r in regions)
        ratio = speech_duration / total_duration
        
        logger.info(f"Speech ratio: {ratio:.2%} ({speech_duration:.1f}s of {total_duration:.1f}s)")
        
        return ratio