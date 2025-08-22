"""Advanced subtitle timing fixer that ensures subtitles stay visible until all words are spoken."""

from typing import List, Dict, Optional
import logging

logger = logging.getLogger(__name__)


class SubtitleTimingFixer:
    """Fixes subtitle timing to ensure they remain visible while being spoken."""
    
    def __init__(
        self,
        min_display_time: float = 1.5,
        reading_speed_wpm: int = 160,
        speech_overlap_buffer: float = 0.5
    ):
        """Initialize the subtitle timing fixer.
        
        Args:
            min_display_time: Minimum time a subtitle should be displayed
            reading_speed_wpm: Reading speed in words per minute
            speech_overlap_buffer: Extra time to keep subtitle visible after speech
        """
        self.min_display_time = min_display_time
        self.reading_speed_wpm = reading_speed_wpm
        self.speech_overlap_buffer = speech_overlap_buffer
        
        logger.info(f"SubtitleTimingFixer initialized with min_display={min_display_time}s, "
                   f"reading_speed={reading_speed_wpm}wpm")
    
    def fix_subtitle_timing(self, segments: List[Dict]) -> List[Dict]:
        """Fix subtitle timing to ensure proper display duration.
        
        The main issue: Subtitles disappear before all their words are spoken.
        Solution: Extend subtitle end time to cover all words being spoken.
        
        Args:
            segments: List of subtitle segments with text and timing
            
        Returns:
            Fixed segments with proper timing
        """
        if not segments:
            return segments
        
        fixed_segments = []
        
        for i, segment in enumerate(segments):
            fixed_segment = segment.copy()
            
            # Get the text and analyze it
            text = segment.get('text', '').strip()
            if not text:
                fixed_segments.append(fixed_segment)
                continue
            
            # Calculate how long this subtitle needs to be displayed
            start_time = segment['start']
            end_time = segment['end']
            original_end = end_time
            
            # CRITICAL FIX: If we have word-level timestamps, use them
            if 'words' in segment and segment['words']:
                words = segment['words']
                
                # Find the ACTUAL last word timestamp
                last_word_end = max(word.get('end', 0) for word in words)
                first_word_start = min(word.get('start', start_time) for word in words)
                
                # Log what we found
                logger.info(f"Segment text: '{text[:50]}...'")
                logger.info(f"  Original timing: {start_time:.2f}s - {end_time:.2f}s")
                logger.info(f"  Word timing: {first_word_start:.2f}s - {last_word_end:.2f}s")
                logger.info(f"  Last word: '{words[-1].get('word', 'unknown')}' ends at {last_word_end:.2f}s")
                
                # CRITICAL: The subtitle MUST stay visible until the last word is completely spoken
                # Add a generous buffer to ensure it doesn't cut off
                required_end_time = last_word_end + 0.5  # 500ms buffer after last word
                
                # Always extend to cover the last word, never shorten
                if required_end_time > end_time:
                    logger.warning(f"  ⚠️ FIXING: Subtitle would disappear {required_end_time - end_time:.2f}s before last word!")
                    fixed_segment['end'] = required_end_time
                    end_time = required_end_time
                    logger.info(f"  ✓ Extended subtitle to {required_end_time:.2f}s")
                
                # Also adjust start if needed
                if first_word_start < start_time - 0.1:
                    fixed_segment['start'] = first_word_start - 0.1
                    logger.info(f"  Adjusted start to {fixed_segment['start']:.2f}s")
            else:
                logger.warning(f"NO WORD TIMESTAMPS for segment: '{text[:50]}...'")
                # Fallback: estimate based on text length
                word_count = len(text.split())
                estimated_duration = word_count * 0.4  # Rough estimate
                if end_time - start_time < estimated_duration:
                    fixed_segment['end'] = start_time + estimated_duration
                    logger.info(f"  Extended based on word count to {fixed_segment['end']:.2f}s")
            
            # Calculate minimum display time based on text length
            word_count = len(text.split())
            char_count = len(text)
            
            # Reading time calculation (with more time for two-line subtitles)
            reading_time = (word_count / self.reading_speed_wpm) * 60
            
            # If text is long enough to be two lines (>42 chars), add extra time
            if char_count > 42:
                reading_time *= 1.3  # 30% more time for two-line subtitles
                logger.debug(f"Two-line subtitle detected ({char_count} chars), "
                           f"increased reading time to {reading_time:.2f}s")
            
            # Ensure minimum display time
            min_required_time = max(self.min_display_time, reading_time)
            current_duration = end_time - start_time
            
            if current_duration < min_required_time:
                # Extend the subtitle duration
                fixed_segment['end'] = start_time + min_required_time
                logger.debug(f"Extended subtitle duration from {current_duration:.2f}s "
                           f"to {min_required_time:.2f}s for readability")
            
            # Check for overlap with next segment and adjust if needed
            if i < len(segments) - 1:
                next_segment = segments[i + 1]
                next_start = next_segment['start']
                
                # If our extended subtitle would overlap with the next one
                if fixed_segment['end'] > next_start:
                    # Check if we can delay the next subtitle slightly
                    gap_available = next_start - segment['end']
                    
                    if gap_available > 0.2:  # If there's at least 200ms gap
                        # Use most of the gap but leave some space
                        fixed_segment['end'] = next_start - 0.1
                        logger.debug(f"Adjusted end time to {fixed_segment['end']:.2f}s "
                                   f"to avoid overlap with next subtitle at {next_start:.2f}s")
                    else:
                        # Can't extend without overlap, keep original with small buffer
                        fixed_segment['end'] = min(fixed_segment['end'], next_start - 0.05)
            
            fixed_segments.append(fixed_segment)
        
        return fixed_segments
    
    def calculate_optimal_split_point(self, text: str, max_chars_per_line: int = 42) -> Optional[int]:
        """Calculate the optimal point to split text into two lines.
        
        Args:
            text: Text to potentially split
            max_chars_per_line: Maximum characters per line
            
        Returns:
            Index to split at, or None if no split needed
        """
        if len(text) <= max_chars_per_line:
            return None
        
        words = text.split()
        
        # Find the split point that creates most balanced lines
        best_split = len(words) // 2
        best_balance = float('inf')
        
        for i in range(1, len(words)):
            line1 = ' '.join(words[:i])
            line2 = ' '.join(words[i:])
            
            # Both lines must fit
            if len(line1) <= max_chars_per_line and len(line2) <= max_chars_per_line:
                balance = abs(len(line1) - len(line2))
                if balance < best_balance:
                    best_balance = balance
                    best_split = i
        
        return best_split
    
    def ensure_speech_coverage(self, segment: Dict) -> Dict:
        """Ensure subtitle covers the entire duration of speech.
        
        Critical fix: The subtitle must remain visible while ALL its words
        are being spoken, not just until the "segment" ends.
        
        Args:
            segment: Segment to fix
            
        Returns:
            Fixed segment with proper speech coverage
        """
        fixed = segment.copy()
        
        # If we have word timestamps, ensure we cover all of them
        if 'words' in segment and segment['words']:
            words = segment['words']
            
            # Find the actual speech span
            first_word_start = min(word.get('start', segment['start']) for word in words)
            last_word_end = max(word.get('end', segment['end']) for word in words)
            
            # The subtitle should appear slightly before the first word
            # and disappear slightly after the last word
            fixed['start'] = first_word_start - 0.1  # 100ms before first word
            fixed['end'] = last_word_end + 0.3  # 300ms after last word
            
            logger.debug(f"Adjusted subtitle timing to cover speech from "
                       f"{first_word_start:.2f}s to {last_word_end:.2f}s")
        
        return fixed