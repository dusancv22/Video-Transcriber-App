from pathlib import Path
from typing import Dict, Any
import whisper
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
            self.model = whisper.load_model(self.model_size).to(self.device)
            load_time = time.time() - start_time
            print(f"Model loaded successfully on {self.device} (took {load_time:.2f} seconds)")
            logger.info(f"Model loaded successfully on {self.device} (took {load_time:.2f} seconds)")
        except Exception as e:
            error_msg = f"Failed to load Whisper model: {str(e)}"
            logger.error(error_msg)
            raise RuntimeError(error_msg)

    def transcribe_audio(self, audio_path: str | Path) -> Dict[str, Any]:
        """
        Transcribe a single MP3 audio file with forced English language setting.
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
            
            # Perform transcription with forced English
            result = self.model.transcribe(
                str(audio_path),
                language='en',  # Force English language
                task='transcribe',  # Ensure we're in transcription mode
                fp16=False  # Use FP32 for better accuracy
            )
            
            # Calculate duration and log completion
            duration = time.time() - start_time
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            print(f"Transcription completed in {duration:.2f} seconds")
            print(f"Detected language: {result['language']}")
            logger.info(f"Transcription of {audio_path.name} completed in {duration:.2f} seconds")
            logger.info(f"Detected language: {result['language']}")
            
            return {
                'text': result['text'],
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