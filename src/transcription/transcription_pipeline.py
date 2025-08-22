from pathlib import Path
from typing import Dict, Any, Optional, Callable, List
import logging
import time
from datetime import datetime
from src.audio_processing.converter import AudioConverter

# Try to import WhisperManager (standard whisper)
try:
    from src.transcription.whisper_manager import WhisperManager
    STANDARD_WHISPER_AVAILABLE = True
except ImportError:
    WhisperManager = None
    STANDARD_WHISPER_AVAILABLE = False

# Import EnhancedWhisperManager (faster-whisper)
from src.transcription.enhanced_whisper_manager import EnhancedWhisperManager
from src.post_processing.text_processor import TextProcessor
from src.post_processing.advanced_text_processor import AdvancedTextProcessor
from src.post_processing.combiner import TextCombiner
from src.subtitles.subtitle_generator import SubtitleGenerator

logger = logging.getLogger(__name__)

class TranscriptionPipeline:
    def __init__(
        self, 
        use_advanced_processing: bool = True, 
        model_size: str = "large", 
        model_path: Optional[str] = None,
        use_vad_enhancement: bool = True,  # Enable VAD for accurate subtitle timing
        use_faster_whisper: bool = False  # Use faster-whisper for word-level timestamps
    ):
        """Initialize the transcription pipeline components.
        
        Args:
            use_advanced_processing: Whether to use advanced text processing (filler removal, etc.)
            model_size: Size of the Whisper model to use
            model_path: Optional path to a pre-downloaded model file
            use_vad_enhancement: Whether to use VAD for accurate subtitle timing
            use_faster_whisper: Whether to use faster-whisper (works on Windows with word timestamps)
        """
        logger.info(f"Initializing TranscriptionPipeline with model_size={model_size}, VAD={use_vad_enhancement}, faster_whisper={use_faster_whisper}")
        print("\nInitializing transcription pipeline...")
        self.converter = AudioConverter()
        
        # Choose which whisper implementation to use
        if use_faster_whisper:
            # Use faster-whisper for word-level timestamps (works on Windows!)
            try:
                logger.info("Initializing Enhanced Whisper Manager with faster-whisper")
                # For faster-whisper, map model sizes appropriately
                # If there's a .pt model path, ignore it for faster-whisper
                if model_path and model_path.endswith('.pt'):
                    logger.info("Ignoring .pt model file for faster-whisper, will download appropriate model")
                    model_path = None  # Don't pass .pt files to faster-whisper
                
                # Map model sizes for faster-whisper
                if model_size == "large":
                    faster_model_size = "large-v3"  # Use latest large model
                else:
                    faster_model_size = model_size
                    
                self.whisper_manager = EnhancedWhisperManager(model_size=faster_model_size, model_path=model_path)
                self.use_vad = use_vad_enhancement
                self.use_faster_whisper = True
                print("faster-whisper enabled for word-level timestamps (works on Windows!)")
                logger.info("faster-whisper initialized successfully")
            except Exception as e:
                logger.warning(f"Failed to initialize faster-whisper: {e}", exc_info=True)
                print(f"Warning: faster-whisper initialization failed ({e})")
                
                # Fall back to standard Whisper if available
                if STANDARD_WHISPER_AVAILABLE:
                    print("Falling back to standard Whisper")
                    self.whisper_manager = WhisperManager(model_size=model_size, model_path=model_path)
                    self.use_vad = False
                    self.use_faster_whisper = False
                else:
                    raise RuntimeError(f"faster-whisper failed and standard Whisper not available: {e}")
        elif use_vad_enhancement:
            # Try to use enhanced manager with VAD (requires faster-whisper now)
            try:
                logger.info("Initializing Enhanced Whisper Manager with VAD")
                # For VAD, we need to use faster-whisper
                faster_model_size = "large-v2" if model_size == "large" else model_size
                self.whisper_manager = EnhancedWhisperManager(model_size=faster_model_size, model_path=model_path)
                self.use_vad = True
                self.use_faster_whisper = True  # VAD requires faster-whisper
                print("VAD-enhanced transcription enabled (using faster-whisper)")
                logger.info("VAD enhancement initialized successfully")
            except Exception as e:
                logger.warning(f"Failed to initialize VAD enhancement: {e}", exc_info=True)
                print(f"Warning: VAD initialization failed ({e})")
                
                # Fall back to standard Whisper if available
                if STANDARD_WHISPER_AVAILABLE:
                    print("Falling back to standard Whisper")
                    self.whisper_manager = WhisperManager(model_size=model_size, model_path=model_path)
                    self.use_vad = False
                    self.use_faster_whisper = False
                else:
                    raise RuntimeError("Neither faster-whisper nor standard Whisper available")
        else:
            # Try standard Whisper first
            if STANDARD_WHISPER_AVAILABLE:
                logger.info("Using standard Whisper Manager")
                self.whisper_manager = WhisperManager(model_size=model_size, model_path=model_path)
                self.use_vad = False
                self.use_faster_whisper = False
            else:
                # Fall back to faster-whisper without VAD
                logger.info("Standard Whisper not available, using faster-whisper")
                faster_model_size = "large-v2" if model_size == "large" else model_size
                self.whisper_manager = EnhancedWhisperManager(model_size=faster_model_size, model_path=model_path)
                self.use_vad = False
                self.use_faster_whisper = True
                print("Using faster-whisper (standard Whisper not installed)")
        
        self.text_processor = TextProcessor()
        self.advanced_processor = AdvancedTextProcessor(remove_fillers=True, aggressive_cleaning=True)
        self.text_combiner = TextCombiner()
        # Initialize subtitle generator with word-level optimization enabled by default
        self.subtitle_generator = SubtitleGenerator(
            use_word_level_optimization=True,
            transition_delay=0.25  # Increased to 250ms for better sync with speech transitions
        )
        self.use_advanced_processing = use_advanced_processing
        print(f"Pipeline initialized successfully (Advanced processing: {'Enabled' if use_advanced_processing else 'Disabled'})")
        
    def process_video(
        self, 
        video_path: str | Path,
        output_dir: Optional[Path] = None,
        progress_callback: Optional[Callable[[float, str], None]] = None,
        language: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Process a video file through the complete pipeline with enhanced progress logging.
        
        Args:
            video_path: Path to the video file
            output_dir: Directory for transcription output (defaults to video location)
            progress_callback: Optional callback for progress updates
            language: Optional language code for transcription (e.g., 'en', 'es'). If None, auto-detect.
            
        Returns:
            Dictionary containing process results and timing information
        """
        video_path = Path(video_path)
        start_time = time.time()
        
        if output_dir is None:
            output_dir = video_path.parent / "transcripts"
            output_dir.mkdir(exist_ok=True)
            
        print(f"\nStarting processing of: {video_path.name}")
        print(f"Output directory: {output_dir}")
        logger.info(f"Starting processing of: {video_path.name}")
        
        try:
            # Step 1: Convert video to audio
            if progress_callback:
                progress_callback(0.0, "Starting video conversion")
            
            print("\nStep 1/4: Converting video to audio...")
            conversion_start = time.time()
            success, audio_files = self.converter.convert_video_to_audio(
                str(video_path),
                lambda p: progress_callback(p * 0.4, "Converting video to audio") if progress_callback else None
            )
            
            if not success or not audio_files:
                raise RuntimeError("Failed to convert video to audio")
                
            conversion_time = time.time() - conversion_start
            print(f"Conversion completed in {conversion_time:.2f} seconds")
            print(f"Generated {len(audio_files)} audio segments")
            logger.info(f"Audio conversion completed in {conversion_time:.2f} seconds")
            
            # Step 2: Transcribe audio files
            if progress_callback:
                progress_callback(0.4, "Starting transcription")
                
            print("\nStep 2/4: Transcribing audio...")
            transcription_start = time.time()
            full_text = []
            detected_language = None
            
            total_segments = len(audio_files)
            for idx, audio_file in enumerate(audio_files, 1):
                print(f"\nProcessing segment {idx}/{total_segments}")
                progress_base = 0.4
                progress_per_segment = 0.5 / total_segments
                current_progress = progress_base + (progress_per_segment * idx)
                
                if progress_callback:
                    progress_callback(
                        current_progress,
                        f"Transcribing segment {idx}/{total_segments}"
                    )
                
                try:
                    print(f"DEBUG: Attempting to transcribe: {audio_file}")
                    # Use transcribe_audio_with_timestamps to get VAD-enhanced transcription
                    result = self.whisper_manager.transcribe_audio_with_timestamps(audio_file, language=language)
                    print(f"DEBUG: Transcription successful for segment {idx}")
                    full_text.append(result['text'])
                    if not detected_language:
                        detected_language = result['language']
                except Exception as e:
                    print(f"ERROR: Failed to transcribe segment {idx}: {e}")
                    logger.error(f"Failed to transcribe segment {idx}: {e}")
                    raise
                    
            transcription_time = time.time() - transcription_start
            print(f"\nTranscription completed in {transcription_time:.2f} seconds")
            logger.info(f"Transcription completed in {transcription_time:.2f} seconds")
            
            # Step 3: Post-processing
            if progress_callback:
                progress_callback(0.9, "Post-processing transcription")
                
            print("\nStep 3/4: Post-processing transcription...")
            processing_start = time.time()
            
            # Get segment metadata for intelligent text combination
            segment_metadata = self.converter.get_last_split_metadata()
            
            # Use intelligent text combination if we have multiple segments
            if len(full_text) > 1:
                print("Applying intelligent text combination with overlap removal...")
                combined_text = self.text_combiner.combine_overlapping_segments(
                    full_text, 
                    segment_metadata,
                    overlap_seconds=2.5
                )
            else:
                print("Single segment - no deduplication needed")
                combined_text = full_text[0] if full_text else ""
            
            # Apply text processing - basic first, then advanced if enabled
            processed_text = self.text_processor.process_transcript(combined_text)
            
            if self.use_advanced_processing:
                print("Applying advanced post-processing (filler removal, smart formatting)...")
                processed_text = self.advanced_processor.process_transcript(processed_text)
            
            processing_time = time.time() - processing_start
            print(f"Post-processing completed in {processing_time:.2f} seconds")
            logger.info(f"Post-processing completed in {processing_time:.2f} seconds")
            
            # Step 4: Save and cleanup
            if progress_callback:
                progress_callback(0.95, "Saving transcript")
                
            print("\nStep 4/4: Saving transcript and cleaning up...")
            output_file = output_dir / f"{video_path.stem}_transcript.txt"
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(processed_text)
                
            # Clean up temporary files
            self.converter.cleanup_temp_files()
            
            # Calculate total time
            total_time = time.time() - start_time
            
            # Final progress update
            if progress_callback:
                progress_callback(1.0, "Processing complete")
                
            print(f"\nProcessing completed successfully!")
            print(f"Total processing time: {total_time:.2f} seconds")
            print(f"Output saved to: {output_file}")
            logger.info(f"Processing completed successfully in {total_time:.2f} seconds")
            
            return {
                'success': True,
                'text': processed_text,
                'language': detected_language,
                'video_name': video_path.name,
                'transcript_path': output_file,
                'processing_times': {
                    'conversion': conversion_time,
                    'transcription': transcription_time,
                    'processing': processing_time,
                    'total': total_time
                },
                'deduplication_stats': self.text_combiner.get_deduplication_stats(),
                'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            
        except Exception as e:
            error_msg = f"Error processing video: {e}"
            logger.error(error_msg)
            print(f"\nError: {error_msg}")
            # Attempt cleanup even if processing failed
            self.converter.cleanup_temp_files()
            return {
                'success': False,
                'error': str(e),
                'video_name': video_path.name,
                'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }

    def process_video_with_subtitles(
        self, 
        video_path: str | Path,
        output_dir: Optional[Path] = None,
        progress_callback: Optional[Callable[[float, str], None]] = None,
        language: Optional[str] = None,
        subtitle_formats: Optional[List[str]] = None,
        max_chars_per_line: int = 42
    ) -> Dict[str, Any]:
        """
        Process a video file with subtitle generation support.
        
        This method extends the standard process_video to also generate subtitle files
        in various formats while maintaining all existing transcription functionality.
        
        Args:
            video_path: Path to the video file
            output_dir: Directory for transcription and subtitle output
            progress_callback: Optional callback for progress updates
            language: Optional language code for transcription
            subtitle_formats: List of subtitle formats to generate (e.g., ['srt', 'vtt'])
            max_chars_per_line: Maximum characters per subtitle line
            
        Returns:
            Dictionary containing process results, timing, and subtitle file paths
        """
        video_path = Path(video_path)
        start_time = time.time()
        
        if output_dir is None:
            output_dir = video_path.parent / "transcripts"
            output_dir.mkdir(exist_ok=True)
        
        # Default to SRT if no formats specified
        if subtitle_formats is None:
            subtitle_formats = ['srt']
        
        print(f"\nStarting processing with subtitles of: {video_path.name}")
        print(f"Output directory: {output_dir}")
        print(f"Subtitle formats: {', '.join(subtitle_formats)}")
        logger.info(f"Starting processing with subtitles of: {video_path.name}")
        
        try:
            # Step 1: Convert video to audio
            if progress_callback:
                progress_callback(0.0, "Starting video conversion")
            
            print("\nStep 1/5: Converting video to audio...")
            conversion_start = time.time()
            success, audio_files = self.converter.convert_video_to_audio(
                str(video_path),
                lambda p: progress_callback(p * 0.3, "Converting video to audio") if progress_callback else None
            )
            
            if not success or not audio_files:
                raise RuntimeError("Failed to convert video to audio")
            
            conversion_time = time.time() - conversion_start
            print(f"Conversion completed in {conversion_time:.2f} seconds")
            print(f"Generated {len(audio_files)} audio segments")
            logger.info(f"Audio conversion completed in {conversion_time:.2f} seconds")
            
            # Step 2: Transcribe audio files with timestamps
            if progress_callback:
                progress_callback(0.3, "Starting transcription with timestamps")
            
            print("\nStep 2/5: Transcribing audio with timestamps...")
            transcription_start = time.time()
            full_text = []
            all_segments = []
            detected_language = None
            current_time_offset = 0.0
            
            total_segments = len(audio_files)
            segment_metadata = self.converter.get_last_split_metadata()
            
            for idx, audio_file in enumerate(audio_files, 1):
                print(f"\nProcessing segment {idx}/{total_segments}")
                progress_base = 0.3
                progress_per_segment = 0.4 / total_segments
                current_progress = progress_base + (progress_per_segment * idx)
                
                if progress_callback:
                    progress_callback(
                        current_progress,
                        f"Transcribing segment {idx}/{total_segments} with timestamps"
                    )
                
                try:
                    # Use the new method that returns timestamps
                    result = self.whisper_manager.transcribe_audio_with_timestamps(audio_file, language=language)
                    
                    # Collect full text
                    full_text.append(result['text'])
                    
                    # Adjust timestamps for multi-segment files
                    if result.get('segments'):
                        for segment in result['segments']:
                            adjusted_segment = {
                                'start': segment['start'] + current_time_offset,
                                'end': segment['end'] + current_time_offset,
                                'text': segment['text']
                            }
                            
                            # CRITICAL: Preserve word-level timestamps if they exist!
                            if 'words' in segment and segment['words']:
                                # Adjust word timestamps too
                                adjusted_words = []
                                for word in segment['words']:
                                    adjusted_words.append({
                                        'word': word['word'],
                                        'start': word['start'] + current_time_offset,
                                        'end': word['end'] + current_time_offset,
                                        'probability': word.get('probability', 1.0)
                                    })
                                adjusted_segment['words'] = adjusted_words
                            
                            all_segments.append(adjusted_segment)
                    
                    # Update time offset for next segment
                    if segment_metadata and idx <= len(segment_metadata):
                        # Use actual duration from metadata if available
                        segment_duration = segment_metadata[idx - 1].get('duration', 0)
                        if segment_duration > 0:
                            current_time_offset += segment_duration
                        elif result.get('segments'):
                            # Fallback to last segment end time
                            current_time_offset += result['segments'][-1]['end']
                    
                    if not detected_language:
                        detected_language = result['language']
                        
                except Exception as e:
                    print(f"ERROR: Failed to transcribe segment {idx}: {e}")
                    logger.error(f"Failed to transcribe segment {idx}: {e}")
                    raise
            
            transcription_time = time.time() - transcription_start
            print(f"\nTranscription completed in {transcription_time:.2f} seconds")
            print(f"Generated {len(all_segments)} subtitle segments")
            logger.info(f"Transcription completed in {transcription_time:.2f} seconds")
            
            # Step 3: Post-processing
            if progress_callback:
                progress_callback(0.7, "Post-processing transcription")
            
            print("\nStep 3/5: Post-processing transcription...")
            processing_start = time.time()
            
            # Use intelligent text combination if we have multiple segments
            if len(full_text) > 1:
                print("Applying intelligent text combination with overlap removal...")
                combined_text = self.text_combiner.combine_overlapping_segments(
                    full_text, 
                    segment_metadata,
                    overlap_seconds=2.5
                )
            else:
                print("Single segment - no deduplication needed")
                combined_text = full_text[0] if full_text else ""
            
            # Apply text processing
            processed_text = self.text_processor.process_transcript(combined_text)
            
            if self.use_advanced_processing:
                print("Applying advanced post-processing...")
                processed_text = self.advanced_processor.process_transcript(processed_text)
            
            processing_time = time.time() - processing_start
            print(f"Post-processing completed in {processing_time:.2f} seconds")
            
            # Step 4: Generate subtitles
            if progress_callback:
                progress_callback(0.85, "Generating subtitle files")
            
            print("\nStep 4/5: Generating subtitle files...")
            
            # DEBUG: Check if we have word timestamps before subtitle generation
            logger.info(f"Checking word timestamps before subtitle generation...")
            word_count = 0
            segments_with_words = 0
            for idx, seg in enumerate(all_segments[:5]):  # Check first 5 segments
                if 'words' in seg and seg['words']:
                    segments_with_words += 1
                    word_count += len(seg['words'])
                    logger.info(f"  Segment {idx+1} has {len(seg['words'])} words: '{seg['text'][:50]}...'")
                    # Log first and last word timing
                    if seg['words']:
                        first_word = seg['words'][0]
                        last_word = seg['words'][-1]
                        logger.info(f"    First word: '{first_word.get('word', '')}' at {first_word.get('start', 0):.2f}s")
                        logger.info(f"    Last word: '{last_word.get('word', '')}' at {last_word.get('end', 0):.2f}s")
                        logger.info(f"    Segment timing: {seg['start']:.2f}s - {seg['end']:.2f}s")
                else:
                    logger.warning(f"  Segment {idx+1} has NO WORDS: '{seg.get('text', '')[:50]}...'")
            
            logger.info(f"Word timestamp summary: {segments_with_words}/{min(5, len(all_segments))} segments have word timestamps")
            logger.info(f"Total words found: {word_count}")
            
            subtitle_start = time.time()
            
            # Configure subtitle generator
            self.subtitle_generator.max_chars_per_line = max_chars_per_line
            
            # Generate subtitles in requested formats
            subtitle_base_path = output_dir / f"{video_path.stem}_subtitle"
            subtitle_files = self.subtitle_generator.generate_multiple_formats(
                all_segments,
                subtitle_base_path,
                subtitle_formats
            )
            
            subtitle_time = time.time() - subtitle_start
            print(f"Subtitle generation completed in {subtitle_time:.2f} seconds")
            
            # List generated subtitle files
            for format, file_path in subtitle_files.items():
                if file_path:
                    print(f"  - {format.upper()}: {file_path}")
            
            # Step 5: Save transcript and cleanup
            if progress_callback:
                progress_callback(0.95, "Saving transcript and cleaning up")
            
            print("\nStep 5/5: Saving transcript and cleaning up...")
            output_file = output_dir / f"{video_path.stem}_transcript.txt"
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(processed_text)
            
            # Clean up temporary files
            self.converter.cleanup_temp_files()
            
            # Calculate total time
            total_time = time.time() - start_time
            
            # Final progress update
            if progress_callback:
                progress_callback(1.0, "Processing complete with subtitles")
            
            print(f"\nProcessing completed successfully!")
            print(f"Total processing time: {total_time:.2f} seconds")
            print(f"Transcript saved to: {output_file}")
            logger.info(f"Processing with subtitles completed in {total_time:.2f} seconds")
            
            # Convert Path objects to strings in subtitle_files
            subtitle_files_str = {k: str(v) if v else None for k, v in subtitle_files.items()}
            
            return {
                'success': True,
                'text': processed_text,
                'language': detected_language,
                'video_name': video_path.name,
                'transcript_path': output_file,
                'subtitle_files': subtitle_files_str,
                'subtitle_segments': len(all_segments),
                'processing_times': {
                    'conversion': conversion_time,
                    'transcription': transcription_time,
                    'processing': processing_time,
                    'subtitles': subtitle_time,
                    'total': total_time
                },
                'deduplication_stats': self.text_combiner.get_deduplication_stats(),
                'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            
        except Exception as e:
            error_msg = f"Error processing video with subtitles: {e}"
            logger.error(error_msg)
            print(f"\nError: {error_msg}")
            # Attempt cleanup even if processing failed
            self.converter.cleanup_temp_files()
            return {
                'success': False,
                'error': str(e),
                'video_name': video_path.name,
                'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }

    def get_pipeline_status(self) -> Dict[str, Any]:
        """Get comprehensive status information about the pipeline components."""
        status = {
            'whisper_info': self.whisper_manager.get_model_info(),
            'converter_available': True,
            'temp_dir': str(self.converter.output_dir),
            'subtitle_formats_available': list(SubtitleGenerator.SUPPORTED_FORMATS.keys()),
            'subtitle_optimization': self.subtitle_generator.get_optimization_status(),
            'vad_enabled': self.use_vad,
            'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        
        logger.info(f"Pipeline status: {status}")
        return status
    
    def configure_subtitle_sync(
        self,
        use_word_level: bool = True,
        transition_delay: float = 0.15,
        pause_threshold: float = 0.3,
        min_pause_for_boundary: float = 0.2
    ):
        """Configure subtitle synchronization settings.
        
        Args:
            use_word_level: Enable word-level timestamp optimization
            transition_delay: Delay to add to transitions (seconds)
            pause_threshold: Minimum pause to consider as boundary
            min_pause_for_boundary: Minimum pause to create boundary
        """
        self.subtitle_generator.configure_word_optimization(
            enabled=use_word_level,
            transition_delay=transition_delay,
            pause_threshold=pause_threshold,
            min_pause_for_boundary=min_pause_for_boundary
        )
        logger.info(f"Subtitle sync configured: word_level={use_word_level}, delay={transition_delay}s")