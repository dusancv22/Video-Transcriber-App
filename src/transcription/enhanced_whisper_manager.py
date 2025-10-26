"""Enhanced Whisper manager using faster-whisper for accurate subtitle timing with word-level timestamps."""

import os
# Disable symlinks on Windows to avoid permission issues
os.environ['HF_HUB_DISABLE_SYMLINKS_WARNING'] = '1'
os.environ['HF_HUB_DISABLE_SYMLINKS'] = '1'

from pathlib import Path
from typing import Dict, Any, Optional, List
from faster_whisper import WhisperModel
import torch
import time
import logging
from datetime import datetime
import tempfile
from pydub import AudioSegment

from src.audio_processing.vad_manager import VADManager

logger = logging.getLogger(__name__)


class EnhancedWhisperManager:
    """Whisper manager using faster-whisper for accurate word-level timestamps."""
    
    def __init__(
        self,
        model_size: str = "large-v2",
        model_path: Optional[str] = None,
        vad_threshold: float = 0.3,  # More sensitive detection
        merge_gap: float = 1.5  # Merge segments within 1.5 seconds for better context
    ):
        """Initialize enhanced Whisper manager with faster-whisper.
        
        Args:
            model_size: Size of the Whisper model (tiny, base, small, medium, large, large-v2, large-v3)
            model_path: Optional path to pre-downloaded model
            vad_threshold: VAD sensitivity threshold (0.0-1.0)
            merge_gap: Maximum gap in seconds to merge adjacent speech regions
        """
        self.model_size = model_size
        self.model_path = model_path
        self.model = None
        
        # Determine compute type and device
        if torch.cuda.is_available():
            self.device = "cuda"
            self.compute_type = "float16"  # Use FP16 on GPU for efficiency
        else:
            self.device = "cpu"
            self.compute_type = "int8"  # Use INT8 on CPU for better performance
        
        self.vad_manager = None  # Initialize lazily
        self.vad_threshold = vad_threshold
        self.merge_gap = merge_gap
        
        logger.info(f"EnhancedWhisperManager initializing with faster-whisper {model_size} on {self.device}")
        logger.info(f"Using compute type: {self.compute_type}")
        
        # Load the model
        self.load_model()
    
    def load_model(self) -> None:
        """Load the faster-whisper model into memory."""
        try:
            start_time = time.time()
            
            # Check if model_path is a standard Whisper .pt file
            if self.model_path and Path(self.model_path).exists():
                if self.model_path.endswith('.pt'):
                    # This is a standard Whisper model, can't use with faster-whisper
                    print(f"Note: {self.model_path} is a standard Whisper model (.pt file)")
                    print(f"faster-whisper requires its own model format. Downloading faster-whisper {self.model_size} model...")
                    logger.info(f"Standard Whisper .pt file detected, using faster-whisper model instead")
                    
                    # Use the model size, not the path
                    self.model = WhisperModel(
                        self.model_size,
                        device=self.device,
                        compute_type=self.compute_type,
                        download_root=None  # Use default cache directory
                    )
                else:
                    # This might be a faster-whisper model directory
                    print(f"Loading faster-whisper model from: {self.model_path}")
                    logger.info(f"Loading model from custom path: {self.model_path}")
                    self.model = WhisperModel(
                        self.model_path,
                        device=self.device,
                        compute_type=self.compute_type
                    )
            else:
                # Use default model loading
                print(f"Loading faster-whisper {self.model_size} model (downloading if needed)...")
                logger.info(f"Loading {self.model_size} model using default method")
                self.model = WhisperModel(
                    self.model_size,
                    device=self.device,
                    compute_type=self.compute_type,
                    download_root=None  # Use default cache directory
                )
            
            load_time = time.time() - start_time
            print(f"Enhanced model loaded successfully on {self.device} (took {load_time:.2f} seconds)")
            logger.info(f"Enhanced model loaded successfully on {self.device} (took {load_time:.2f} seconds)")
            
        except Exception as e:
            error_msg = f"Failed to load faster-whisper model: {str(e)}"
            logger.error(error_msg)
            print(f"Error: {error_msg}")
            raise RuntimeError(error_msg)
    
    def transcribe_with_vad(
        self,
        audio_path: str | Path,
        language: str = None,
        use_vad: bool = True
    ) -> Dict[str, Any]:
        """Transcribe audio with VAD-corrected timestamps.
        
        This method uses VAD to detect speech regions and preserves the
        original video timeline in the subtitle segments.
        
        Args:
            audio_path: Path to audio file
            language: Optional language code
            use_vad: Whether to use VAD (can be disabled for fallback)
            
        Returns:
            Dictionary with transcription results and accurate timestamps
        """
        audio_path = Path(audio_path)
        
        if not audio_path.exists():
            raise FileNotFoundError(f"Audio file not found: {audio_path}")
        
        start_time = time.time()
        
        # If VAD is disabled, fall back to simple method
        if not use_vad:
            logger.info("VAD disabled, using simple transcription with word timestamps")
            return self.simple_transcribe_with_timestamps(audio_path, language)
        
        try:
            logger.info(f"Starting VAD-enhanced transcription of: {audio_path.name}")
            print(f"\nStarting VAD-enhanced transcription of: {audio_path.name}")
            
            # Initialize VAD manager on first use
            if self.vad_manager is None:
                logger.info("Initializing VAD manager on first use...")
                print("Initializing VAD for speech detection...")
                try:
                    self.vad_manager = VADManager(threshold=self.vad_threshold)
                    logger.info("VAD manager initialized successfully")
                except Exception as vad_init_error:
                    logger.error(f"Failed to initialize VAD: {vad_init_error}")
                    print(f"Warning: VAD initialization failed: {vad_init_error}")
                    raise
            
            # Step 1: Detect speech regions using VAD
            print("Detecting speech regions...")
            logger.info(f"Running VAD detection on: {audio_path}")
            vad_regions = self.vad_manager.detect_speech_regions(audio_path)
            
            if not vad_regions:
                logger.warning("No speech detected by VAD")
                print("Warning: No speech detected in audio")
                return {
                    'text': '',
                    'segments': [],
                    'language': language or 'unknown',
                    'duration': time.time() - start_time,
                    'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    'file_size_mb': audio_path.stat().st_size / (1024 * 1024)
                }
            
            # Merge close regions to reduce processing
            merged_regions = self.vad_manager.merge_close_regions(vad_regions, self.merge_gap)
            
            print(f"Detected {len(merged_regions)} speech regions")
            logger.info(f"Processing {len(merged_regions)} speech regions")
            
            # Step 2: Transcribe each speech region
            all_segments = []
            all_text = []
            detected_language = None
            padding = 0.2  # 200ms padding on each side to avoid cutting speech
            
            for i, region in enumerate(merged_regions, 1):
                # Add padding to ensure we don't cut off speech
                region_start = max(0, region['start'] - padding)
                region_end = region['end'] + padding
                duration = region_end - region_start
                
                print(f"Processing region {i}/{len(merged_regions)} ({region_start:.1f}s - {region_end:.1f}s, {duration:.1f}s)")
                
                # Extract audio segment with padding
                temp_segment = None
                try:
                    temp_segment = self.vad_manager.extract_audio_segment(
                        audio_path,
                        region_start,
                        region_end
                    )
                    
                    # Transcribe the segment using faster-whisper
                    transcribe_params = {
                        'audio': str(temp_segment),
                        'beam_size': 5,
                        'best_of': 5,
                        'temperature': 0.0,
                        'condition_on_previous_text': False,
                        'word_timestamps': True,  # CRITICAL: This WORKS on Windows with faster-whisper!
                        'vad_filter': False,  # Disable faster-whisper's VAD since we're using our own VAD
                    }
                    
                    if language:
                        transcribe_params['language'] = language
                    elif detected_language:
                        # Use previously detected language for consistency
                        transcribe_params['language'] = detected_language
                    
                    # faster-whisper returns a generator, not a dict
                    segments_generator, info = self.model.transcribe(**transcribe_params)
                    
                    # Store detected language from first segment
                    if not detected_language:
                        detected_language = info.language
                        print(f"Detected language: {detected_language}")
                    
                    # Process segments from the generator
                    region_text = []
                    first_segment = True
                    for segment in segments_generator:
                        segment_text = segment.text.strip()
                        if segment_text:
                            # DEBUG: Check if faster-whisper returned word timestamps
                            if first_segment and segment.words:
                                logger.info(f"✓ faster-whisper returned {len(segment.words)} words for first segment")
                                first_segment = False
                            elif first_segment:
                                logger.warning(f"✗ NO WORDS returned by faster-whisper for segment: {segment_text[:50]}")
                                first_segment = False
                            
                            # Adjust timestamps to original timeline
                            adjusted_segment = {
                                'start': segment.start + region_start,
                                'end': segment.end + region_start,
                                'text': segment_text
                            }
                            
                            # CRITICAL: Extract word-level timestamps from faster-whisper
                            if segment.words:
                                adjusted_words = []
                                for word in segment.words:
                                    adjusted_word = {
                                        'word': word.word.strip(),
                                        'start': word.start + region_start,
                                        'end': word.end + region_start,
                                        'probability': word.probability
                                    }
                                    adjusted_words.append(adjusted_word)
                                adjusted_segment['words'] = adjusted_words
                            
                            all_segments.append(adjusted_segment)
                            region_text.append(segment_text)
                    
                    # Add text from this region
                    if region_text:
                        all_text.append(' '.join(region_text))
                    
                finally:
                    # Clean up temp file
                    if temp_segment and temp_segment.exists():
                        temp_segment.unlink()
            
            # Combine all text
            full_text = ' '.join(all_text)
            
            # Apply text cleaning (need to add this method)
            cleaned_text = full_text  # For now, just use the raw text
            
            # Post-process segments for optimal subtitle display
            optimized_segments = self._optimize_segments_for_subtitles(all_segments)
            
            # Calculate metrics
            duration = time.time() - start_time
            file_size_mb = audio_path.stat().st_size / (1024 * 1024)
            
            print(f"\nTranscription completed in {duration:.2f} seconds")
            print(f"Generated {len(optimized_segments)} subtitle segments")
            logger.info(f"VAD-enhanced transcription completed in {duration:.2f} seconds")
            
            return {
                'text': cleaned_text,
                'segments': optimized_segments,
                'language': detected_language or language or 'unknown',
                'duration': duration,
                'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                'file_size_mb': file_size_mb,
                'vad_regions': len(merged_regions),
                'method': 'vad_enhanced'
            }
            
        except Exception as e:
            logger.error(f"VAD-enhanced transcription failed: {e}", exc_info=True)
            print(f"Warning: VAD-enhanced transcription failed: {str(e)}")
            print("Falling back to simple faster-whisper transcription...")
            # Fall back to simple transcription without VAD
            return self.simple_transcribe_with_timestamps(audio_path, language)
    
    def _optimize_segments_for_subtitles(self, segments: List[Dict]) -> List[Dict]:
        """Optimize segments for subtitle display with natural boundaries.
        
        Analyzes word-level timestamps to create segments that align with
        natural speech pauses for better subtitle synchronization.
        
        Args:
            segments: Raw segments from transcription
            
        Returns:
            Optimized segments for subtitles with natural boundaries
        """
        if not segments:
            return segments
        
        optimized = []
        i = 0
        
        while i < len(segments):
            current = segments[i].copy()
            duration = current['end'] - current['start']
            
            # Check if segment has word-level timestamps for optimization
            if 'words' in current and current['words']:
                # Analyze word gaps within the segment
                words = current['words']
                natural_splits = []
                
                # Find natural pause points within the segment
                for j in range(len(words) - 1):
                    word_gap = words[j + 1]['start'] - words[j]['end']
                    
                    # If gap is significant (>200ms), it's a natural pause
                    if word_gap > 0.2:
                        natural_splits.append({
                            'index': j,
                            'gap': word_gap,
                            'time': words[j]['end'] + (word_gap / 2)
                        })
                
                # If segment is long and has natural pauses, consider splitting
                if duration > 4.0 and natural_splits:
                    # Find the best split point (prefer middle of segment)
                    segment_middle = current['start'] + (duration / 2)
                    best_split = min(natural_splits, 
                                   key=lambda x: abs(x['time'] - segment_middle))
                    
                    if best_split['gap'] > 0.3:  # Only split at significant pauses
                        # Split the segment at the natural pause
                        split_idx = best_split['index']
                        
                        # First part
                        first_part = current.copy()
                        first_part['end'] = words[split_idx]['end'] + 0.1
                        first_part['text'] = ' '.join([w['word'] for w in words[:split_idx + 1]])
                        first_part['words'] = words[:split_idx + 1]
                        optimized.append(first_part)
                        
                        # Second part
                        second_part = current.copy()
                        second_part['start'] = words[split_idx + 1]['start'] - 0.1
                        second_part['text'] = ' '.join([w['word'] for w in words[split_idx + 1:]])
                        second_part['words'] = words[split_idx + 1:]
                        optimized.append(second_part)
                        
                        i += 1
                        continue
            
            # Check if segment is very short and should be merged
            if duration < 1.0 and i + 1 < len(segments):
                next_segment = segments[i + 1]
                gap = next_segment['start'] - current['end']
                
                # Merge if gap is small
                if gap < 0.3:
                    merged = current.copy()
                    merged['end'] = next_segment['end']
                    merged['text'] = current['text'] + ' ' + next_segment['text']
                    
                    # Merge word timestamps if available
                    if 'words' in current and 'words' in next_segment:
                        merged['words'] = current.get('words', []) + next_segment.get('words', [])
                    
                    optimized.append(merged)
                    i += 2
                else:
                    # Extend short segment slightly for readability
                    if duration < 0.5:
                        current['end'] = current['start'] + 1.0
                    optimized.append(current)
                    i += 1
            else:
                optimized.append(current)
                i += 1
        
        return optimized
    
    def transcribe_audio_with_timestamps(self, audio_path: str | Path, language: str = None) -> Dict[str, Any]:
        """Override parent method to use VAD by default.
        
        Args:
            audio_path: Path to audio file
            language: Optional language code
            
        Returns:
            Transcription results with accurate timestamps
        """
        # Try with VAD first
        try:
            return self.transcribe_with_vad(audio_path, language, use_vad=True)
        except Exception as e:
            logger.warning(f"VAD transcription failed, trying without VAD: {e}")
            print("VAD transcription failed, trying direct transcription without VAD...")
            # Fall back to simple transcription without VAD
            return self.simple_transcribe_with_timestamps(audio_path, language)
    
    def simple_transcribe_with_timestamps(self, audio_path: str | Path, language: str = None) -> Dict[str, Any]:
        """Simple transcription using faster-whisper with word timestamps but without VAD.
        
        Args:
            audio_path: Path to audio file
            language: Optional language code
            
        Returns:
            Transcription results with word-level timestamps
        """
        audio_path = Path(audio_path)
        
        if not audio_path.exists():
            raise FileNotFoundError(f"Audio file not found: {audio_path}")
        
        try:
            start_time = time.time()
            print(f"\nStarting simple faster-whisper transcription of: {audio_path.name}")
            logger.info(f"Starting simple transcription with word timestamps")
            
            # Prepare transcription parameters for faster-whisper
            transcribe_params = {
                'audio': str(audio_path),
                'beam_size': 5,
                'best_of': 5,
                'temperature': 0.0,
                'condition_on_previous_text': False,
                'word_timestamps': True,  # Enable word-level timestamps
                'vad_filter': False,  # Disable VAD to avoid onnxruntime issues
            }
            
            if language:
                transcribe_params['language'] = language
            
            # Get segments from faster-whisper
            segments_generator, info = self.model.transcribe(**transcribe_params)
            
            # Process segments
            segments = []
            full_text = []
            
            for segment in segments_generator:
                segment_text = segment.text.strip()
                if segment_text:
                    segment_dict = {
                        'start': segment.start,
                        'end': segment.end,
                        'text': segment_text
                    }
                    
                    # Extract word-level timestamps
                    if segment.words:
                        segment_dict['words'] = []
                        for word in segment.words:
                            segment_dict['words'].append({
                                'word': word.word.strip(),
                                'start': word.start,
                                'end': word.end,
                                'probability': word.probability
                            })
                    
                    segments.append(segment_dict)
                    full_text.append(segment_text)
            
            # Join all text
            complete_text = ' '.join(full_text)
            
            # Post-process segments
            optimized_segments = self._optimize_segments_for_subtitles(segments)
            
            # Calculate metrics
            duration = time.time() - start_time
            file_size_mb = audio_path.stat().st_size / (1024 * 1024)
            
            # Count total words
            total_words = sum(len(seg.get('words', [])) for seg in optimized_segments)
            
            print(f"Transcription completed in {duration:.2f} seconds")
            print(f"Generated {len(optimized_segments)} segments with {total_words} word timestamps")
            
            return {
                'text': complete_text,
                'segments': optimized_segments,
                'language': info.language if hasattr(info, 'language') else language,
                'duration': duration,
                'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                'file_size_mb': file_size_mb,
                'has_word_timestamps': total_words > 0,
                'method': 'simple_faster_whisper'
            }
            
        except Exception as e:
            error_msg = f"Simple transcription failed: {str(e)}"
            logger.error(error_msg)
            raise RuntimeError(error_msg)
    
    def transcribe_audio(self, audio_path: str | Path, language: str = None) -> Dict[str, Any]:
        """Standard transcription without timestamps for regular text output.
        
        Args:
            audio_path: Path to audio file
            language: Optional language code
            
        Returns:
            Transcription results without detailed timestamps
        """
        audio_path = Path(audio_path)
        
        if not audio_path.exists():
            raise FileNotFoundError(f"Audio file not found: {audio_path}")
        
        try:
            start_time = time.time()
            print(f"\nStarting standard transcription of: {audio_path.name}")
            
            # Simpler parameters for standard transcription
            transcribe_params = {
                'audio': str(audio_path),
                'beam_size': 5,
                'temperature': 0.0,
                'word_timestamps': False,  # No word timestamps for faster processing
                'vad_filter': False  # Disable VAD to avoid issues
            }
            
            if language:
                transcribe_params['language'] = language
            
            segments_generator, info = self.model.transcribe(**transcribe_params)
            
            # Collect all text
            full_text = []
            for segment in segments_generator:
                if segment.text.strip():
                    full_text.append(segment.text.strip())
            
            complete_text = ' '.join(full_text)
            
            duration = time.time() - start_time
            file_size_mb = audio_path.stat().st_size / (1024 * 1024)
            
            print(f"Transcription completed in {duration:.2f} seconds")
            
            return {
                'text': complete_text,
                'language': info.language if hasattr(info, 'language') else language,
                'duration': duration,
                'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                'file_size_mb': file_size_mb
            }
            
        except Exception as e:
            error_msg = f"Standard transcription failed: {str(e)}"
            logger.error(error_msg)
            raise RuntimeError(error_msg)
    
    def get_model_info(self) -> Dict[str, Any]:
        """Return information about the loaded model."""
        gpu_info = torch.cuda.get_device_properties(0) if torch.cuda.is_available() else None
        
        info = {
            'model_size': self.model_size,
            'device': self.device,
            'compute_type': self.compute_type,
            'cuda_available': torch.cuda.is_available(),
            'cuda_device': torch.cuda.get_device_name(0) if torch.cuda.is_available() else None,
            'gpu_memory_gb': f"{gpu_info.total_memory / 1024**3:.1f}GB" if gpu_info else None,
            'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'backend': 'faster-whisper'
        }
        
        logger.info(f"Enhanced model info: {info}")
        return info
    
    def get_quick_offset(self, audio_path: str | Path) -> float:
        """Get a quick offset for the first speech in the audio.
        
        Useful for manual sync adjustment without full VAD processing.
        
        Args:
            audio_path: Path to audio file
            
        Returns:
            Time offset in seconds to first speech
        """
        try:
            if self.vad_manager:
                return self.vad_manager.get_first_speech_time(audio_path)
            return 0.0
        except Exception as e:
            logger.error(f"Failed to get speech offset: {e}")
            return 0.0