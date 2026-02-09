from pathlib import Path
from typing import Dict, Any, Optional
import whisper
import torch
import time
import logging
from datetime import datetime
import os

logger = logging.getLogger(__name__)

class WhisperManager:
    def __init__(self, model_size: str = "large", model_path: Optional[str] = None):
        """Initialize Whisper manager with specified model size.
        
        Args:
            model_size: Size of the model (tiny, base, small, medium, large)
            model_path: Optional path to a pre-downloaded model file
        """
        self.model_size = model_size
        self.model_path = model_path
        self.model = None
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        logger.info(f"Initializing WhisperManager with {model_size} model on {self.device}")
        if model_path:
            logger.info(f"Using custom model path: {model_path}")
        self.load_model()
        
    def load_model(self) -> None:
        """Load the Whisper model into memory."""
        try:
            start_time = time.time()
            
            if self.model_path and Path(self.model_path).exists():
                # Load model from custom path
                print(f"Loading Whisper model from: {self.model_path}")
                logger.info(f"Loading model from custom path: {self.model_path}")
                
                # Load the model using the custom path
                self.model = whisper.load_model(self.model_path).to(self.device)
                
                # Try to detect model size from filename if not specified
                if 'large' in Path(self.model_path).name.lower():
                    self.model_size = 'large'
                elif 'medium' in Path(self.model_path).name.lower():
                    self.model_size = 'medium'
                elif 'small' in Path(self.model_path).name.lower():
                    self.model_size = 'small'
                elif 'base' in Path(self.model_path).name.lower():
                    self.model_size = 'base'
                elif 'tiny' in Path(self.model_path).name.lower():
                    self.model_size = 'tiny'
                    
            else:
                # Use default Whisper loading (will download if needed)
                print(f"Loading Whisper {self.model_size} model (downloading if needed)...")
                logger.info(f"Loading {self.model_size} model using default method")
                self.model = whisper.load_model(self.model_size).to(self.device)
            
            load_time = time.time() - start_time
            print(f"Model loaded successfully on {self.device} (took {load_time:.2f} seconds)")
            logger.info(f"Model loaded successfully on {self.device} (took {load_time:.2f} seconds)")
            
        except Exception as e:
            error_msg = f"Failed to load Whisper model: {str(e)}"
            logger.error(error_msg)
            print(f"Error: {error_msg}")
            raise RuntimeError(error_msg)
    
    def reload_model(self, model_size: str, model_path: Optional[str] = None) -> None:
        """Reload the model with new settings.
        
        Args:
            model_size: New model size
            model_path: Optional new model path
        """
        logger.info(f"Reloading model: size={model_size}, path={model_path}")
        
        # Clear current model from memory
        if self.model:
            del self.model
            torch.cuda.empty_cache() if torch.cuda.is_available() else None
        
        # Update settings
        self.model_size = model_size
        self.model_path = model_path
        
        # Load new model
        self.load_model()

    def transcribe_audio_with_timestamps(self, audio_path: str | Path, language: str = None) -> Dict[str, Any]:
        """
        Transcribe audio file and return both text and timestamp segments.
        
        This method returns segments with timestamps for subtitle generation
        while maintaining the same transcription quality parameters.
        
        Args:
            audio_path: Path to the audio file to transcribe
            language: Optional language code (e.g., 'en', 'es', 'fr'). If None, auto-detect.
            
        Returns:
            Dictionary containing:
                - text: Full transcription text
                - segments: List of segments with start, end, and text
                - language: Detected or specified language
                - duration: Processing duration
                - timestamp: Processing timestamp
                - file_size_mb: File size in MB
        """
        if not self.model:
            raise RuntimeError("Model not loaded. Call load_model() first.")
        
        audio_path = Path(audio_path)
        
        # Basic validation
        if not audio_path.exists():
            raise FileNotFoundError(f"Audio file not found: {audio_path}")
        
        if audio_path.suffix.lower() != '.mp3':
            raise ValueError(f"Expected MP3 file, got: {audio_path.suffix}")
        
        try:
            # Log start of transcription
            start_time = time.time()
            print(f"\nStarting transcription with timestamps of: {audio_path.name}")
            logger.info(f"Starting transcription with timestamps of: {audio_path.name}")
            
            # Get file size for logging
            file_size_mb = audio_path.stat().st_size / (1024 * 1024)
            print(f"File size: {file_size_mb:.2f} MB")
            
            # Perform transcription with word-level timestamps for better accuracy
            transcribe_params = {
                'audio': str(audio_path),
                'task': 'transcribe',
                'fp16': self.device == "cuda",  # Use FP16 on GPU for ~2x speed, FP32 on CPU
                'temperature': 0.0,
                'compression_ratio_threshold': 2.4,
                'logprob_threshold': -1.0,
                'condition_on_previous_text': False,
                'initial_prompt': None,
                'suppress_blank': True,
                'suppress_tokens': [-1],
                'word_timestamps': True,  # Enable word-level timestamps for better accuracy
            }
            
            # Add language parameter if specified
            if language:
                transcribe_params['language'] = language
                print(f"Transcribing in {language} language")
                logger.info(f"Using specified language: {language}")
            else:
                print("Auto-detecting language...")
                logger.info("Language auto-detection enabled")
            
            result = self.model.transcribe(**transcribe_params)
            
            # Extract segments with timestamps - now with better timing
            segments = []
            if 'segments' in result:
                for segment in result['segments']:
                    # Use the actual segment timing from Whisper
                    # These should be more accurate with word_timestamps enabled
                    segment_text = segment['text'].strip()
                    if segment_text:  # Only add non-empty segments
                        segment_dict = {
                            'start': segment['start'],
                            'end': segment['end'],
                            'text': segment_text
                        }
                        
                        # CRITICAL: Preserve word-level timestamps if available
                        if 'words' in segment and segment['words']:
                            segment_dict['words'] = []
                            for word in segment['words']:
                                if word.get('word') or word.get('text'):
                                    segment_dict['words'].append({
                                        'word': word.get('word', word.get('text', '')),
                                        'start': word.get('start', 0),
                                        'end': word.get('end', 0)
                                    })
                        
                        segments.append(segment_dict)
                
                # Post-process segments to merge very short ones and fix timing issues
                segments = self._optimize_segment_timing(segments)
                
                logger.info(f"Extracted {len(segments)} segments with timestamps")
            
            # Get the raw transcription text
            raw_text = result['text']
            
            # Apply repetition detection and cleanup
            cleaned_text = self._clean_transcription_text(raw_text)
            
            # Check if cleaning was applied
            if cleaned_text != raw_text:
                print(f"Repetition detected and cleaned in: {audio_path.name}")
                logger.info(f"Repetition detected and cleaned in transcription of: {audio_path.name}")
            
            # Calculate duration and log completion
            duration = time.time() - start_time
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            print(f"Transcription completed in {duration:.2f} seconds")
            print(f"Detected language: {result['language']}")
            print(f"Generated {len(segments)} subtitle segments")
            logger.info(f"Transcription of {audio_path.name} completed in {duration:.2f} seconds")
            
            return {
                'text': cleaned_text,
                'segments': segments,
                'language': result['language'],
                'duration': duration,
                'timestamp': timestamp,
                'file_size_mb': file_size_mb
            }
            
        except Exception as e:
            error_msg = f"Transcription failed for {audio_path.name}: {str(e)}"
            logger.error(error_msg)
            print(f"Error: {error_msg}")
            raise RuntimeError(error_msg)
    
    def _optimize_segment_timing(self, segments):
        """Optimize segment timing by merging very short segments and fixing gaps.
        
        Args:
            segments: List of segments from Whisper
            
        Returns:
            Optimized list of segments
        """
        if not segments:
            return segments
        
        optimized = []
        i = 0
        
        while i < len(segments):
            current = segments[i].copy()
            
            # Check if this segment is very short (less than 1 second)
            duration = current['end'] - current['start']
            
            if duration < 1.0 and i + 1 < len(segments):
                # Check if we should merge with next segment
                next_segment = segments[i + 1]
                gap_to_next = next_segment['start'] - current['end']
                
                # Merge if gap is small (less than 0.5 seconds)
                if gap_to_next < 0.5:
                    # Merge segments
                    current['end'] = next_segment['end']
                    current['text'] = current['text'] + ' ' + next_segment['text']
                    
                    # Merge word timestamps if available
                    if 'words' in current and 'words' in next_segment:
                        current['words'] = current.get('words', []) + next_segment.get('words', [])
                    elif 'words' in next_segment:
                        current['words'] = next_segment['words']
                    
                    i += 2  # Skip next segment since we merged it
                else:
                    # Keep segment as is
                    optimized.append(current)
                    i += 1
            else:
                # Keep segment as is
                optimized.append(current)
                i += 1
        
        return optimized
    
    def transcribe_audio(self, audio_path: str | Path, language: str = None) -> Dict[str, Any]:
        """
        Transcribe a single MP3 audio file with enhanced repetition prevention.
        
        Uses optimized Whisper parameters to prevent repetitive transcription output
        and includes post-processing to detect and clean any remaining repetition.
        
        Args:
            audio_path: Path to the audio file to transcribe
            language: Optional language code (e.g., 'en', 'es', 'fr'). If None, auto-detect.
        """
        if not self.model:
            raise RuntimeError("Model not loaded. Call load_model() first.")
        
        audio_path = Path(audio_path)
        
        # Basic validation
        if not audio_path.exists():
            raise FileNotFoundError(f"Audio file not found: {audio_path}")
        
        if audio_path.suffix.lower() != '.mp3':
            raise ValueError(f"Expected MP3 file, got: {audio_path.suffix}")
        
        try:
            # Log start of transcription
            start_time = time.time()
            print(f"\nStarting transcription of: {audio_path.name}")
            logger.info(f"Starting transcription of: {audio_path.name}")
            
            # Get file size for logging
            file_size_mb = audio_path.stat().st_size / (1024 * 1024)
            print(f"File size: {file_size_mb:.2f} MB")
            
            # Log transcription parameters for debugging
            print(f"DEBUG: Starting transcription with model {self.model_size}")
            print(f"DEBUG: Device: {self.device}")
            print(f"DEBUG: Audio path: {audio_path}")
            
            # Perform transcription with enhanced repetition prevention parameters
            # Note: Removed no_captions_threshold as it's not supported in this version
            transcribe_params = {
                'audio': str(audio_path),
                'task': 'transcribe',  # Ensure we're in transcription mode
                'fp16': self.device == "cuda",  # Use FP16 on GPU for ~2x speed, FP32 on CPU
                'temperature': 0.0,  # Eliminate randomness for consistent output
                'compression_ratio_threshold': 2.4,  # Detect repetitive/low-quality content
                'logprob_threshold': -1.0,  # Filter out low-confidence transcriptions
                'condition_on_previous_text': False,  # Prevent context bleeding between segments
                'initial_prompt': None,  # Clear initial prompt to prevent bias
                'suppress_blank': True,  # Remove blank/empty segments
                'suppress_tokens': [-1],  # Suppress specific problematic tokens if needed
            }
            
            # Add language parameter if specified
            if language:
                transcribe_params['language'] = language
                print(f"Transcribing in {language} language")
                logger.info(f"Using specified language: {language}")
            else:
                print("Auto-detecting language...")
                logger.info("Language auto-detection enabled")
            
            result = self.model.transcribe(**transcribe_params)
            
            print(f"DEBUG: Transcription result received successfully")
            
            # Get the raw transcription text
            raw_text = result['text']
            
            # Apply repetition detection and cleanup
            cleaned_text = self._clean_transcription_text(raw_text)
            
            # Check if cleaning was applied
            if cleaned_text != raw_text:
                print(f"Repetition detected and cleaned in: {audio_path.name}")
                logger.info(f"Repetition detected and cleaned in transcription of: {audio_path.name}")
            
            # Calculate duration and log completion
            duration = time.time() - start_time
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            print(f"Transcription completed in {duration:.2f} seconds")
            print(f"Detected language: {result['language']}")
            logger.info(f"Transcription of {audio_path.name} completed in {duration:.2f} seconds")
            logger.info(f"Detected language: {result['language']}")
            
            return {
                'text': cleaned_text,
                'language': result['language'],
                'duration': duration,
                'timestamp': timestamp,
                'file_size_mb': file_size_mb
            }
            
        except Exception as e:
            error_msg = f"Transcription failed for {audio_path.name}: {str(e)}"
            logger.error(error_msg)
            print(f"Error: {error_msg}")
            raise RuntimeError(error_msg)

    def _detect_excessive_repetition(self, text: str, max_repetitions: int = 3) -> bool:
        """
        Detect if text contains excessive repetition of phrases.
        
        Args:
            text: The text to analyze for repetition
            max_repetitions: Maximum allowed repetitions before considering it excessive
            
        Returns:
            True if excessive repetition is detected, False otherwise
        """
        words = text.split()
        if len(words) < 6:  # Skip very short texts
            return False
        
        # Check for repeated phrases at the beginning
        for phrase_length in range(2, 6):  # Check 2-5 word phrases
            if len(words) >= phrase_length * max_repetitions:
                first_phrase = ' '.join(words[:phrase_length])
                repetition_count = 1
                
                start_idx = phrase_length
                while start_idx + phrase_length <= len(words):
                    current_phrase = ' '.join(words[start_idx:start_idx + phrase_length])
                    if current_phrase == first_phrase:
                        repetition_count += 1
                        start_idx += phrase_length
                    else:
                        break
                
                if repetition_count > max_repetitions:
                    logger.debug(f"Excessive repetition detected: '{first_phrase}' repeated {repetition_count} times")
                    return True
        
        return False

    def _clean_repetitive_text(self, text: str, max_repetitions: int = 3) -> str:
        """
        Remove excessive repetition from text by keeping only the first occurrence of repeated phrases.
        
        Args:
            text: The text to clean
            max_repetitions: Maximum allowed repetitions
            
        Returns:
            Cleaned text with excessive repetitions removed
        """
        if not self._detect_excessive_repetition(text, max_repetitions):
            return text
        
        words = text.split()
        cleaned_words = []
        
        # Find and remove repetitive patterns
        i = 0
        while i < len(words):
            # Try different phrase lengths
            found_repetition = False
            
            for phrase_length in range(2, min(6, len(words) - i + 1)):
                if i + phrase_length > len(words):
                    continue
                    
                current_phrase = words[i:i + phrase_length]
                repetition_count = 1
                
                # Count consecutive repetitions
                check_idx = i + phrase_length
                while check_idx + phrase_length <= len(words):
                    next_phrase = words[check_idx:check_idx + phrase_length]
                    if next_phrase == current_phrase:
                        repetition_count += 1
                        check_idx += phrase_length
                    else:
                        break
                
                # If we found excessive repetition, keep only the first occurrence
                if repetition_count > max_repetitions:
                    cleaned_words.extend(current_phrase)
                    i = check_idx
                    found_repetition = True
                    logger.debug(f"Cleaned repetitive phrase: '{' '.join(current_phrase)}' (was repeated {repetition_count} times)")
                    break
            
            if not found_repetition:
                cleaned_words.append(words[i])
                i += 1
        
        return ' '.join(cleaned_words)

    def _clean_transcription_text(self, text: str) -> str:
        """
        Apply comprehensive cleaning to transcription text.
        
        Args:
            text: Raw transcription text
            
        Returns:
            Cleaned and formatted text
        """
        if not text or not text.strip():
            return text
        
        # Remove excessive repetition
        cleaned_text = self._clean_repetitive_text(text)
        
        # Additional cleaning: remove excessive whitespace
        cleaned_text = ' '.join(cleaned_text.split())
        
        # Remove common transcription artifacts
        artifacts_to_remove = [
            'Thank you.',  # Common ending artifact
            'Thanks for watching.',
            'Thank you for watching.',
        ]
        
        for artifact in artifacts_to_remove:
            if cleaned_text.strip().endswith(artifact):
                cleaned_text = cleaned_text.strip()[:-len(artifact)].strip()
        
        return cleaned_text

    def get_model_info(self) -> Dict[str, Any]:
        """Return information about the loaded model."""
        gpu_info = torch.cuda.get_device_properties(0) if torch.cuda.is_available() else None
        
        info = {
            'model_size': self.model_size,
            'device': self.device,
            'cuda_available': torch.cuda.is_available(),
            'cuda_device': torch.cuda.get_device_name(0) if torch.cuda.is_available() else None,
            'gpu_memory_gb': f"{gpu_info.total_memory / 1024**3:.1f}GB" if gpu_info else None,
            'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        
        logger.info(f"Model info: {info}")
        return info