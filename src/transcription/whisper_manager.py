from pathlib import Path
from typing import Dict, Any
from faster_whisper import WhisperModel
import torch
import time
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class WhisperManager:
    def __init__(self, model_size: str = "large"):
        """Initialize Whisper manager with specified model size."""
        self.model_size = model_size
        self.model = None
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        logger.info(f"Initializing WhisperManager with {model_size} model on {self.device}")
        self.load_model()
        
    def load_model(self) -> None:
        """Load the Whisper model into memory."""
        try:
            start_time = time.time()
            print(f"Loading Whisper {self.model_size} model...")
            # Use faster-whisper model loading
            self.model = WhisperModel(self.model_size, device=self.device)
            load_time = time.time() - start_time
            print(f"Model loaded successfully on {self.device} (took {load_time:.2f} seconds)")
            logger.info(f"Model loaded successfully on {self.device} (took {load_time:.2f} seconds)")
        except Exception as e:
            error_msg = f"Failed to load Whisper model: {str(e)}"
            logger.error(error_msg)
            raise RuntimeError(error_msg)

    def transcribe_audio(self, audio_path: str | Path) -> Dict[str, Any]:
        """
        Transcribe a single MP3 audio file with enhanced repetition prevention.
        
        Uses optimized faster-whisper parameters to prevent repetitive transcription output:
        - condition_on_previous_text=False: Prevents context bleeding between segments
        - beam_size=1: Uses greedy decoding to reduce repetition likelihood
        - vad_filter=True: Voice Activity Detection for cleaner segment boundaries
        - temperature=0.0: Eliminates randomness for consistent output
        
        Includes post-processing to detect and clean any remaining repetition.
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
            print(f"Using optimized parameters: beam_size=1, condition_on_previous_text=False, vad_filter=True")
            logger.info(f"Starting transcription of: {audio_path.name}")
            
            # Get file size for logging
            file_size_mb = audio_path.stat().st_size / (1024 * 1024)
            print(f"File size: {file_size_mb:.2f} MB")
            
            # Perform transcription with faster-whisper compatible parameters for optimal repetition prevention
            segments, info = self.model.transcribe(
                str(audio_path),
                language='en',  # Force English language
                task='transcribe',  # Ensure we're in transcription mode
                temperature=0.0,  # Eliminate randomness for consistent output
                condition_on_previous_text=False,  # CRITICAL: prevents repetition between segments
                initial_prompt=None,  # Clear initial prompt to prevent bias
                beam_size=1,  # Reduces repetition likelihood by using greedy decoding
                vad_filter=True,  # Voice Activity Detection for cleaner segment boundaries
                vad_parameters=dict(
                    min_silence_duration_ms=500  # Customize silence detection for better segmentation
                )
            )
            
            # Convert segments to text (faster-whisper returns generator)
            raw_text = ' '.join([segment.text for segment in segments])
            
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
            print(f"Detected language: {info.language}")
            logger.info(f"Transcription of {audio_path.name} completed in {duration:.2f} seconds")
            logger.info(f"Detected language: {info.language}")
            
            return {
                'text': cleaned_text,
                'language': info.language,
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