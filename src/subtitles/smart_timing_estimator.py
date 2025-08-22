"""Smart subtitle timing estimator for when word-level timestamps are unavailable."""

from typing import List, Dict, Tuple
import logging
import re

logger = logging.getLogger(__name__)


class SmartTimingEstimator:
    """Estimates subtitle timing based on text analysis and speech patterns."""
    
    def __init__(
        self,
        avg_speech_rate_wpm: int = 140,  # Average Spanish speech rate
        reading_rate_wpm: int = 160,      # Subtitle reading rate
        two_line_extension: float = 0.6,   # Extra time for two-line subtitles
        min_subtitle_duration: float = 1.5,
        max_subtitle_duration: float = 7.0
    ):
        """Initialize the timing estimator.
        
        Args:
            avg_speech_rate_wpm: Average words per minute for speech
            reading_rate_wpm: Average reading speed for subtitles
            two_line_extension: Extra seconds for two-line subtitles
            min_subtitle_duration: Minimum subtitle display time
            max_subtitle_duration: Maximum subtitle display time
        """
        self.avg_speech_rate_wpm = avg_speech_rate_wpm
        self.reading_rate_wpm = reading_rate_wpm
        self.two_line_extension = two_line_extension
        self.min_subtitle_duration = min_subtitle_duration
        self.max_subtitle_duration = max_subtitle_duration
        
        logger.info(f"SmartTimingEstimator initialized with speech_rate={avg_speech_rate_wpm}wpm")
    
    def fix_subtitle_timing_without_words(self, segments: List[Dict]) -> List[Dict]:
        """Fix subtitle timing when word-level timestamps are not available.
        
        This is a fallback method that uses heuristics to ensure subtitles
        stay visible for appropriate durations.
        
        Args:
            segments: List of subtitle segments without word timestamps
            
        Returns:
            Fixed segments with improved timing
        """
        if not segments:
            return segments
        
        fixed_segments = []
        
        for i, segment in enumerate(segments):
            fixed_segment = segment.copy()
            
            text = segment.get('text', '').strip()
            if not text:
                fixed_segments.append(fixed_segment)
                continue
            
            # Calculate text metrics
            word_count = len(text.split())
            char_count = len(text)
            is_two_line = char_count > 42
            
            # Get current timing
            start_time = segment['start']
            end_time = segment['end']
            current_duration = end_time - start_time
            
            # Calculate required speaking time (how long it takes to SAY the text)
            speaking_time = (word_count / self.avg_speech_rate_wpm) * 60
            
            # Calculate required reading time (how long viewers need to READ)
            reading_time = (word_count / self.reading_rate_wpm) * 60
            
            # For two-line subtitles, add extra time
            if is_two_line:
                # Two-line subtitles need more time because:
                # 1. Viewers need to read both lines
                # 2. The speaker is still saying the second line content
                speaking_time += self.two_line_extension
                reading_time *= 1.4  # 40% more time for two lines
                
                logger.debug(f"Two-line subtitle detected: '{text[:30]}...' ({char_count} chars)")
                logger.debug(f"  Extended timing: speaking={speaking_time:.2f}s, reading={reading_time:.2f}s")
            
            # The subtitle must be visible for the longer of:
            # 1. Time to speak all the words
            # 2. Time to read the subtitle
            # 3. Minimum duration
            required_duration = max(speaking_time, reading_time, self.min_subtitle_duration)
            
            # But not longer than maximum
            required_duration = min(required_duration, self.max_subtitle_duration)
            
            # If current duration is too short, extend it
            if current_duration < required_duration:
                extension = required_duration - current_duration
                fixed_segment['end'] = start_time + required_duration
                
                logger.info(f"Extended subtitle from {current_duration:.2f}s to {required_duration:.2f}s")
                logger.info(f"  Text: '{text[:50]}...' ({word_count} words, {char_count} chars)")
                
                # Check for overlap with next segment
                if i < len(segments) - 1:
                    next_segment = segments[i + 1]
                    next_start = next_segment['start']
                    
                    if fixed_segment['end'] > next_start - 0.1:
                        # Would overlap - adjust to leave small gap
                        fixed_segment['end'] = next_start - 0.1
                        logger.debug(f"  Adjusted to avoid overlap: {fixed_segment['end']:.2f}s")
            
            fixed_segments.append(fixed_segment)
        
        return fixed_segments
    
    def estimate_phrase_boundaries(self, text: str) -> List[int]:
        """Estimate natural phrase boundaries in text.
        
        Args:
            text: Text to analyze
            
        Returns:
            List of word indices where natural breaks might occur
        """
        words = text.split()
        boundaries = []
        
        # Look for punctuation and conjunctions that indicate phrase boundaries
        for i, word in enumerate(words):
            # Check for punctuation
            if any(punct in word for punct in [',', ';', ':', '.']):
                boundaries.append(i)
            # Check for conjunctions that often start new phrases
            elif word.lower() in ['y', 'o', 'pero', 'porque', 'cuando', 'donde', 'and', 'or', 'but']:
                if i > 0:  # Don't split at the very beginning
                    boundaries.append(i - 1)
        
        return boundaries
    
    def smart_segment_merge(self, segments: List[Dict]) -> List[Dict]:
        """Intelligently merge segments that are unnaturally split.
        
        Args:
            segments: Original segments
            
        Returns:
            Merged segments with better boundaries
        """
        if not segments:
            return segments
        
        merged = []
        i = 0
        
        while i < len(segments):
            current = segments[i].copy()
            text = current.get('text', '').strip()
            word_count = len(text.split())
            
            # Check if this segment is suspiciously short
            if word_count <= 3 and i < len(segments) - 1:
                next_segment = segments[i + 1]
                next_text = next_segment.get('text', '').strip()
                gap = next_segment['start'] - current['end']
                
                # Merge if:
                # 1. Gap is small (< 1 second)
                # 2. Combined text would be reasonable length
                combined_text = text + ' ' + next_text
                combined_words = len(combined_text.split())
                
                if gap < 1.0 and combined_words <= 20:  # Reasonable subtitle length
                    logger.info(f"Merging short segment '{text}' with next segment")
                    
                    current['end'] = next_segment['end']
                    current['text'] = combined_text
                    merged.append(current)
                    i += 2
                    continue
            
            # Check for orphan single words (like "pueblo.")
            if word_count == 1 and i > 0 and len(merged) > 0:
                # This is likely an orphan word that should be with previous
                prev_segment = merged[-1]
                gap = current['start'] - prev_segment['end']
                
                if gap < 1.5:  # Close enough to merge
                    logger.info(f"Merging orphan word '{text}' with previous segment")
                    prev_segment['end'] = current['end']
                    prev_segment['text'] = prev_segment['text'].rstrip() + ' ' + text
                    i += 1
                    continue
            
            merged.append(current)
            i += 1
        
        return merged