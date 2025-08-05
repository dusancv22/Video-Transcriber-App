import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.append(str(project_root))

from src.transcription.transcription_pipeline import TranscriptionPipeline
import time

def progress_callback(progress: float, status: str):
    """Simple progress callback to show pipeline progress"""
    print(f"Progress: {progress*100:.1f}% - {status}")

def test_pipeline():
    """Test the complete transcription pipeline"""
    
    # Initialize pipeline
    print("\nInitializing TranscriptionPipeline...")
    pipeline = TranscriptionPipeline()
    
    # Test file path - you can adjust this to your test video location
    test_file = Path("tests/test_transcription/test_files/test video - Copy.mp4")
    
    if not test_file.exists():
        print(f"\nError: Test file not found: {test_file}")
        return
    
    print(f"\nProcessing video file: {test_file}")
    print("File size:", test_file.stat().st_size / (1024*1024), "MB")
    
    start_time = time.time()
    
    # Process the video
    result = pipeline.process_video(
        video_path=test_file,
        progress_callback=progress_callback
    )
    
    process_time = time.time() - start_time
    
    # Print results
    print("\nProcessing completed!")
    print(f"Total time: {process_time:.2f} seconds")
    
    if result['success']:
        print("\nTranscription successful!")
        print(f"Detected language: {result['language']}")
        print(f"Transcript saved to: {result.get('transcript_path')}")
        print("\nFirst 200 characters of transcription:")
        print("-" * 50)
        print(result['text'][:200] + "...")
        print("-" * 50)
    else:
        print("\nTranscription failed!")
        print(f"Error: {result.get('error')}")

if __name__ == "__main__":
    test_pipeline()