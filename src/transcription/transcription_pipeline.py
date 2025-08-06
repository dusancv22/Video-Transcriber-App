from pathlib import Path
from typing import Dict, Any, Optional, Callable
import logging
import time
from datetime import datetime
from src.audio_processing.converter import AudioConverter
from src.transcription.whisper_manager import WhisperManager
from src.post_processing.text_processor import TextProcessor
from src.post_processing.combiner import TextCombiner

logger = logging.getLogger(__name__)

class TranscriptionPipeline:
    def __init__(self):
        """Initialize the transcription pipeline components."""
        logger.info("Initializing TranscriptionPipeline")
        print("\nInitializing transcription pipeline...")
        self.converter = AudioConverter()
        self.whisper_manager = WhisperManager(model_size="large")
        self.text_processor = TextProcessor()
        self.text_combiner = TextCombiner()
        print("Pipeline initialized successfully")
        
    def process_video(
        self, 
        video_path: str | Path,
        output_dir: Optional[Path] = None,
        progress_callback: Optional[Callable[[float, str], None]] = None
    ) -> Dict[str, Any]:
        """
        Process a video file through the complete pipeline with enhanced progress logging.
        
        Args:
            video_path: Path to the video file
            output_dir: Directory for transcription output (defaults to video location)
            progress_callback: Optional callback for progress updates
            
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
                
                result = self.whisper_manager.transcribe_audio(audio_file)
                raw_text = result['text']
                
                # Format each segment immediately after transcription
                print(f"  Formatting segment {idx} text...")
                formatted_text = self.text_processor.format_segment_text(raw_text)
                full_text.append(formatted_text)
                
                if not detected_language:
                    detected_language = result['language']
                    
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
            
            # Since segments are pre-formatted, only do final cleanup
            print("Applying final text cleanup...")
            processed_text = self.text_processor.format_text(combined_text)
            
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

    def get_pipeline_status(self) -> Dict[str, Any]:
        """Get comprehensive status information about the pipeline components."""
        status = {
            'whisper_info': self.whisper_manager.get_model_info(),
            'converter_available': True,
            'temp_dir': str(self.converter.output_dir),
            'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        
        logger.info(f"Pipeline status: {status}")
        return status