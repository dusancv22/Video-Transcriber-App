import pysubs2
from pathlib import Path
from typing import List, Dict, Optional, Tuple
import logging
import re
from src.post_processing.text_processor import TextProcessor
from src.subtitles.smart_timing_estimator import SmartTimingEstimator
from src.subtitles.word_based_subtitle_generator import WordBasedSubtitleGenerator

logger = logging.getLogger(__name__)

class SubtitleGenerator:
    """Generate subtitle files in various formats from transcription segments."""
    
    # Formats pysubs2 can actually write. TTML and SAMI were advertised here
    # previously but pysubs2 cannot save them - they failed silently.
    SUPPORTED_FORMATS = {
        'srt': 'SubRip',
        'vtt': 'WebVTT',
        'ass': 'Advanced SubStation Alpha',
        'ssa': 'SubStation Alpha'
    }
    
    def __init__(
        self, 
        max_chars_per_line: int = 42, 
        max_lines_per_subtitle: int = 2,
        use_word_level_optimization: bool = True,
        transition_delay: float = 0.15
    ):
        """Initialize subtitle generator with formatting preferences.
        
        Args:
            max_chars_per_line: Maximum characters per subtitle line
            max_lines_per_subtitle: Maximum lines per subtitle entry (standard is 2)
            use_word_level_optimization: Whether to use word-level timestamp optimization
            transition_delay: Default transition delay for better sync
        """
        self.max_chars_per_line = max_chars_per_line
        self.max_lines_per_subtitle = 2  # Force 2 lines max as per subtitle standards
        self.max_chars_per_subtitle = max_chars_per_line * 2  # Total chars for 2 lines
        self.use_word_level_optimization = use_word_level_optimization
        self.transition_delay = transition_delay

        # Initialize smart timing estimator for when word timestamps are unavailable
        self.smart_estimator = SmartTimingEstimator(
            avg_speech_rate_wpm=140,  # Spanish average
            reading_rate_wpm=160,
            two_line_extension=0.6
        )

        logger.info(f"SubtitleGenerator initialized with {max_chars_per_line} chars/line")
    
    def generate_subtitles(
        self, 
        segments: List[Dict],
        output_path: Path,
        format: str = 'srt',
        time_offset: float = 0.0,
        min_duration: float = 0.5,
        max_duration: float = 7.0,
        global_sync_offset: float = 0.0
    ) -> Path:
        """Generate subtitle file from segments with timestamps.
        
        This method now splits long segments into multiple subtitles while
        preserving accurate timing and avoiding text truncation.
        
        Args:
            segments: List of dictionaries with 'start', 'end', 'text' keys
            output_path: Base path for output file (without extension)
            format: Output format (srt, vtt, ass, etc.)
            time_offset: Global time offset in seconds (for synchronization)
            min_duration: Minimum subtitle duration in seconds
            max_duration: Maximum subtitle duration in seconds
            global_sync_offset: Manual sync adjustment in seconds (+ delays, - advances)
            
        Returns:
            Path to generated subtitle file
        """
        if format not in self.SUPPORTED_FORMATS:
            raise ValueError(f"Unsupported format: {format}. Supported: {list(self.SUPPORTED_FORMATS.keys())}")
        
        logger.info(f"Generating {format} subtitles with {len(segments)} segments")

        # Collapse hallucination loops in segment texts (walls of the same
        # word/phrase from non-speech audio). Word-level runs are collapsed
        # separately inside the word-based generator.
        segments = [
            dict(seg, text=TextProcessor.collapse_repetitions(seg['text']))
            if seg.get('text') else seg
            for seg in segments
        ]

        # First, merge orphan segments (like single word "pueblo.")
        logger.info("Checking for orphan segments to merge...")
        segments = self.smart_estimator.smart_segment_merge(segments)
        
        # Check if we have word timestamps. Scan ALL segments: early segments
        # (music, merged intros) often lack word data even when the rest of the
        # file has it, and sampling only the head silently degraded whole files
        # to heuristic timing.
        segments_with_words = sum(1 for seg in segments if seg.get('words'))
        has_word_timestamps = segments_with_words > 0
        logger.info(
            f"Word timestamps: {segments_with_words}/{len(segments)} segments "
            f"-> using {'word-based' if has_word_timestamps else 'estimated'} timing"
        )
        
        if has_word_timestamps:
            # Use the simple word-based generator that actually uses word timestamps!
            logger.info("Using word-based subtitle generator with actual word timestamps")
            word_generator = WordBasedSubtitleGenerator(
                max_chars_per_line=self.max_chars_per_line,
                max_words_per_subtitle=10,
                min_subtitle_duration=min_duration,
                max_subtitle_duration=max_duration
            )
            return word_generator.generate_from_segments(segments, output_path, format)
        else:
            # No word timestamps available - use smart estimation
            logger.warning("No word timestamps available - using smart timing estimation")
            segments = self.smart_estimator.fix_subtitle_timing_without_words(segments)
        
        # Log sync adjustment if applied
        if global_sync_offset != 0:
            logger.info(f"Applying global sync offset: {global_sync_offset:+.2f}s")
        
        # Create pysubs2 subtitle file
        subs = pysubs2.SSAFile()
        
        for segment in segments:
            # Apply both time offset and global sync adjustment
            start_time = segment['start'] + time_offset + global_sync_offset
            end_time = segment['end'] + time_offset + global_sync_offset
            segment_duration = end_time - start_time
            
            # Clean and prepare text
            text = segment['text'].strip()
            if not text:
                continue
            
            # Calculate minimum reading time based on text length
            # Average reading speed: 150-200 words per minute for subtitles
            word_count = len(text.split())
            min_reading_time = max(1.5, word_count * 0.4)  # ~150 WPM reading speed
            
            # Extend duration if needed for reading time
            if segment_duration < min_reading_time:
                logger.debug(f"Extending segment duration from {segment_duration:.2f}s to {min_reading_time:.2f}s for readability")
                end_time = start_time + min_reading_time
                segment_duration = min_reading_time
            
            # Split long text into multiple subtitles if needed
            subtitle_texts = self._split_text_for_subtitles(text)
            
            if len(subtitle_texts) == 1:
                # Single subtitle - use original timing
                # Enforce duration constraints
                if segment_duration < min_duration:
                    end_time = start_time + min_duration
                elif segment_duration > max_duration:
                    end_time = start_time + max_duration
                
                event = pysubs2.SSAEvent(
                    start=int(start_time * 1000),
                    end=int(end_time * 1000),
                    text=subtitle_texts[0]
                )
                subs.append(event)
            else:
                # Multiple subtitles needed - split time proportionally
                # Calculate time per subtitle based on reading speed
                time_per_subtitle = segment_duration / len(subtitle_texts)
                
                # Ensure each subtitle has reasonable duration
                time_per_subtitle = max(min_duration, min(time_per_subtitle, max_duration))
                
                for i, subtitle_text in enumerate(subtitle_texts):
                    sub_start = start_time + (i * time_per_subtitle)
                    sub_end = min(sub_start + time_per_subtitle, end_time)
                    
                    # Make sure we don't exceed the original segment end time
                    if i == len(subtitle_texts) - 1:
                        sub_end = end_time
                    
                    event = pysubs2.SSAEvent(
                        start=int(sub_start * 1000),
                        end=int(sub_end * 1000),
                        text=subtitle_text
                    )
                    subs.append(event)
        
        # Generate output filename with extension
        output_file = output_path.with_suffix(f'.{format}')
        
        # Save in requested format
        subs.save(str(output_file), encoding='utf-8-sig')
        logger.info(f"Saved subtitle file: {output_file}")
        
        return output_file
    
    def _split_text_for_subtitles(self, text: str) -> List[str]:
        """Split text into subtitle-sized chunks without truncation.
        
        If text fits in one subtitle (2 lines), return as-is.
        If text is too long, split into multiple subtitles.
        
        Args:
            text: Raw text to split
            
        Returns:
            List of formatted subtitle texts
        """
        # Clean up text
        text = re.sub(r'\s+', ' ', text.strip())
        
        # Calculate if text fits in one subtitle
        if len(text) <= self.max_chars_per_subtitle:
            # Text fits - format into 1 or 2 lines
            return [self._format_subtitle_text(text)]
        
        # Text too long - need to split into multiple subtitles
        words = text.split()
        subtitles = []
        current_subtitle_words = []
        current_length = 0
        
        for word in words:
            word_length = len(word)
            
            # Check if adding this word would exceed subtitle limit
            if current_length > 0 and current_length + word_length + 1 > self.max_chars_per_subtitle:
                # Create subtitle from current words
                subtitle_text = ' '.join(current_subtitle_words)
                subtitles.append(self._format_subtitle_text(subtitle_text))
                
                # Start new subtitle with this word
                current_subtitle_words = [word]
                current_length = word_length
            else:
                # Add word to current subtitle
                current_subtitle_words.append(word)
                current_length += word_length + (1 if current_length > 0 else 0)
        
        # Don't forget the last subtitle
        if current_subtitle_words:
            subtitle_text = ' '.join(current_subtitle_words)
            subtitles.append(self._format_subtitle_text(subtitle_text))
        
        return subtitles
    
    def _format_subtitle_text(self, text: str) -> str:
        """Format text for optimal subtitle display with line breaks.
        
        Takes text that fits in a subtitle and formats it into 1 or 2 lines.
        
        Args:
            text: Text to format (must fit in subtitle limits)
            
        Returns:
            Formatted text with appropriate line breaks
        """
        # If text fits in one line, return as-is
        if len(text) <= self.max_chars_per_line:
            return text
        
        # Split into 2 lines - try to balance them
        words = text.split()
        
        # Find best split point for balanced lines
        best_split = len(words) // 2
        best_balance = float('inf')
        
        for split_point in range(1, len(words)):
            line1 = ' '.join(words[:split_point])
            line2 = ' '.join(words[split_point:])
            
            # Check if both lines fit
            if len(line1) <= self.max_chars_per_line and len(line2) <= self.max_chars_per_line:
                # Calculate balance (difference in line lengths)
                balance = abs(len(line1) - len(line2))
                
                # Prefer splits that create more balanced lines
                if balance < best_balance:
                    best_balance = balance
                    best_split = split_point
        
        # Create the two lines with the best split
        line1 = ' '.join(words[:best_split])
        line2 = ' '.join(words[best_split:])
        
        # Join with subtitle line break (\\N for ASS/SSA formats)
        return f"{line1}\\N{line2}" if line2 else line1
    
    def generate_multiple_formats(
        self,
        segments: List[Dict],
        output_base_path: Path,
        formats: List[str],
        **kwargs
    ) -> Dict[str, Path]:
        """Generate subtitles in multiple formats.
        
        Args:
            segments: List of segments with timestamps
            output_base_path: Base path for output files
            formats: List of format strings (e.g., ['srt', 'vtt'])
            **kwargs: Additional arguments for generate_subtitles
            
        Returns:
            Dictionary mapping format to generated file path
        """
        generated_files = {}
        
        for format in formats:
            try:
                file_path = self.generate_subtitles(
                    segments,
                    output_base_path,
                    format=format,
                    **kwargs
                )
                generated_files[format] = file_path
                logger.info(f"Generated {format} subtitle: {file_path}")
            except Exception as e:
                logger.error(f"Failed to generate {format} subtitle: {e}")
                generated_files[format] = None
        
        return generated_files
    
    @staticmethod
    def get_format_info(format: str) -> Dict[str, str]:
        """Get information about a subtitle format.
        
        Args:
            format: Format identifier
            
        Returns:
            Dictionary with format information
        """
        if format not in SubtitleGenerator.SUPPORTED_FORMATS:
            return {'error': f'Unknown format: {format}'}
        
        info = {
            'name': SubtitleGenerator.SUPPORTED_FORMATS[format],
            'extension': f'.{format}',
            'description': ''
        }
        
        # Add format-specific descriptions
        descriptions = {
            'srt': 'Most widely supported format, simple text-based',
            'vtt': 'Web standard, supports styling and positioning',
            'ass': 'Advanced format with rich styling and effects',
            'ssa': 'Predecessor to ASS, good compatibility'
        }
        
        info['description'] = descriptions.get(format, 'Subtitle format')
        
        return info
    
