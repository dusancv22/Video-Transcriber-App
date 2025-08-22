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

    def __init__(self, pipeline, queue_manager, output_dir, language_code=None, 
                 subtitle_formats=None, max_chars_per_line=42, translation_settings=None):
        """Initialize the worker thread.
        
        Args:
            pipeline: The transcription pipeline instance
            queue_manager: The queue manager for handling files
            output_dir: Directory for output files
            language_code: Optional language code for transcription (e.g., 'en', 'es')
            subtitle_formats: List of subtitle formats to generate (e.g., ['srt', 'vtt'])
            max_chars_per_line: Maximum characters per subtitle line
            translation_settings: Dictionary with translation settings (enabled, source_lang, target_lang)
        """
        super().__init__()
        self.pipeline = pipeline
        self.queue_manager = queue_manager
        self.output_dir = output_dir
        self.language_code = language_code
        self.subtitle_formats = subtitle_formats or []
        self.max_chars_per_line = max_chars_per_line
        self.translation_settings = translation_settings or {'enabled': False}
        self.is_paused = False
        self._stop = False
        self.subtitle_translator = None
        
        # Initialize translator if translation is enabled
        if self.translation_settings.get('enabled'):
            try:
                from src.translation.subtitle_translator import SubtitleTranslator
                self.subtitle_translator = SubtitleTranslator(
                    source_lang=self.translation_settings.get('source_lang', 'auto'),
                    target_lang=self.translation_settings.get('target_lang', 'en')
                )
                logger.info(f"Translation enabled: {self.translation_settings.get('source_lang')} -> {self.translation_settings.get('target_lang')}")
                print(f"Translation enabled: {self.translation_settings.get('source_lang')} -> {self.translation_settings.get('target_lang')}")
            except Exception as e:
                logger.error(f"Failed to initialize translator: {e}")
                print(f"Warning: Failed to initialize translator: {e}")
                self.subtitle_translator = None
        
        logger.info(f"TranscriptionWorker initialized with language: {language_code or 'auto-detect'}")
        if self.subtitle_formats:
            logger.info(f"Subtitle generation enabled: {', '.join(self.subtitle_formats)}")
            print(f"Transcription worker initialized (Language: {language_code or 'auto-detect'}, Subtitles: {', '.join(self.subtitle_formats)})")
        else:
            print(f"Transcription worker initialized (Language: {language_code or 'auto-detect'})")

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

                    # Process the video file with or without subtitles
                    if self.subtitle_formats:
                        # Use subtitle-aware processing
                        result = self.pipeline.process_video_with_subtitles(
                            video_path=next_item.file_path,
                            output_dir=self.output_dir,
                            progress_callback=progress_callback,
                            language=self.language_code,
                            subtitle_formats=self.subtitle_formats,
                            max_chars_per_line=self.max_chars_per_line
                        )
                    else:
                        # Use standard processing
                        result = self.pipeline.process_video(
                            video_path=next_item.file_path,
                            output_dir=self.output_dir,
                            progress_callback=progress_callback,
                            language=self.language_code
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
                    
                    # Add subtitle file info if generated
                    if result.get('subtitle_files'):
                        completion_info['subtitle_files'] = result['subtitle_files']
                        completion_info['subtitle_segments'] = result.get('subtitle_segments', 0)
                        
                        # Translate subtitles if enabled
                        if self.subtitle_translator and result.get('subtitle_files'):
                            try:
                                print(f"Translating subtitles to {self.translation_settings.get('target_lang')}...")
                                print(f"DEBUG: subtitle_files = {result['subtitle_files']}")
                                print(f"DEBUG: subtitle_translator exists = {self.subtitle_translator is not None}")
                                translated_files = {}
                                
                                for format_type, subtitle_path in result['subtitle_files'].items():
                                    print(f"DEBUG: Processing format_type={format_type}, subtitle_path={subtitle_path}")
                                    # Convert Path object to string if needed
                                    path_exists = False
                                    if subtitle_path:
                                        subtitle_path = str(subtitle_path) if not isinstance(subtitle_path, str) else subtitle_path
                                        print(f"DEBUG: Checking subtitle file: {subtitle_path}")
                                        try:
                                            path_obj = Path(subtitle_path)
                                            print(f"DEBUG: Created Path object: {path_obj}", flush=True)
                                            import sys
                                            sys.stdout.flush()
                                            path_exists = path_obj.exists()
                                            print(f"DEBUG: File exists = {path_exists}", flush=True)
                                        except Exception as e:
                                            print(f"DEBUG: Error checking if file exists: {e}")
                                            import traceback
                                            print(f"DEBUG: Path check traceback:\n{traceback.format_exc()}")
                                            path_exists = False
                                    else:
                                        print(f"DEBUG: subtitle_path is None or empty")
                                        continue
                                    
                                    print(f"DEBUG: About to check path_exists={path_exists} for translation", flush=True)
                                    if path_exists:
                                        try:
                                            print(f"DEBUG: Starting translation of {format_type} subtitle...", flush=True)
                                            # Translate the subtitle file
                                            translated_path = self.subtitle_translator.translate_subtitle_file(
                                                subtitle_path=Path(subtitle_path),
                                                preserve_original=True
                                            )
                                            translated_files[format_type] = str(translated_path)
                                            print(f"  Translated {format_type}: {translated_path.name}")
                                        except Exception as e:
                                            import traceback
                                            logger.error(f"Failed to translate {format_type} subtitle: {e}")
                                            print(f"  Failed to translate {format_type}: {e}")
                                            print(f"DEBUG: Full traceback:\n{traceback.format_exc()}")
                                    else:
                                        print(f"DEBUG: Skipping translation - file doesn't exist or path is None")
                                
                                if translated_files:
                                    completion_info['translated_subtitle_files'] = translated_files
                                    print(f"Translation complete: {len(translated_files)} subtitle(s) translated")
                                else:
                                    print(f"DEBUG: No files were translated")
                                    
                            except Exception as e:
                                import traceback
                                logger.error(f"Translation failed: {e}")
                                print(f"Translation failed: {e}")
                                print(f"DEBUG: Outer exception traceback:\n{traceback.format_exc()}")
                        else:
                            print(f"DEBUG: Translation skipped - translator={self.subtitle_translator is not None}, has_files={result.get('subtitle_files') is not None}")

                    # Emit completion signal
                    self.file_completed.emit(completion_info)

                    # Log completion status
                    if result['success']:
                        success_msg = f"Successfully processed {next_item.file_path.name} in {processing_time:.2f} seconds"
                        if result.get('subtitle_files'):
                            subtitle_count = len([f for f in result['subtitle_files'].values() if f])
                            success_msg += f" (Generated {subtitle_count} subtitle file{'s' if subtitle_count != 1 else ''})"
                        print(success_msg)
                        logger.info(success_msg)
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