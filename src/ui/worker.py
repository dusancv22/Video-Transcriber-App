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
                 subtitle_formats=None, max_chars_per_line=42, translation_settings=None,
                 save_to_source=False):
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
        self.save_to_source = save_to_source
        self.is_paused = False
        self._stop = False
        # Translation models are loaded lazily inside run() (worker thread) -
        # loading them here would block the GUI thread.
        self.translation_enabled = bool(self.translation_settings.get('enabled'))
        if self.translation_enabled:
            logger.info(
                f"Translation enabled: {self.translation_settings.get('source_lang')} "
                f"-> {self.translation_settings.get('target_lang')}"
            )

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

        # Clear any pause/cancel state left over from a previous run
        self.pipeline.reset_control_flags()

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

                    # Determine output directory for this file
                    if self.save_to_source:
                        file_output_dir = next_item.file_path.parent
                    else:
                        file_output_dir = self.output_dir

                    # Process the video file with or without subtitles
                    if self.subtitle_formats:
                        # Use subtitle-aware processing
                        result = self.pipeline.process_video_with_subtitles(
                            video_path=next_item.file_path,
                            output_dir=file_output_dir,
                            progress_callback=progress_callback,
                            language=self.language_code,
                            subtitle_formats=self.subtitle_formats,
                            max_chars_per_line=self.max_chars_per_line
                        )
                    else:
                        # Use standard processing
                        result = self.pipeline.process_video(
                            video_path=next_item.file_path,
                            output_dir=file_output_dir,
                            progress_callback=progress_callback,
                            language=self.language_code
                        )

                    # Calculate processing time
                    processing_time = time.time() - start_time

                    # User cancelled mid-file (stop requested): exit the loop
                    # without reporting the file as failed.
                    if result.get('cancelled'):
                        logger.info("Processing cancelled by user - stopping worker")
                        print("Processing cancelled by user")
                        break

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
                        if self.translation_enabled:
                            translated_files = self._translate_subtitle_files(result['subtitle_files'])
                            if translated_files:
                                completion_info['translated_subtitle_files'] = translated_files
                                print(f"Translation complete: {len(translated_files)} subtitle(s) translated")
                                self.progress_updated.emit(1.0, "Processing complete with translation")
                            else:
                                self.progress_updated.emit(1.0, "Processing complete (translation failed)")
                        else:
                            self.progress_updated.emit(1.0, "Processing complete with subtitles")

                    # Emit completion signal AFTER translation (if any) is done
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
                    logger.error(f"Error processing {next_item.file_path.name}: {e}", exc_info=True)
                    print(f"ERROR: Failed to process {next_item.file_path.name}: {e}")
                    self.error_occurred.emit(str(next_item.file_path), str(e))

        except Exception as e:
            logger.error(f"Critical error in worker thread: {e}")
            print(f"Critical error in worker thread: {e}")
            self.error_occurred.emit("Worker Thread", str(e))
        
        finally:
            # Clean up resources
            self._cleanup()

    def _translate_subtitle_files(self, subtitle_files: dict) -> dict:
        """Translate generated subtitle files (runs in the worker thread).

        One translator instance is created per file batch and reused across
        formats, so the translation model is loaded only once instead of once
        per format.

        Args:
            subtitle_files: Mapping of format -> subtitle file path (or None)

        Returns:
            Mapping of format -> translated file path for successful translations
        """
        translated_files = {}
        translator = None

        try:
            print(f"Translating subtitles to {self.translation_settings.get('target_lang')}...")

            for format_type, subtitle_path in subtitle_files.items():
                if not subtitle_path or not Path(subtitle_path).exists():
                    logger.warning(f"Skipping translation for {format_type}: file missing")
                    continue

                try:
                    self.progress_updated.emit(0.96, f"Translating {format_type.upper()} subtitles...")

                    # Lazily create ONE translator for this file, reused across
                    # formats (previously the model was reloaded per format)
                    if translator is None:
                        from src.translation.subtitle_translator import SubtitleTranslator
                        translator = SubtitleTranslator(
                            source_lang=self.translation_settings.get('source_lang', 'auto'),
                            target_lang=self.translation_settings.get('target_lang', 'en')
                        )

                    translated_path = translator.translate_subtitle_file(
                        subtitle_path=Path(subtitle_path),
                        preserve_original=True
                    )
                    translated_files[format_type] = str(translated_path)
                    print(f"  Translated {format_type}: {translated_path.name}")
                except Exception as e:
                    logger.error(f"Failed to translate {format_type} subtitle: {e}", exc_info=True)
                    print(f"  Failed to translate {format_type}: {e}")
        except Exception as e:
            logger.error(f"Translation failed: {e}", exc_info=True)
            print(f"Translation failed: {e}")
        finally:
            if translator is not None:
                translator.cleanup()

        return translated_files

    def pause(self):
        """Pause processing - takes effect mid-file (between transcription segments)."""
        if not self.is_paused:
            self.is_paused = True
            self.pipeline.set_paused(True)
            logger.info("Worker paused")
            print("Pausing transcription...")

    def resume(self):
        """Resume processing."""
        if self.is_paused:
            self.is_paused = False
            self.pipeline.set_paused(False)
            logger.info("Worker resumed")
            print("Resuming transcription...")

    def stop(self):
        """Stop processing gracefully.

        Cancels the in-progress transcription (takes effect between
        transcription segments, typically within a second or two) rather than
        only stopping between files.
        """
        logger.info("Stopping worker")
        print("Stopping transcription worker...")
        self._stop = True
        self.is_paused = False  # Ensure we're not stuck in pause
        self.pipeline.request_cancel()

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