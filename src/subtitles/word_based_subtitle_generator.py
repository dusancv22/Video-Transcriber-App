"""
Simple word-based subtitle generator that actually uses word timestamps.
This replaces the overcomplicated existing system with something that just works.
"""

from pathlib import Path
from typing import List, Dict, Tuple
import pysubs2
import logging

logger = logging.getLogger(__name__)


class WordBasedSubtitleGenerator:
    """Generate subtitles using actual word-level timestamps."""
    
    def __init__(
        self,
        max_chars_per_line: int = 42,
        max_words_per_subtitle: int = 10,
        min_subtitle_duration: float = 1.0,
        max_subtitle_duration: float = 7.0
    ):
        """Initialize the generator.
        
        Args:
            max_chars_per_line: Maximum characters per line
            max_words_per_subtitle: Maximum words in one subtitle
            min_subtitle_duration: Minimum duration for a subtitle
            max_subtitle_duration: Maximum duration for a subtitle
        """
        self.max_chars_per_line = max_chars_per_line
        self.max_words_per_subtitle = max_words_per_subtitle
        self.min_subtitle_duration = min_subtitle_duration
        self.max_subtitle_duration = max_subtitle_duration
    
    def generate_from_segments(
        self,
        segments: List[Dict],
        output_path: Path,
        format: str = 'srt'
    ) -> Path:
        """Generate subtitles from segments with word timestamps.
        
        Args:
            segments: List of segments with 'words' field containing word timestamps
            output_path: Output file path (without extension)
            format: Output format (srt, vtt, ass)
            
        Returns:
            Path to generated subtitle file
        """
        # First, extract ALL words with their timestamps
        all_words = []
        
        for segment in segments:
            if 'words' in segment and segment['words']:
                # We have word-level timestamps!
                for word_data in segment['words']:
                    all_words.append({
                        'word': word_data['word'].strip(),
                        'start': word_data['start'],
                        'end': word_data['end']
                    })
            else:
                # No word timestamps - fall back to splitting text evenly
                text = segment.get('text', '').strip()
                if not text:
                    continue
                    
                words = text.split()
                duration = segment['end'] - segment['start']
                time_per_word = duration / len(words) if words else 0
                
                for i, word in enumerate(words):
                    all_words.append({
                        'word': word,
                        'start': segment['start'] + i * time_per_word,
                        'end': segment['start'] + (i + 1) * time_per_word
                    })
        
        if not all_words:
            logger.warning("No words found in segments!")
            return None
        
        logger.info(f"Processing {len(all_words)} words with timestamps")
        
        # Now group words into subtitles based on natural boundaries
        subtitles = self._group_words_into_subtitles(all_words)
        
        # Create the subtitle file
        subs = pysubs2.SSAFile()
        
        for subtitle in subtitles:
            # Format text for display (2 lines max)
            display_text = self._format_subtitle_text(subtitle['text'])
            
            # Create subtitle event
            event = pysubs2.SSAEvent(
                start=int(subtitle['start'] * 1000),  # Convert to milliseconds
                end=int(subtitle['end'] * 1000),
                text=display_text
            )
            subs.events.append(event)
        
        # Save in requested format
        output_file = output_path.with_suffix(f'.{format}')
        
        if format == 'srt':
            subs.save(str(output_file), format_='srt')
        elif format == 'vtt':
            subs.save(str(output_file), format_='vtt')
        elif format == 'ass':
            subs.save(str(output_file), format_='ass')
        else:
            subs.save(str(output_file))
        
        logger.info(f"Generated {len(subtitles)} subtitles to {output_file}")
        return output_file
    
    def _group_words_into_subtitles(self, words: List[Dict]) -> List[Dict]:
        """Group words into subtitle segments based on timing and length.
        
        Args:
            words: List of words with start/end timestamps
            
        Returns:
            List of subtitle dictionaries with text, start, and end times
        """
        subtitles = []
        current_subtitle = []
        current_start = None
        
        for i, word_data in enumerate(words):
            word = word_data['word']
            
            # Start a new subtitle if needed
            if not current_subtitle:
                current_subtitle = [word]
                current_start = word_data['start']
            else:
                # Check if we should start a new subtitle
                current_text = ' '.join(current_subtitle + [word])
                current_duration = word_data['end'] - current_start
                
                # Reasons to start a new subtitle:
                # 1. Too many words
                # 2. Too long duration
                # 3. Too many characters
                # 4. Natural pause (gap between words)
                
                should_break = False
                
                # Check word count
                if len(current_subtitle) >= self.max_words_per_subtitle:
                    should_break = True
                
                # Check duration
                elif current_duration > self.max_subtitle_duration:
                    should_break = True
                
                # Check character count (for 2 lines)
                elif len(current_text) > self.max_chars_per_line * 2:
                    should_break = True
                
                # Check for natural pause (gap > 0.3 seconds)
                elif i > 0:
                    gap = word_data['start'] - words[i-1]['end']
                    if gap > 0.3:
                        should_break = True
                
                if should_break:
                    # Save current subtitle
                    if current_subtitle:
                        subtitle_text = ' '.join(current_subtitle)
                        subtitles.append({
                            'text': subtitle_text,
                            'start': current_start,
                            'end': words[i-1]['end']  # Use actual end time of last word
                        })
                    
                    # Start new subtitle
                    current_subtitle = [word]
                    current_start = word_data['start']
                else:
                    # Add word to current subtitle
                    current_subtitle.append(word)
        
        # Add final subtitle
        if current_subtitle:
            subtitle_text = ' '.join(current_subtitle)
            subtitles.append({
                'text': subtitle_text,
                'start': current_start,
                'end': words[-1]['end']
            })
        
        # Ensure minimum duration
        for subtitle in subtitles:
            duration = subtitle['end'] - subtitle['start']
            if duration < self.min_subtitle_duration:
                # Extend the end time slightly
                subtitle['end'] = subtitle['start'] + self.min_subtitle_duration
        
        return subtitles
    
    def _format_subtitle_text(self, text: str) -> str:
        """Format text for 2-line display.
        
        Args:
            text: Text to format
            
        Returns:
            Text formatted with line break if needed
        """
        if len(text) <= self.max_chars_per_line:
            return text
        
        # Find best split point
        words = text.split()
        
        if len(words) == 1:
            return text  # Can't split a single word
        
        # Try to split roughly in the middle
        mid_point = len(text) // 2
        best_split = -1
        best_diff = len(text)
        
        current_pos = 0
        for i, word in enumerate(words[:-1]):
            current_pos += len(word) + 1  # +1 for space
            diff = abs(current_pos - mid_point)
            
            if diff < best_diff:
                best_diff = diff
                best_split = i
        
        if best_split >= 0:
            line1 = ' '.join(words[:best_split + 1])
            line2 = ' '.join(words[best_split + 1:])
            
            # Make sure neither line is too long
            if len(line1) <= self.max_chars_per_line and len(line2) <= self.max_chars_per_line:
                return f"{line1}\n{line2}"
        
        # If we can't split nicely, just return the text
        # The subtitle display will handle wrapping
        return text