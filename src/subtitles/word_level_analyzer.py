"""Word-level timestamp analyzer for natural subtitle segment boundaries."""

from typing import List, Dict, Tuple, Optional
import logging
import math

logger = logging.getLogger(__name__)


class WordLevelAnalyzer:
    """Analyzes word-level timestamps to create natural subtitle boundaries."""
    
    def __init__(
        self,
        pause_threshold: float = 0.3,
        min_pause_for_boundary: float = 0.2,
        transition_delay: float = 0.15,
        max_segment_duration: float = 7.0,
        min_segment_duration: float = 1.0,
        aggressive_merge: bool = True,
        merge_orphan_words: bool = True
    ):
        """Initialize the word-level analyzer.
        
        Args:
            pause_threshold: Minimum pause duration to consider as potential boundary
            min_pause_for_boundary: Minimum pause to create a segment boundary
            transition_delay: Delay to add to segment transitions for better sync
            max_segment_duration: Maximum duration for a single subtitle segment
            min_segment_duration: Minimum duration for a single subtitle segment
            aggressive_merge: Aggressively merge segments that are unnaturally split
            merge_orphan_words: Merge single-word segments with previous segment
        """
        self.pause_threshold = pause_threshold
        self.min_pause_for_boundary = min_pause_for_boundary
        self.transition_delay = transition_delay
        self.max_segment_duration = max_segment_duration
        self.min_segment_duration = min_segment_duration
        self.aggressive_merge = aggressive_merge
        self.merge_orphan_words = merge_orphan_words
        
        logger.info(f"WordLevelAnalyzer initialized with pause threshold: {pause_threshold}s, transition delay: {transition_delay}s")
    
    def optimize_segment_boundaries(self, segments: List[Dict]) -> List[Dict]:
        """Optimize segment boundaries using word-level timestamps.
        
        This method analyzes word-level timestamps within segments to find
        natural pause points and adjusts segment boundaries accordingly.
        
        Args:
            segments: List of segments with potential word-level timestamps
            
        Returns:
            List of segments with optimized boundaries
        """
        if not segments:
            return segments
        
        # First pass: merge orphan words and short segments
        if self.aggressive_merge:
            segments = self._merge_orphan_segments(segments)
        
        optimized_segments = []
        
        for i, segment in enumerate(segments):
            # Check if segment has word-level timestamps
            if 'words' in segment and segment['words']:
                # Analyze this segment for better boundaries
                if i < len(segments) - 1:
                    next_segment = segments[i + 1]
                    optimized = self._optimize_segment_pair(segment, next_segment)
                    
                    # Store the optimized current segment
                    optimized_segments.append(optimized['current'])
                    
                    # Update the next segment in the list for processing
                    if i + 1 < len(segments):
                        segments[i + 1] = optimized['next']
                else:
                    # Last segment - just apply transition delay
                    optimized_segments.append(self._apply_transition_delay(segment))
            else:
                # No word-level data - apply simple transition delay
                optimized_segments.append(self._apply_transition_delay(segment))
        
        # Post-process to ensure no overlaps and proper durations
        return self._ensure_proper_timing(optimized_segments)
    
    def _optimize_segment_pair(self, current: Dict, next_segment: Dict) -> Dict:
        """Optimize the boundary between two segments.
        
        Args:
            current: Current segment with word-level timestamps
            next_segment: Next segment
            
        Returns:
            Dictionary with optimized 'current' and 'next' segments
        """
        words = current.get('words', [])
        if not words:
            return {
                'current': self._apply_transition_delay(current),
                'next': next_segment
            }
        
        # Find natural pause points in the current segment
        pause_points = self._find_pause_points(words)
        
        # If we found good pause points, check if we should adjust the boundary
        if pause_points:
            # Get the current boundary
            current_boundary = current['end']
            
            # Find the best pause point near the current boundary
            best_pause = self._find_best_pause_near_boundary(
                pause_points, 
                current_boundary,
                current['start']
            )
            
            if best_pause:
                # Calculate the adjustment
                adjustment = best_pause['time'] - current_boundary
                
                # Only adjust if the change is significant but not too large
                if abs(adjustment) < 0.5 and abs(adjustment) > 0.05:
                    logger.debug(f"Adjusting boundary by {adjustment:.3f}s at {best_pause['time']:.2f}s")
                    
                    # Find which words belong to each segment after adjustment
                    words_before, words_after = self._split_words_at_time(words, best_pause['time'])
                    
                    # Update current segment
                    new_current = current.copy()
                    new_current['end'] = best_pause['time'] + self.transition_delay
                    if words_before:
                        new_current['text'] = ' '.join([w.get('word', w.get('text', '')) for w in words_before])
                        new_current['words'] = words_before
                    
                    # Update next segment
                    new_next = next_segment.copy()
                    new_next['start'] = best_pause['time'] + self.transition_delay
                    
                    # Add any words that were moved to the next segment
                    if words_after:
                        moved_text = ' '.join([w.get('word', w.get('text', '')) for w in words_after])
                        new_next['text'] = moved_text + ' ' + new_next.get('text', '')
                        
                        # Update word timestamps if next segment has them
                        if 'words' in new_next and new_next['words']:
                            new_next['words'] = words_after + new_next['words']
                    
                    return {'current': new_current, 'next': new_next}
        
        # No good adjustment found - just apply transition delay
        return {
            'current': self._apply_transition_delay(current),
            'next': next_segment
        }
    
    def _find_pause_points(self, words: List[Dict]) -> List[Dict]:
        """Find natural pause points between words.
        
        Args:
            words: List of word dictionaries with timestamps
            
        Returns:
            List of pause points with timing and confidence
        """
        pause_points = []
        
        for i in range(len(words) - 1):
            current_word = words[i]
            next_word = words[i + 1]
            
            # Get word end and next word start
            word_end = current_word.get('end', 0)
            next_start = next_word.get('start', 0)
            
            # Calculate gap between words
            gap = next_start - word_end
            
            # Check if this is a significant pause
            if gap >= self.min_pause_for_boundary:
                # Calculate pause confidence based on gap duration
                confidence = min(1.0, gap / self.pause_threshold)
                
                # The boundary should be in the middle of the pause
                boundary_time = word_end + (gap / 2)
                
                pause_points.append({
                    'time': boundary_time,
                    'gap': gap,
                    'confidence': confidence,
                    'after_word': current_word.get('word', current_word.get('text', '')),
                    'before_word': next_word.get('word', next_word.get('text', ''))
                })
                
                logger.debug(f"Found pause: {gap:.3f}s gap after '{current_word.get('word', '')}' at {boundary_time:.2f}s")
        
        return pause_points
    
    def _find_best_pause_near_boundary(
        self, 
        pause_points: List[Dict], 
        current_boundary: float,
        segment_start: float
    ) -> Optional[Dict]:
        """Find the best pause point near the current segment boundary.
        
        Args:
            pause_points: List of detected pause points
            current_boundary: Current segment end time
            segment_start: Current segment start time
            
        Returns:
            Best pause point or None
        """
        if not pause_points:
            return None
        
        # Filter pauses that are reasonably close to the boundary
        max_distance = 0.8  # Don't look for pauses more than 800ms away
        nearby_pauses = [
            p for p in pause_points
            if abs(p['time'] - current_boundary) <= max_distance
        ]
        
        if not nearby_pauses:
            return None
        
        # Score each pause based on:
        # 1. Distance from current boundary (closer is better)
        # 2. Pause duration (longer is better)
        # 3. Position in segment (avoid very early or very late)
        
        best_pause = None
        best_score = -1
        
        for pause in nearby_pauses:
            # Distance score (0-1, closer is better)
            distance = abs(pause['time'] - current_boundary)
            distance_score = 1.0 - (distance / max_distance)
            
            # Pause duration score (0-1, longer is better)
            pause_score = pause['confidence']
            
            # Position score (0-1, middle of segment is better)
            segment_duration = current_boundary - segment_start
            if segment_duration > 0:
                position_ratio = (pause['time'] - segment_start) / segment_duration
                # Prefer pauses in the latter half of the segment
                if 0.4 <= position_ratio <= 0.9:
                    position_score = 1.0
                elif position_ratio < 0.4:
                    position_score = position_ratio / 0.4
                else:
                    position_score = (1.0 - position_ratio) / 0.1
            else:
                position_score = 0.5
            
            # Combined score with weights
            total_score = (
                distance_score * 0.3 +
                pause_score * 0.5 +
                position_score * 0.2
            )
            
            if total_score > best_score:
                best_score = total_score
                best_pause = pause
        
        if best_pause:
            logger.debug(f"Best pause selected at {best_pause['time']:.2f}s with score {best_score:.3f}")
        
        return best_pause
    
    def _split_words_at_time(self, words: List[Dict], split_time: float) -> Tuple[List[Dict], List[Dict]]:
        """Split words list at a specific time point.
        
        Args:
            words: List of words with timestamps
            split_time: Time to split at
            
        Returns:
            Tuple of (words_before, words_after)
        """
        words_before = []
        words_after = []
        
        for word in words:
            word_end = word.get('end', 0)
            if word_end <= split_time:
                words_before.append(word)
            else:
                words_after.append(word)
        
        return words_before, words_after
    
    def _apply_transition_delay(self, segment: Dict) -> Dict:
        """Apply transition delay to a segment.
        
        This delays when the subtitle disappears, giving viewers more time
        to read while the speaker transitions to the next phrase.
        
        Args:
            segment: Segment to modify
            
        Returns:
            Modified segment with transition delay
        """
        modified = segment.copy()
        
        # Calculate delay based on content complexity
        text = segment.get('text', '')
        word_count = len(text.split())
        
        # Base delay
        delay = self.transition_delay
        
        # Additional delay for multi-line subtitles
        # Assume ~42 chars per line, if text is longer it's likely 2 lines
        if len(text) > 42:
            # Add extra time for second line (viewers need time to read both lines)
            delay += 0.3  # Extra 300ms for two-line subtitles
            logger.debug(f"Two-line subtitle detected, extending delay to {delay}s")
        
        # For very short segments (1-2 words), use minimal delay
        if word_count <= 2:
            delay = min(delay, 0.1)
        
        # Extend the end time so subtitle stays visible longer
        modified['end'] = segment['end'] + delay
        return modified
    
    def _ensure_proper_timing(self, segments: List[Dict]) -> List[Dict]:
        """Ensure segments have proper timing without overlaps.
        
        Args:
            segments: List of segments to validate
            
        Returns:
            List of segments with corrected timing
        """
        if not segments:
            return segments
        
        corrected = []
        
        for i, segment in enumerate(segments):
            current = segment.copy()
            
            # Ensure minimum duration
            duration = current['end'] - current['start']
            if duration < self.min_segment_duration:
                current['end'] = current['start'] + self.min_segment_duration
            
            # Ensure maximum duration
            if duration > self.max_segment_duration:
                current['end'] = current['start'] + self.max_segment_duration
            
            # Check for overlap with next segment
            if i < len(segments) - 1:
                next_segment = segments[i + 1]
                if current['end'] > next_segment['start']:
                    # Adjust to prevent overlap
                    gap = 0.05  # 50ms gap
                    current['end'] = next_segment['start'] - gap
            
            corrected.append(current)
        
        return corrected
    
    def analyze_speech_rhythm(self, segments: List[Dict]) -> Dict:
        """Analyze speech rhythm patterns in the segments.
        
        Args:
            segments: List of segments with word-level timestamps
            
        Returns:
            Dictionary with rhythm analysis metrics
        """
        total_pauses = 0
        total_pause_duration = 0
        word_count = 0
        speech_duration = 0
        
        for segment in segments:
            if 'words' in segment and segment['words']:
                words = segment['words']
                word_count += len(words)
                
                # Analyze pauses within this segment
                for i in range(len(words) - 1):
                    gap = words[i + 1].get('start', 0) - words[i].get('end', 0)
                    if gap > 0.1:  # Count pauses > 100ms
                        total_pauses += 1
                        total_pause_duration += gap
                
                # Calculate speech duration (excluding pauses)
                for word in words:
                    word_duration = word.get('end', 0) - word.get('start', 0)
                    speech_duration += word_duration
        
        # Calculate metrics
        avg_pause_duration = total_pause_duration / total_pauses if total_pauses > 0 else 0
        pause_ratio = total_pause_duration / (speech_duration + total_pause_duration) if speech_duration > 0 else 0
        words_per_minute = (word_count / speech_duration * 60) if speech_duration > 0 else 0
        
        return {
            'total_pauses': total_pauses,
            'avg_pause_duration': avg_pause_duration,
            'pause_ratio': pause_ratio,
            'words_per_minute': words_per_minute,
            'total_words': word_count,
            'speech_duration': speech_duration,
            'total_pause_duration': total_pause_duration
        }
    
    def _merge_orphan_segments(self, segments: List[Dict]) -> List[Dict]:
        """Merge orphan words and unnaturally split segments.
        
        This handles cases like 'pueblo.' being its own segment when it should
        be part of the previous phrase.
        
        Args:
            segments: Original segments
            
        Returns:
            Segments with orphans merged
        """
        if not segments:
            return segments
        
        merged = []
        i = 0
        
        while i < len(segments):
            current = segments[i].copy()
            
            # Check if this is an orphan segment (very short or single word)
            word_count = len(current.get('text', '').split())
            duration = current['end'] - current['start']
            
            # Conditions for orphan segment:
            # 1. Single word or very few words (≤2)
            # 2. Very short duration relative to content
            # 3. Previous segment exists
            is_orphan = (
                word_count <= 2 and 
                i > 0 and 
                len(merged) > 0
            )
            
            if is_orphan:
                # Check the gap to previous segment
                prev_segment = merged[-1]
                gap = current['start'] - prev_segment['end']
                
                # If gap is reasonable (< 1 second), merge with previous
                if gap < 1.0:
                    logger.info(f"Merging orphan segment '{current['text']}' with previous")
                    
                    # Merge with previous segment
                    prev_segment['end'] = current['end']
                    prev_segment['text'] = prev_segment['text'].rstrip() + ' ' + current['text']
                    
                    # Merge word timestamps if available
                    if 'words' in prev_segment and 'words' in current:
                        prev_segment['words'] = prev_segment.get('words', []) + current.get('words', [])
                    elif 'words' in current:
                        prev_segment['words'] = current['words']
                    
                    # Update the last segment in merged list
                    merged[-1] = prev_segment
                    i += 1
                    continue
            
            # Also check if next segment is an orphan that should be merged with current
            if i + 1 < len(segments):
                next_segment = segments[i + 1]
                next_word_count = len(next_segment.get('text', '').split())
                next_gap = next_segment['start'] - current['end']
                
                # If next is orphan and gap is small, merge it with current
                if next_word_count <= 2 and next_gap < 1.0:
                    logger.info(f"Merging next orphan segment '{next_segment['text']}' with current")
                    
                    current['end'] = next_segment['end']
                    current['text'] = current['text'].rstrip() + ' ' + next_segment['text']
                    
                    # Merge word timestamps
                    if 'words' in current and 'words' in next_segment:
                        current['words'] = current.get('words', []) + next_segment.get('words', [])
                    elif 'words' in next_segment:
                        current['words'] = next_segment['words']
                    
                    merged.append(current)
                    i += 2  # Skip next segment
                    continue
            
            # Normal segment, add as-is
            merged.append(current)
            i += 1
        
        return merged