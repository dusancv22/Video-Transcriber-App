import sys
from pathlib import Path

# Add the project root directory to Python path
project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.append(str(project_root))

from src.transcription.whisper_manager import WhisperManager
import time

def test_basic_transcription():
    """Test basic MP3 transcription functionality"""
    
    # Initialize the manager
    print("\nInitializing WhisperManager...")
    manager = WhisperManager(model_size="large")
    
    # Test file path
    test_file = Path("tests/test_transcription/test_files/test.mp3")
    
    if not test_file.exists():
        print(f"\nError: Test file not found: {test_file}")
        print(f"Please place a test MP3 file at: {test_file}")
        return
    
    # Print model information
    print("\nModel Information:")
    model_info = manager.get_model_info()
    for key, value in model_info.items():
        print(f"{key}: {value}")
    
    # Test transcription
    print(f"\nTranscribing test file: {test_file}")
    start_time = time.time()
    
    try:
        result = manager.transcribe_audio(test_file)
        transcribe_time = time.time() - start_time
        
        # Print results
        print(f"\nTranscription completed in {transcribe_time:.2f} seconds")
        print(f"Detected language: {result['language']}")
        
        print("\nTranscription result:")
        print("-" * 50)
        print(result['text'])
        print("-" * 50)
            
    except Exception as e:
        print(f"\nError during transcription: {str(e)}")

if __name__ == "__main__":
    test_basic_transcription()