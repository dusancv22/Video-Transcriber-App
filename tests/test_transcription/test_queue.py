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

def test_multiple_files():
    """Test processing multiple video files in sequence"""
    
    # Initialize pipeline
    print("\nInitializing TranscriptionPipeline...")
    pipeline = TranscriptionPipeline()
    
    # Test files
    test_files = [
        Path("tests/test_transcription/test_files/test video - Copy.mp4"),
        Path("tests/test_transcription/test_files/test2.mp4")  # Add a second test file
    ]
    
    # Output directory
    output_dir = Path("tests/test_transcription/test_files/output")
    output_dir.mkdir(exist_ok=True)
    
    # Process each file
    for i, video_file in enumerate(test_files, 1):
        if not video_file.exists():
            print(f"\nError: Test file not found: {video_file}")
            continue
            
        print(f"\nProcessing file {i}/{len(test_files)}: {video_file.name}")
        print("File size:", video_file.stat().st_size / (1024*1024), "MB")
        
        start_time = time.time()
        
        # Process the video
        result = pipeline.process_video(
            video_path=video_file,
            output_dir=output_dir,
            progress_callback=progress_callback
        )
        
        process_time = time.time() - start_time
        
        # Print results
        if result['success']:
            print(f"\nFile {i} transcription successful!")
            print(f"Processing time: {process_time:.2f} seconds")
            print(f"Detected language: {result['language']}")
            print(f"Transcript saved to: {result.get('transcript_path')}")
        else:
            print(f"\nFile {i} transcription failed!")
            print(f"Error: {result.get('error')}")

if __name__ == "__main__":
    test_multiple_files()