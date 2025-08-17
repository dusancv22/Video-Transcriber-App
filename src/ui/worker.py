from PyQt6.QtCore import QThread, pyqtSignal
from pathlib import Path
import time
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class TranscriptionWorker(QThread):
    # Signal definitions
    progress_updated = pyqtSignal(float, str)
    file_completed = pyqtSignal(dict)
    all_completed = pyqtSignal()
    error_occurred = pyqtSignal(str, str)

    def __init__(self, pipeline, queue_manager, output_dir):
        """Initialize the worker thread."""
        super().__init__()
        self.pipeline = pipeline
        self.queue_manager = queue_manager
        self.output_dir = output_dir
        self.is_paused = False
        self._stop = False
        
        logger.info("TranscriptionWorker initialized")
        print("Transcription worker initialized")

    def run(self):
        """Main processing loop with enhanced progress reporting."""
        logger.info("Starting transcription worker process")
        print("\nStarting transcription process...")
        
        try:
            while not self._stop:
                if self.is_paused:
                    print("Processing paused...")
                    self.msleep(100)  # Reduce CPU usage while paused
                    continue

                next_item = self.queue_manager.get_next_file()
                if not next_item:
                    print("\nAll files processed")
                    logger.info("No more files to process")
                    self.all_completed.emit()
                    break

                try:
                    # Start processing current file
                    start_time = time.time()
                    print(f"\nProcessing: {next_item.file_path.name}")
                    logger.info(f"Starting processing of {next_item.file_path.name}")

                    def progress_callback(progress: float, status: str):
                        if not self.is_paused:
                            self.progress_updated.emit(progress, status)

                    # Process the video file
                    result = self.pipeline.process_video(
                        video_path=next_item.file_path,
                        output_dir=self.output_dir,
                        progress_callback=progress_callback
                    )

                    # Calculate processing time
                    processing_time = time.time() - start_time
                    
                    # Prepare completion info
                    completion_info = {
                        'file_path': str(next_item.file_path),
                        'success': result['success'],
                        'error': result.get('error'),
                        'processing_time': processing_time,
                        'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    }

                    # Emit completion signal
                    self.file_completed.emit(completion_info)

                    # Log completion status
                    if result['success']:
                        print(f"Successfully processed {next_item.file_path.name} in {processing_time:.2f} seconds")
                        logger.info(f"Successfully processed {next_item.file_path.name} in {processing_time:.2f} seconds")
                    else:
                        error_msg = result.get('error', 'Unknown error')
                        print(f"Failed to process {next_item.file_path.name}: {error_msg}")
                        logger.error(f"Failed to process {next_item.file_path.name}: {error_msg}")

                except Exception as e:
                    import traceback
                    error_details = traceback.format_exc()
                    logger.error(f"Error processing {next_item.file_path.name}: {e}")
                    logger.error(f"Full traceback:\n{error_details}")
                    print(f"ERROR: Failed to process {next_item.file_path.name}")
                    print(f"ERROR: {e}")
                    print(f"DEBUG: Full traceback:\n{error_details}")
                    self.error_occurred.emit(str(next_item.file_path), str(e))

        except Exception as e:
            logger.error(f"Critical error in worker thread: {e}")
            print(f"Critical error in worker thread: {e}")
            self.error_occurred.emit("Worker Thread", str(e))
        
        finally:
            # Clean up resources
            self._cleanup()

    def pause(self):
        """Pause processing."""
        if not self.is_paused:
            self.is_paused = True
            logger.info("Worker paused")
            print("Pausing transcription...")

    def resume(self):
        """Resume processing."""
        if self.is_paused:
            self.is_paused = False
            logger.info("Worker resumed")
            print("Resuming transcription...")

    def stop(self):
        """Stop processing gracefully."""
        logger.info("Stopping worker")
        print("Stopping transcription worker...")
        self._stop = True
        self.is_paused = False  # Ensure we're not stuck in pause

    def _cleanup(self):
        """Clean up resources before thread ends."""
        try:
            if self.pipeline:
                self.pipeline.converter.cleanup_temp_files()
            logger.info("Worker cleanup completed")
            print("Worker cleanup completed")
        except Exception as e:
            logger.error(f"Error during worker cleanup: {e}")
            print(f"Error during worker cleanup: {e}")

    def wait_with_timeout(self, timeout_ms: int = 5000) -> bool:
        """
        Wait for the thread to finish with timeout.
        
        Args:
            timeout_ms: Maximum time to wait in milliseconds
            
        Returns:
            bool: True if thread finished, False if timed out
        """
        print(f"Waiting for worker to finish (timeout: {timeout_ms}ms)...")
        return self.wait(timeout_ms)