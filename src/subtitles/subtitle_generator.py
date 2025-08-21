import pysubs2
from pathlib import Path
from typing import List, Dict, Optional, Tuple
import logging
import re

logger = logging.getLogger(__name__)

class SubtitleGenerator:
    """Generate subtitle files in various formats from transcription segments."""
    
    SUPPORTED_FORMATS = {
        'srt': 'SubRip',
        'vtt': 'WebVTT', 
        'ass': 'Advanced SubStation Alpha',
        'ssa': 'SubStation Alpha',
        'ttml': 'Timed Text Markup Language',
        'sami': 'Synchronized Accessible Media Interchange'
    }
    
    def __init__(self, max_chars_per_line: int = 42, max_lines_per_subtitle: int = 2):
        """Initialize subtitle generator with formatting preferences.
        
        Args:
            max_chars_per_line: Maximum characters per subtitle line
            max_lines_per_subtitle: Maximum lines per subtitle entry (standard is 2)
        """
        self.max_chars_per_line = max_chars_per_line
        self.max_lines_per_subtitle = 2  # Force 2 lines max as per subtitle standards
        logger.info(f"SubtitleGenerator initialized with {max_chars_per_line} chars/line, max 2 lines")
    
    def generate_subtitles(
        self, 
        segments: List[Dict],
        output_path: Path,
        format: str = 'srt',
        time_offset: float = 0.0,
        min_duration: float = 0.5,
        max_duration: float = 7.0
    ) -> Path:
        """Generate subtitle file from segments with timestamps.
        
        Args:
            segments: List of dictionaries with 'start', 'end', 'text' keys
            output_path: Base path for output file (without extension)
            format: Output format (srt, vtt, ass, etc.)
            time_offset: Global time offset in seconds (for synchronization)
            min_duration: Minimum subtitle duration in seconds
            max_duration: Maximum subtitle duration in seconds
            
        Returns:
            Path to generated subtitle file
        """
        if format not in self.SUPPORTED_FORMATS:
            raise ValueError(f"Unsupported format: {format}. Supported: {list(self.SUPPORTED_FORMATS.keys())}")
        
        logger.info(f"Generating {format} subtitles with {len(segments)} segments")
        
        # Create pysubs2 subtitle file
        subs = pysubs2.SSAFile()
        
        for i, segment in enumerate(segments):
            # Apply time offset if needed
            start_time = segment['start'] + time_offset
            end_time = segment['end'] + time_offset
            
            # Enforce duration constraints
            duration = end_time - start_time
            if duration < min_duration:
                end_time = start_time + min_duration
            elif duration > max_duration:
                end_time = start_time + max_duration
            
            # Format text for subtitles
            formatted_text = self._format_subtitle_text(segment['text'])
            
            # Create subtitle event
            event = pysubs2.SSAEvent(
                start=int(start_time * 1000),  # Convert to milliseconds
                end=int(end_time * 1000),
                text=formatted_text
            )
            subs.append(event)
            
            if (i + 1) % 100 == 0:
                logger.debug(f"Processed {i + 1}/{len(segments)} segments")
        
        # Generate output filename with extension
        output_file = output_path.with_suffix(f'.{format}')
        
        # Save in requested format
        subs.save(str(output_file))
        logger.info(f"Saved subtitle file: {output_file}")
        
        return output_file
    
    def _format_subtitle_text(self, text: str) -> str:
        """Format text for optimal subtitle display with line breaks.
        
        Args:
            text: Raw text to format
            
        Returns:
            Formatted text with appropriate line breaks
        """
        # Clean up text
        text = text.strip()
        if not text:
            return ""
        
        # Remove multiple spaces
        text = re.sub(r'\s+', ' ', text)
        
        # Split into optimal lines
        lines = self._split_into_lines(text)
        
        # Join with subtitle line break (\\N for ASS/SSA formats)
        return '\\N'.join(lines)
    
    def _split_into_lines(self, text: str) -> List[str]:
        """Split text into lines respecting max characters and subtitle standards.
        
        Enforces maximum 2 lines per subtitle as per industry standards.
        If text is too long, it will be properly fitted into 2 lines.
        
        Args:
            text: Text to split
            
        Returns:
            List of text lines (maximum 2 lines)
        """
        words = text.split()
        if not words:
            return []
        
        # Calculate total text length
        total_length = sum(len(word) for word in words) + len(words) - 1
        
        # If text fits in one line, return as is
        if total_length <= self.max_chars_per_line:
            return [' '.join(words)]
        
        # Try to split into 2 lines evenly
        # Find the best split point that balances both lines
        best_split = len(words) // 2
        best_balance = float('inf')
        
        for split_point in range(1, len(words)):
            line1 = ' '.join(words[:split_point])
            line2 = ' '.join(words[split_point:])
            
            # Skip if either line is too long
            if len(line1) > self.max_chars_per_line or len(line2) > self.max_chars_per_line:
                continue
            
            # Calculate balance (difference in line lengths)
            balance = abs(len(line1) - len(line2))
            
            # Prefer splits that create more balanced lines
            if balance < best_balance:
                best_balance = balance
                best_split = split_point
        
        # Create the two lines
        line1 = ' '.join(words[:best_split])
        line2 = ' '.join(words[best_split:])
        
        # If line2 is still too long, truncate it
        if len(line2) > self.max_chars_per_line:
            line2 = line2[:self.max_chars_per_line - 3] + '...'
        
        # If line1 is too long (rare case), adjust the split
        if len(line1) > self.max_chars_per_line:
            # Revert to simple split
            lines = []
            current_line = []
            current_length = 0
            
            for i, word in enumerate(words):
                word_length = len(word)
                
                if current_length > 0 and current_length + word_length + 1 > self.max_chars_per_line:
                    lines.append(' '.join(current_line))
                    if len(lines) >= 2:  # Stop at 2 lines
                        # Put remaining text in line 2 and truncate if needed
                        remaining = ' '.join(words[i:])  # Use index instead of words.index
                        if len(remaining) > self.max_chars_per_line:
                            remaining = remaining[:self.max_chars_per_line - 3] + '...'
                        lines[1] = remaining
                        return lines[:2]
                    current_line = [word]
                    current_length = word_length
                else:
                    current_line.append(word)
                    current_length += word_length + (1 if current_length > 0 else 0)
            
            if current_line and len(lines) < 2:
                lines.append(' '.join(current_line))
            
            return lines[:2]  # Ensure maximum 2 lines
        
        return [line1, line2] if line2 else [line1]
    
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
    
    def adjust_timing(
        self,
        segments: List[Dict],
        offset: float = 0.0,
        speed_factor: float = 1.0
    ) -> List[Dict]:
        """Adjust timing of all segments.
        
        Args:
            segments: Original segments
            offset: Time offset in seconds (positive = delay, negative = advance)
            speed_factor: Speed adjustment factor (>1 = faster, <1 = slower)
            
        Returns:
            New list of segments with adjusted timing
        """
        adjusted_segments = []
        
        for segment in segments:
            adjusted_segment = segment.copy()
            # Apply speed factor first, then offset
            adjusted_segment['start'] = (segment['start'] * speed_factor) + offset
            adjusted_segment['end'] = (segment['end'] * speed_factor) + offset
            
            # Ensure positive times
            adjusted_segment['start'] = max(0, adjusted_segment['start'])
            adjusted_segment['end'] = max(adjusted_segment['start'] + 0.1, adjusted_segment['end'])
            
            adjusted_segments.append(adjusted_segment)
        
        return adjusted_segments
    
    def merge_short_segments(
        self,
        segments: List[Dict],
        min_duration: float = 1.0
    ) -> List[Dict]:
        """Merge segments that are too short with adjacent segments.
        
        Args:
            segments: Original segments
            min_duration: Minimum duration in seconds
            
        Returns:
            List of segments with short ones merged
        """
        if not segments:
            return []
        
        merged = []
        current = segments[0].copy()
        
        for next_segment in segments[1:]:
            current_duration = current['end'] - current['start']
            
            # Check if current segment is too short and can be merged
            if current_duration < min_duration:
                # Merge with next segment
                current['end'] = next_segment['end']
                current['text'] = current['text'] + ' ' + next_segment['text']
            else:
                # Keep current segment and move to next
                merged.append(current)
                current = next_segment.copy()
        
        # Don't forget the last segment
        merged.append(current)
        
        return merged
    
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
            'ssa': 'Predecessor to ASS, good compatibility',
            'ttml': 'XML-based, used in broadcasting',
            'sami': 'Microsoft format, good for Windows Media'
        }
        
        info['description'] = descriptions.get(format, 'Subtitle format')
        
        return info